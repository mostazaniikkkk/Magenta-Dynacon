# class_generator.py
from sqlalchemy import Table, inspect
from sqlalchemy.orm import declarative_base
from .crud_mixing import CRUDMixin

# Py 3.9+: importlib.resources.files
try:
    from importlib.resources import files as ir_files
except ImportError:  # Py<3.9 fallback
    ir_files = None
    import pkgutil

Base = declarative_base()

def _read_template():
    pkg = __package__  # "magenta_dynaconn.management.class_manager"
    if ir_files:
        return ir_files(pkg).joinpath("class_base.txt").read_text(encoding="utf-8")
    # fallback antiguo
    data = pkgutil.get_data(pkg, "class_base.txt")
    return data.decode("utf-8")

def generate_classes(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    namespace = {"Base": Base, "Table": Table, "CRUDMixin": CRUDMixin}
    generated = {}

    template = _read_template()

    for tname in tables:
        table = Table(tname, Base.metadata, autoload_with=engine)
        class_name = tname.capitalize()
        code = template.replace("{ClassName}", class_name).replace("{table_name}", tname)

        namespace["table"] = table
        exec(code, namespace, namespace)
        generated[tname] = namespace[class_name]

    return generated
