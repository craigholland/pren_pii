from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqla_wrapper import SQLAlchemy
from pii.database import db_config
Base = declarative_base()

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
if pg_uri := getattr(db_config, 'SQLALCHEMY_DATABASE_URL', None):
    db = SQLAlchemy(pg_uri)
    db.Model.metadata = MetaData(naming_convention=convention)
    engine = create_engine(
        pg_uri,
        connect_args={"connect_timeout": db_config.DB_CONNECT_TIMEOUT},
    )
else:
    raise ValueError("DATABASE_URL is not set")

