from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from alembic_utils.pg_extension import PGExtension
from alembic_utils.replaceable_entity import register_entities
from dotenv import load_dotenv

# Load environment variables from .env in database/data folder
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'data', '.env')
load_dotenv(dotenv_path)

# Import SQLAlchemy URL and Base metadata
from pii.database.db_config import SQLALCHEMY_DATABASE_URL
from pii.database.models.core.service_object import ServiceObject
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# set the SQLAlchemy URL for Alembic
config.set_main_option('sqlalchemy.url', SQLALCHEMY_DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
#target_metadata = Base.metadata
target_metadata = ServiceObject.metadata

uuid_ossp_ext = PGExtension(
    schema="public",
    signature="uuid-ossp",
)
register_entities([uuid_ossp_ext])

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
