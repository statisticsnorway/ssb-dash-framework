import sqlite3

from ssb_dash_framework.utils.config_tools import connection
from ssb_dash_framework.utils.config_tools import get_connection
from ssb_dash_framework_testdata.altinn import build_db


def build_in_memory_sqlite_for_demo() -> None:
    # set_sqlite_connection() opens a new sqlite3 connection per get_connection()
    # call, so plain ":memory:" would give each call an empty, separate database.
    # A shared-cache in-memory URI lets every connection see the same database,
    # as long as at least one connection to it stays open for the process lifetime.
    DB_URI = "file:ssb_dash_demo?mode=memory&cache=shared"
    _keep_alive = sqlite3.connect(DB_URI)

    build_db.seed_sqlite(DB_URI)
    connection.set_sqlite_connection(DB_URI)

    with get_connection() as conn:
        t = conn.list_tables()
        assert t == [
            "enheter",
            "enhetsinfo",
            "kontaktinfo",
            "skjemadata",
            "skjemamottak",
        ]
