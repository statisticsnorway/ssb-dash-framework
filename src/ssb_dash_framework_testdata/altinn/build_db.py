"""Load the Altinn testdata in this folder into a SQLite or PostgreSQL database."""

import sqlite3
from pathlib import Path

TESTDATA_DIR = Path(__file__).parent

DATA_FILES = (
    "enheter.sql",
    "enhetsinfo.sql",
    "skjemamottak.sql",
    "kontaktinfo.sql",
    "skjemadata.sql",
)


def _scripts(schema_file: str, testdata_dir: Path) -> list[str]:
    return [
        (testdata_dir / name).read_text(encoding="utf-8")
        for name in (schema_file, *DATA_FILES)
    ]


def seed_sqlite(database_path: str | Path, testdata_dir: Path = TESTDATA_DIR) -> None:
    """Create and populate the Altinn tables in a SQLite database.

    Args:
        database_path: Path to the SQLite file, or ":memory:".
        testdata_dir: Folder containing the .sql files to execute.
    """
    conn = sqlite3.connect(str(database_path))
    try:
        for script in _scripts("schema_sqlite.sql", testdata_dir):
            conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


def seed_postgres(database_url: str, testdata_dir: Path = TESTDATA_DIR) -> None:
    """Create and populate the Altinn tables in a PostgreSQL database.

    Args:
        database_url: libpq connection string.
        testdata_dir: Folder containing the .sql files to execute.
    """
    import psycopg

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for script in _scripts("schema_postgres.sql", testdata_dir):
                cur.execute(script)  # type: ignore[arg-type]
        conn.commit()


def seed_parquedit(): ...


def build_in_memory_db(testdata_dir: Path = TESTDATA_DIR) -> sqlite3.Connection:
    """Create an in-memory SQLite database populated with the Altinn testdata.

    Args:
        testdata_dir: Folder containing the .sql files to execute.

    Returns:
        An open connection to the populated in-memory database. The caller is
        responsible for closing it.
    """
    conn = sqlite3.connect(":memory:")
    for script in _scripts("schema_sqlite.sql", testdata_dir):
        conn.executescript(script)
    conn.commit()
    return conn
