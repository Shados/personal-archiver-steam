# This is for integration tests against an actual PostgreSQL database instance
from datetime import datetime, timezone
from typing import List, Tuple

from pytest import mark
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection, Engine

from personal_archiver_steam import db
from personal_archiver_steam.types import MessageRow

from . import does_not_raise


# TODO test creating schema on a db w/ mis-matching schema
def test_ensure_schema(pg_server: Engine) -> None:
    with does_not_raise(Exception):
        db.sql_ensure_schema(pg_server)


@mark.depends(on=["test_ensure_schema"])
def test_schema_deletion(pg_server: Engine) -> None:
    with does_not_raise(Exception):
        metadata = db.sql_ensure_schema(pg_server)
        metadata.drop_all(pg_server)


@mark.depends(on=["test_ensure_schema"])
def test_ensure_schema_on_existing(pg_server: Engine) -> None:
    with does_not_raise(Exception):
        db.sql_ensure_schema(pg_server)
        db.sql_ensure_schema(pg_server)


# TEST_USERS = [
#     (8, "Space Raptor"),
#     (35, "Friend-Shaped Entity"),
# ]


# @mark.depends(on=["test_ensure_schema"])
# def test_upsert_new_user(db_conn: Tuple[MetaData, Connection]) -> None:
#     metadata, conn = db_conn
#     db.upsert_user(metadata, conn, TEST_USERS[0])
#     db.upsert_user(metadata, conn, TEST_USERS[1])


# @mark.depends(on=["test_upsert_new_user"])
# def test_upsert_existing_user(db_conn: Tuple[MetaData, Connection]) -> None:
#     metadata, conn = db_conn
#     db.upsert_user(metadata, conn, TEST_USERS[0])
#     db.upsert_user(metadata, conn, TEST_USERS[1])

#     updated_users = [
#         (8, "A New Username"),
#         (35, "Test Username 12"),
#     ]
#     db.upsert_user(metadata, conn, updated_users[0])
#     db.upsert_user(metadata, conn, updated_users[1])


TEST_MESSAGES: List[MessageRow] = [
    (
        0,
        35,
        8,
        "Friend-Shaped Entity",
        "Space Raptor",
        datetime.now(timezone.utc),
        "Hello!",
    ),
    (
        0,
        35,
        35,
        "Friend-Shaped Entity",
        "Friend-Shaped Entity",
        datetime.now(timezone.utc),
        "Yo",
    ),
]


@mark.depends(on=["test_ensure_schema"])
def test_insert_new_message(db_conn: Tuple[MetaData, Connection]) -> None:
    metadata, conn = db_conn
    db.insert_new_message(metadata, conn, TEST_MESSAGES[0])
    db.insert_new_message(metadata, conn, TEST_MESSAGES[1])


# TODO message read test; not functionality actually present in
# personal_archiver_steam, but probably should verify writes are *actually*
# successful with a basic raw SQL query or something...
