from sqlalchemy import create_engine, text, select, update as sa_update, delete as sa_delete
from sqlalchemy.orm import sessionmaker

# Gestiona el Engine y las sesiones de SQLAlchemy
class DbHandle:
    def __init__(self, url: str, **engine_kwargs):
        # # Crea engine y sessionmaker
        self.url = url
        self.engine = create_engine(url, **engine_kwargs)
        self.Session = sessionmaker(bind=self.engine)

    def new_session(self):
        # # Retorna una sesión nueva
        return self.Session()

    def session_scope(self):
        # # Context manager simple para manejar commit/rollback
        class _Scope:
            def __init__(self, Session):
                self.Session = Session
                self.session = None
            def __enter__(self):
                self.session = self.Session()
                return self.session
            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    self.session.commit()
                else:
                    self.session.rollback()
                self.session.close()
        return _Scope(self.Session)

    def ping(self) -> bool:
        # # SELECT 1; True si responde
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def dispose(self):
        # # Cierra el pool de conexiones
        self.engine.dispose()

    # -------------------------------
    # Métodos CRUD genéricos (ORM)
    # -------------------------------

    def create(self, obj):
        # # Inserta un objeto ORM
        with self.session_scope() as s:
            s.add(obj)

    def read_all(self, model):
        # # Devuelve todos los registros de un modelo
        with self.session_scope() as s:
            return s.scalars(select(model)).all()

    def read_one(self, model, **filters):
        # # Devuelve un solo registro con filtros
        with self.session_scope() as s:
            stmt = select(model).filter_by(**filters)
            return s.scalars(stmt).first()

    def update(self, model, filters: dict, values: dict):
        # # Actualiza registros de un modelo según filtros
        with self.session_scope() as s:
            stmt = sa_update(model).where(
                *[getattr(model, k) == v for k, v in filters.items()]
            ).values(**values)
            s.execute(stmt)

    def delete(self, model, **filters):
        # # Borra registros de un modelo según filtros
        with self.session_scope() as s:
            stmt = sa_delete(model).where(
                *[getattr(model, k) == v for k, v in filters.items()]
            )
            s.execute(stmt)