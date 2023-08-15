import os

import sqlalchemy
from sqlalchemy import BigInteger, Column, MetaData, Table, Text  # ForeignKey, String
from sqlalchemy.engine import Connection, Engine

from ..types import DateTimeUTC, MessageRow
from . import migrations


def connect() -> sqlalchemy.engine.Engine:
    try:
        return sqlalchemy.create_engine(os.environ["DATABASE_URL"])
    except KeyError as ex:
        print("You must set the `DATABASE_URL` environment variable appropriately")
        raise ex


def sql_ensure_schema(engine: Engine) -> MetaData:
    metadata = sql_metadata()
    if not sqlalchemy.inspect(engine).has_table("messages"):
        # Set up the DB schema if we have not already
        metadata.create_all(engine)
        migrations.stamp(engine, "head")
    elif not migrations.is_at_head(engine):
        # Upgrade the DB schema if it is old
        migrations.upgrade_to(engine, "head")
    return metadata


def sql_metadata() -> MetaData:
    metadata = MetaData()
    # Table(
    #     "users",
    #     metadata,
    #     Column("id", BigInteger, primary_key=True),
    #     Column("latest_username", String, nullable=False),
    # )

    Table(
        "messages",
        metadata,
        Column("id", BigInteger, primary_key=True),
        Column(
            "dm_with_id",
            BigInteger,
            # ForeignKey(metadata.tables["users"].c.id),
            nullable=False,
        ),
        Column(
            "author_id",
            BigInteger,
            # ForeignKey(metadata.tables["users"].c.id),
            nullable=False,
        ),
        # We want raw-text versions for these, in order to track the name *at
        # the time of the message*
        Column("dm_with", Text, nullable=False),
        Column("author", Text, nullable=False),
        Column("timestamp", DateTimeUTC, nullable=False),
        Column("content", Text, nullable=False),
    )
    return metadata


def insert_new_message(
    metadata: MetaData, conn: Connection, message: MessageRow
) -> None:
    from sqlalchemy.dialects.postgresql import insert

    conn.execute(
        insert(metadata.tables["messages"]).values(message).on_conflict_do_nothing()
    )


# def upsert_user(metadata: MetaData, conn: Connection, user: UserRow) -> None:
#     from sqlalchemy.dialects.postgresql import insert

#     statement = insert(metadata.tables["users"]).values(user)
#     statement = statement.on_conflict_do_update(
#         index_elements=["id"],
#         set_={
#             "latest_username": statement.excluded.latest_username,
#         },
#     )
#     conn.execute(statement)
