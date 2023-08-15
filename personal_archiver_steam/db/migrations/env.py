from logging.config import fileConfig

from alembic import context

# Annoyingly, the way alembic runs the env.py means it isn't considered part of
# a package, so no relative imports for me
from personal_archiver_steam import db
from personal_archiver_steam.db import sql_metadata
from personal_archiver_steam.db.migrations import configure_migration_env

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = sql_metadata()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
conn = context.config.attributes.get("connection", None)

if conn is None:
    engine = db.connect()
    conn = engine.connect()

cfg = configure_migration_env(context.config, conn)
context.configure(connection=conn, target_metadata=target_metadata)

with context.begin_transaction():
    context.run_migrations()
