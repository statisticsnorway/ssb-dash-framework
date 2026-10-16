"""Load the Altinn testdata in this folder into a SQLite or PostgreSQL database."""

import sqlite3
from pathlib import Path

from ssb_dash_framework import get_connection

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


def seed_parquedit(test_dir: Path, testdata_dir: Path = TESTDATA_DIR): 
    import json
    from ssb_dash_framework.utils.config_tools.connection import _create_test_connnection_parquedit
    #from ...ssb_dash_framework.utils.config_tools.connection import _create_test_connnection_parquedit
    conn = _create_test_connnection_parquedit(test_dir)
    raw_conn = conn._get_connection().raw
    #conn.create_table
    product_name = "test_obj"
    tag_info = json.dumps(
        {
            "product_name": product_name,
            "user_defined_id": [],
        }
    )
    for script in _scripts("schema_parquedit.sql", testdata_dir):
        #print(script)
        raw_conn.execute(script).commit()
        #raw_conn.execute(f"COMMENT ON TABLE {table_name} IS '{tag_info}';")
    raw_conn.execute(f"COMMENT ON TABLE skjemadata IS '{tag_info}';")
    raw_conn.execute(f"COMMENT ON TABLE skjemamottak IS '{tag_info}';")
    #with get_connection() as conn:
        


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
