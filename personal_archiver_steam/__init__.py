import os

import secretstorage
import typer
from importlib_metadata import metadata, version
from jeepney.io.blocking import DBusConnection

from . import client, db

__version__ = version(__package__)
__all__ = ["app", "__version__"]

__metadata = metadata(__package__)


app = typer.Typer()


@app.command()
def main() -> None:
    if "IN_DEV_ENV" in os.environ:
        # Assume we're in my local dev env and try to pull secrets from
        # Secret Service API
        conn = secretstorage.dbus_init()
        username = "Shados"
        password = get_secret_by_path(conn, "/Gaming/Steam").decode("utf-8")
        refresh_token = get_secret_by_path(
            conn, "/Gaming/Steam - TOTP Refresh Token"
        ).decode("utf-8")
        shared_secret = get_secret_by_path(conn, "/Gaming/Steam - TOTP Secret").decode(
            "utf-8"
        )
    else:
        try:
            username = os.environ["STEAM_USERNAME"]
            password = os.environ["STEAM_PASSWORD"]
            refresh_token = os.environ["STEAM_TOTP_REFRESH_TOKEN"]
            shared_secret = os.environ["STEAM_TOTP_SHARED_SECRET"]
        except KeyError:
            print(
                (
                    "You must set the STEAM_USERNAME, STEAM_PASSWORD, and "
                    "STEAM_TOTP_SHARED_SECRET environment variables appropriately"
                )
            )
            raise typer.Exit()

    # Set up DB connection
    # TODO test connection failure handling
    engine = db.connect()
    metadata = db.sql_ensure_schema(engine)
    with engine.connect() as conn:
        cli = client.LogClient(metadata, conn)
        cli.run(
            username, password, shared_secret=shared_secret, refresh_token=refresh_token
        )


# Set main help message from package metadata :^). For some reason, setting
# this from the 'help' parameter to typer.Typer() does not work.
main.__doc__ = __metadata["Summary"]


def get_secret_by_path(conn: DBusConnection, path: str) -> bytes:
    collection = secretstorage.get_default_collection(conn)
    items = collection.search_items({"Path": path})
    shared_secret = next(items)
    shared_secret.unlock()
    return shared_secret.get_secret()


if __name__ == "__main__":
    app()
