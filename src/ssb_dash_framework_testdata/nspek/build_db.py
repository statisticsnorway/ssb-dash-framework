"""Load mock NSPEK data into a SQLite database for development and demonstration."""

import sqlite3
from pathlib import Path

TESTDATA_DIR = Path(__file__).parent

DATA_FILES = (
    "registreringer.sql",
    "v_registrering_versjon.sql",
    "v_update_counts.sql",
    "enhet_opplysninger.sql",
    "tema_virksomhet.sql",
    "tema_balanse.sql",
    "tema_resultat.sql",
    "tema_resultat_hist.sql",
    "tema_balanse_hist.sql",
    "kontroller.sql",
    "kontrollutslag.sql",
    "ssb_foretak.sql",
    "kommentarer.sql",
)


def _scripts(schema_file: str, testdata_dir: Path) -> list[str]:
    return [
        (testdata_dir / name).read_text(encoding="utf-8")
        for name in (schema_file, *DATA_FILES)
    ]


def seed_sqlite(database_path: str | Path, testdata_dir: Path = TESTDATA_DIR) -> None:
    """Create and populate the NSPEK tables in a SQLite database.

    Args:
        database_path: Path to the SQLite file, or ":memory:".
        testdata_dir: Folder containing the .sql files to execute.
    """
    conn = sqlite3.connect(str(database_path))

    # Register custom PostgreSQL-compatible function mockups for SQLite triggers
    def current_setting(setting_name: str) -> str:
        return ""

    def now() -> str:
        from datetime import datetime
        return datetime.now().isoformat(" ")

    conn.create_function("current_setting", 1, current_setting)
    conn.create_function("now", 0, now)

    try:
        for script in _scripts("schema_sqlite.sql", testdata_dir):
            conn.executescript(script)
        conn.commit()
    finally:
        conn.close()
