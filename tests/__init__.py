import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from time import sleep
from typing import Generator, Type

import pytest
import sqlalchemy
from sqlalchemy.engine import Engine

PG_START_TIMEOUT = 5.0  # seconds


@contextmanager
def does_not_raise(exc: Type[BaseException]) -> Generator[None, None, None]:
    try:
        yield
    except exc:
        # TODO better logging output
        raise pytest.fail(f"DID RAISE {exc}")


def pg_url(pg_path: Path) -> str:
    return f"postgresql://test@:5432/test?host={str(pg_path)}"


def pg_wait_for_server(pg_process: Popen[bytes], pg_path: Path) -> Engine:
    from sqlalchemy import create_engine

    url = pg_url(pg_path)
    engine = create_engine(url)
    start = datetime.now()
    while True:
        if pg_process.poll() is not None:
            raise RuntimeError(f"Failed to launch postgres, {pg_process}")

        try:
            conn = engine.connect()
            conn.close()
            return create_engine(url)
        except sqlalchemy.exc.OperationalError as ex:
            if (datetime.now() - start).seconds > PG_START_TIMEOUT:
                raise RuntimeError(f"Failed to launch postgres, timed out, {ex}")
            pass

        sleep(0.1)


@contextmanager
def pg_start_process(pg_initdb: Path) -> Generator[Popen[bytes], None, None]:
    with (pg_initdb.parent / "db.log").open("at") as log_file:
        pg_args = ["postgres", "-D", str(pg_initdb), "-k", str(pg_initdb)]
        pg_proc = Popen(pg_args, stdin=None, stdout=log_file, stderr=log_file)
        try:
            yield pg_proc
        finally:
            pg_proc.kill()


@contextmanager
def pg_run_initdb(pg_path: Path) -> Generator[Path, None, None]:
    if pg_path.exists():
        shutil.rmtree(pg_path)

    pg_path.mkdir(parents=True, exist_ok=True)
    pg_path.chmod(0o700)
    initdb_args = [
        "initdb",
        "-D",
        str(pg_path),
        "--no-locale",
        "--encoding=UTF8",
        "--no-clean",
        "--no-sync",
    ]
    child = Popen(initdb_args, stdin=None, stdout=PIPE, stderr=PIPE)
    stdout, stderr = child.communicate()
    if child.returncode != 0:
        raise RuntimeError(
            f"initdb failed, returncode: {child.returncode},"
            f" stdout:\n{stdout.decode('utf-8')}\nstderr:\n{stderr.decode('utf-8')}"
        )
    with (pg_path / "pg_ident.conf").open("a+") as file_:
        print(f"test {os.environ['USER']} test", file=file_)

    with (pg_path.parent / "db.log").open("wt") as log_file:
        postgres_args = [
            "postgres",
            "--single",
            "-E",
            "postgres",
            "-D",
            str(pg_path),
            "-k",
            str(pg_path),
        ]
        child = Popen(
            postgres_args,
            stdin=PIPE,
            stdout=log_file,
            stderr=log_file,
        )
        stdout, stderr = child.communicate(
            input="""
            CREATE ROLE test WITH LOGIN SUPERUSER;
            CREATE DATABASE test OWNER test;
            """.encode()
        )
        if child.returncode != 0:
            raise RuntimeError(
                f"postgres DB setup failed, returncode: {child.returncode},"
                f" stdout:\n{stdout.decode('utf-8')}\nstderr:\n{stderr.decode('utf-8')}"
            )
    try:
        yield pg_path
    finally:
        shutil.rmtree(pg_path)


# Fixture wrappers around context managers; un-decorated so I can set their
# scope within individual modules


def pg_initdb_fixture(pg_path: Path) -> Generator[Path, None, None]:
    with pg_run_initdb(pg_path) as initdb_path:
        yield initdb_path


def pg_process_fixture(pg_initdb: Path) -> Generator[Popen[bytes], None, None]:
    with pg_start_process(pg_initdb) as proc:
        yield proc
