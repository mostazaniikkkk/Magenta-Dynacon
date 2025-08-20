import os
import tempfile
from configparser import ConfigParser
from urllib.parse import quote
from .conn.db_handler import DbHandle
from .class_manager.class_generator import Base, generate_classes
from sqlalchemy import Table, text, inspect

class DatabaseRegistry:
    # # Claves esperadas por sección
    REQUIRED_KEYS = ["source", "username", "password", "host", "port", "base"]

    def __init__(self, ini_path: str = "source.ini"):
        # # Path del archivo .ini (puede inyectarse)
        self.INI_PATH = ini_path
        # # Config en memoria + mapas
        self._cfg = ConfigParser(interpolation=None)
        self.handles = {}  # name -> DbHandle
        self.models = {}   # name -> {table_name: Class}
        self._load()
        self._build_connections()
        self._build_models_for_all()

    def _load(self):
        # # Carga el .ini
        self._cfg.read(self.INI_PATH, encoding="utf-8")

    def _atomic_save(self):
        # # Guardado atómico del .ini
        directory = os.path.dirname(os.path.abspath(self.INI_PATH)) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_db_", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                self._cfg.write(tmp)
            os.replace(tmp_path, self.INI_PATH)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _build_connections(self):
        # # Reconstruye todos los DbHandle desde el .ini
        self.handles.clear()
        for name in self._cfg.sections():
            url = self._build_url_from_section(name)
            self.handles[name] = DbHandle(url)

    def _build_or_refresh_one(self, name: str):
        # # Reconstruye solo un DbHandle y sus modelos
        if not self._cfg.has_section(name):
            handle = self.handles.pop(name, None)
            if handle:
                handle.dispose()
            self.models.pop(name, None)
            return
        url = self._build_url_from_section(name)
        old = self.handles.get(name)
        self.handles[name] = DbHandle(url)
        if old:
            old.dispose()
        # # Regenerar modelos para esa instancia
        self.models[name] = generate_classes(self.handles[name].engine)

    def _build_models_for_all(self):
        # # Genera clases dinámicas por cada engine existente
        self.models.clear()
        for name, handle in self.handles.items():
            self.models[name] = generate_classes(handle.engine)

    def _build_url_from_section(self, name: str) -> str:
        data = {k: v for k, v in self._cfg.items(name)}
        source = data.get("source", "").strip()

        if source == "sqlite":
            base = data.get("base", "").strip()
            if not base:
                return "sqlite:///:memory:"
            return f"sqlite:///{base}"

        user = data.get("username", "").strip()
        pwd = quote(data.get("password", ""), safe="")
        host = data.get("host", "").strip()
        port = data.get("port", "").strip()
        base = data.get("base", "").strip()
        return f"{source}://{user}:{pwd}@{host}:{port}/{base}" if base else f"{source}://{user}:{pwd}@{host}:{port}"

    def list_names(self) -> list[str]:
        # # Lista nombres de instancias
        return self._cfg.sections()

    def get_handle(self, name: str) -> DbHandle:
        # # Retorna el DbHandle (engine+sessionmaker)
        if name not in self.handles:
            raise KeyError(f"Instance '{name}' not found.")
        return self.handles[name]

    def new_session(self, name: str):
        # # Sesión nueva para instancia
        return self.get_handle(name).new_session()

    def ping(self, name: str) -> bool:
        # # Ping a la instancia
        return self.get_handle(name).ping()

    def add_instance(self, name: str, data: dict, overwrite: bool = False):
        # # Agrega sección al .ini y refresca el handle + modelos
        self._validate_payload(data)
        if self._cfg.has_section(name) and not overwrite:
            raise ValueError(f"Instance '{name}' already exists. Use overwrite=True to replace.")
        if not self._cfg.has_section(name):
            self._cfg.add_section(name)
        for k in self.REQUIRED_KEYS:
            self._cfg.set(name, k, str(data.get(k, "")))
        self._atomic_save()
        self._build_or_refresh_one(name)

    def update_instance(self, name: str, data: dict):
        # # Actualiza sección y refresca el handle + modelos
        if not self._cfg.has_section(name):
            raise KeyError(f"Instance '{name}' not found.")
        for k, v in data.items():
            self._cfg.set(name, k, str(v))
        self._atomic_save()
        self._build_or_refresh_one(name)

    def remove_instance(self, name: str):
        # # Quita sección y cierra conexiones + borra modelos
        if not self._cfg.has_section(name):
            raise KeyError(f"Instance '{name}' not found.")
        self._cfg.remove_section(name)
        self._atomic_save()
        self._build_or_refresh_one(name)

    def _validate_payload(self, data: dict):
        # # Chequea claves obligatorias
        missing = [k for k in self.REQUIRED_KEYS if k not in data]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

    # --------------------------
    # Nuevo: get_db_instance
    # --------------------------
    def get_db_instance(self, name: str, table_name: str):
        # # Hace un SELECT a la DB y genera la clase si no existe
        if name not in self.handles:
            raise KeyError(f"Instance '{name}' not found.")

        # # Asegurar mapa de modelos para la instancia
        if name not in self.models:
            self.models[name] = {}

        handle = self.handles[name]
        models_map = self.models[name]

        # # Si ya existe la clase, validamos con un SELECT trivial y devolvemos
        if table_name in models_map:
            with handle.engine.connect() as conn:
                conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            return models_map[table_name]

        # # Si no existe, reflejar tabla y generar solo esa clase con el template fijo
        # # 1) Verificar que la tabla exista en la DB
        insp = inspect(handle.engine)
        if table_name not in insp.get_table_names():
            raise KeyError(f"Table '{table_name}' not found in database '{name}'.")

        # # 2) Reflejar tabla
        table = Table(table_name, Base.metadata, autoload_with=handle.engine)

        # # 3) Cargar template fijo y hacer replace
        with open("management/class_manager/class_base.txt", "r", encoding="utf-8") as f:
            code = f.read()
        class_name = table_name.capitalize()
        code = code.replace("{ClassName}", class_name).replace("{table_name}", table_name)

        # # 4) Exec en namespace con Base/CRUD/tabla inyectada
        namespace = {"Base": Base, "Table": Table, "CRUDMixin": __import__("management.class_manager.crud_mixing", fromlist=["CRUDMixin"]).CRUDMixin}
        namespace["table"] = table
        exec(code, namespace, namespace)

        # # 5) Guardar clase y validar con SELECT trivial
        Model = namespace[class_name]
        models_map[table_name] = Model
        with handle.engine.connect() as conn:
            conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
        return Model
