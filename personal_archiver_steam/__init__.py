import jeepney
import secretstorage
import typer
from importlib_metadata import metadata, version

from . import client, db

__version__ = version(__package__)
__all__ = ["app", "__version__"]

__metadata = metadata(__package__)


app = typer.Typer()


@app.command()
def main() -> None:
    # Pull secrets from Secret Service API
    conn = secretstorage.dbus_init()
    username = "Shados"
    shared_secret = get_secret_by_path(
        conn, "/Phone/Apps/Steam Guard - TOTP Secret"
    ).decode("utf-8")
    password = get_secret_by_path(conn, "/Gaming/Steam").decode("utf-8")

    # Set up DB connection
    # TODO test connection failure handling
    engine = db.connect()
    metadata = db.sql_ensure_schema(engine)
    with engine.connect() as conn:
        cli = client.LogClient(metadata, conn)
        cli.run(username, password, shared_secret=shared_secret)


# Set main help message from package metadata :^). For some reason, setting
# this from the 'help' parameter to typer.Typer() does not work.
main.__doc__ = __metadata["Summary"]


def get_secret_by_path(conn: jeepney.io.blocking.DBusConnection, path: str) -> bytes:
    collection = secretstorage.get_default_collection(conn)
    items = collection.search_items({"Path": path})
    shared_secret = next(items)
    shared_secret.unlock()
    return shared_secret.get_secret()


if __name__ == "__main__":
    app()
