from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Estas dos líneas hacen que Alembic conozca nuestras tablas: importa la
# configuración real del proyecto (para tomar la URL de conexión del .env,
# no de alembic.ini) y cada módulo de modelos (para que `Base.metadata`
# sepa que existen "usuarios", "productos" y "ventas").
from app.caja import models as _caja_models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.productos import models as _productos_models  # noqa: F401
from app.usuarios import models as _usuarios_models  # noqa: F401
from app.ventas import models as _ventas_models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Usamos la URL de conexión armada desde el .env (app/core/config.py) en
# vez de la que viene escrita en alembic.ini, para no duplicar la
# contraseña de la base de datos en dos archivos distintos. Se usa
# directamente (sin pasarla por config.set_main_option) porque el lector
# de alembic.ini interpreta el "%" como especial y rompería contraseñas
# escapadas en la URL.
database_url = settings.database_url

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
