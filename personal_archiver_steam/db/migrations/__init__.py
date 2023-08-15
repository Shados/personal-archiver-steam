from contextlib import contextmanager
from typing import Any, Generator

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from sqlalchemy.engine import Connection, Engine


@contextmanager
def connected_config(engine: Engine) -> Generator[Config, None, None]:
    with engine.begin() as conn:
        cfg = configure_migration_env(Config(), conn)
        yield cfg


def configure_migration_env(cfg: Config, conn: Connection) -> Config:
    cfg.attributes["connection"] = conn
    # TODO dynamically look up module reference
    cfg.set_main_option("script_location", "personal_archiver_steam.db:migrations")
    return cfg


def upgrade_to(engine: Engine, rev: str) -> None:
    # TODO replace with something that doesn't use the command version?
    with connected_config(engine) as cfg:
        command.upgrade(cfg, rev)


def downgrade_to(engine: Engine, rev: str) -> None:
    # TODO replace with something that doesn't use the command version?
    with connected_config(engine) as cfg:
        command.downgrade(cfg, rev)


def current_heads(engine: Engine) -> Any:
    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        return set(context.get_current_heads())


def is_at_head(engine: Engine) -> Any:
    with engine.begin() as conn:
        cfg = configure_migration_env(Config(), conn)
        script_dir = script.ScriptDirectory.from_config(cfg)
        context = migration.MigrationContext.configure(conn)
        return set(context.get_current_heads()) == set(script_dir.get_heads())


def stamp(engine: Engine, rev: str) -> Any:
    with connected_config(engine) as cfg:
        command.stamp(cfg, rev)
