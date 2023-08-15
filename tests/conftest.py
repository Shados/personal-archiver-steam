import os
from pathlib import Path
from typing import Generator, Tuple

import pytest
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection, Engine

from personal_archiver_steam import db

from . import pg_initdb_fixture, pg_process_fixture, pg_wait_for_server

pg_server = pytest.fixture(pg_wait_for_server, scope="session")
pg_process = pytest.fixture(pg_process_fixture, scope="session")
pg_initdb = pytest.fixture(pg_initdb_fixture, scope="session")


@pytest.fixture
def db_conn(
    empty_db: Tuple[MetaData, Engine]
) -> Generator[Tuple[MetaData, Connection], None, None]:
    metadata, engine = empty_db
    with engine.connect() as conn:
        yield (metadata, conn)


@pytest.fixture
def empty_db(
    pg_server: Engine,
) -> Generator[Tuple[MetaData, Engine], None, None]:
    metadata = db.sql_ensure_schema(pg_server)
    yield (metadata, pg_server)
    metadata.drop_all(pg_server)


@pytest.fixture(scope="session")
def pg_path() -> Path:
    # TODO Give a human-readable error instead of a KeyError if this is missing?
    return Path(os.environ["TEST_PGDATA"])
