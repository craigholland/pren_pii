import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine, text
from pii.database.models.core.main import Base, db
from pii.database.models.core.service_object import ServiceObject

@pytest.fixture(scope="session")
def engine():
    with PostgresContainer("postgres:14") as pg:
        url = pg.get_connection_url()
        print(f"[TEST] Postgres test container started at: {url}")
        engine = create_engine(url)

        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

        Base.metadata.create_all(engine)
        ServiceObject.metadata.create_all(engine)
        db.engine = engine

        yield engine

        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def session(engine):
    """
    For every test:
      - open a SAVEPOINT transaction
      - bind db.Session() to that connection
      - roll everything back at tear‐down
    """
    conn = engine.connect()
    trans = conn.begin()

    db.Session.configure(bind=conn)
    sess = db.Session()

    yield sess

    sess.close()
    trans.rollback()
    conn.close()
