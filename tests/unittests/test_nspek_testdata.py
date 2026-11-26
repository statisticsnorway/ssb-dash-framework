"""Checks that the configured backend serves the NSPEK testdata correctly."""

import tempfile
from pathlib import Path

from ssb_dash_framework.modules.nspek.nspek_utils import get_nspek_connection
from ssb_dash_framework.modules.nspek.nspek_utils import set_nspek_sqlite_connection
from ssb_dash_framework_testdata.nspek import build_db

EXPECTED_TABLES = {
    "registrering",
    "v_registrering_versjon",
    "v_update_counts",
    "tema_virksomhet",
    "tema_balanse",
    "tema_resultat",
    "tema_resultat_hist",
    "tema_balanse_hist",
    "kommentarfelt_test_2",
    "kontroller",
    "kontrollutslag",
    "ssb_foretak",
    "tema_omloepsmiddel",
}


def test_nspek_sqlite_seeding_and_connection() -> None:
    # 1. Create a temp sqlite file
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # 2. Seed it
        build_db.seed_sqlite(db_path)

        # 3. Configure the app's NSPEK connection to use SQLite
        set_nspek_sqlite_connection(str(db_path))

        # 4. Check tables are present via get_nspek_connection()
        with get_nspek_connection() as conn:
            available_tables = set(conn.list_tables())
            assert EXPECTED_TABLES <= available_tables

            # 5. Check we can query some tables
            reg_count = conn.table("registrering").count().to_pyarrow().as_py()
            assert reg_count >= 1

            foretak_count = conn.table("ssb_foretak").count().to_pyarrow().as_py()
            assert foretak_count >= 1

    finally:
        db_path.unlink(missing_ok=True)
