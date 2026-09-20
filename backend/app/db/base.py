# base.py = el "molde común" del que heredan todas las tablas (usuarios,
# productos, ventas, etc.). SQLAlchemy usa esta clase `Base` para saber
# cuáles clases de Python representan tablas reales en PostgreSQL.
#
# Alembic (la herramienta de migraciones) también importa `Base` para
# comparar "lo que hay en el código" contra "lo que hay en la base de datos"
# y generar automáticamente el script que actualiza las tablas.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
