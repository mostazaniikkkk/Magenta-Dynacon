from .db_registry import DatabaseRegistry

__all__ = ["DatabaseRegistry"]
__version__ = "0.1.0"

# Nota en README:
# Internals (sin estabilidad garantizada):
#   from magenta_dynaconn.conn.db_handler import DbHandle
#   from magenta_dynaconn.class_manager.class_generator import Base, generate_classes
#   from magenta_dynaconn.class_manager.crud_mixing import CRUDMixin
