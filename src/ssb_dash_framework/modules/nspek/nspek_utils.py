import atexit
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
from ibis import BaseBackend
from ibis.backends.postgres import Backend
from psycopg_pool import ConnectionPool

_IS_POOLED_NSPEK: bool | None = None
_CONNECTION_NSPEK: object | None = None
_CONNECTION_CALLABLE_NSPEK: Callable[..., Any] | None = None

# Global dictionary to simulate PostgreSQL session GUCs in SQLite demo mode
_SQLITE_GUC: dict[str, str] = {
    "nspek_app.user_id": "demo",
    "nspek_app.process_type": "",
}


class SQLiteDemoConnectionWrapper:
    """A wrapper around an Ibis SQLite connection that translates PostgreSQL-specific SQL syntax."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def raw_sql(self, query: str, *args: Any, **kwargs: Any) -> Any:
        import re

        cleaned_query = query.strip()
        # 1. Ignore/Handle PostgreSQL GUC / session configurations
        if (
            cleaned_query.upper().startswith("SET ")
            or "SET NSPEK_APP." in cleaned_query.upper()
        ):
            match = re.match(
                r"SET\s+([a-zA-Z0-9_.]+)\s*=\s*['\"]?([^'\";]+)['\"]?",
                cleaned_query,
                re.IGNORECASE,
            )
            if match:
                key = match.group(1).lower()
                val = match.group(2)
                _SQLITE_GUC[key] = val

            class DummyCursor:
                def fetchall(self) -> list:
                    return []

                @property
                def description(self) -> list:
                    return []

            return DummyCursor()

        # 2. Translate SELECT DISTINCT ON (col) ... to standard SQL window functions / CTEs
        match = re.search(
            r"SELECT\s+DISTINCT\s+ON\s*\(([^)]+)\)\s*(.*?)\s*FROM\s+([a-zA-Z0-9_.]+)\s*WHERE\s*(.*?)\s*ORDER\s+BY\s+(.*)",
            cleaned_query,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            partition_col = match.group(1).strip()
            select_cols = match.group(2).strip()
            table_name = match.group(3).strip()
            where_clause = match.group(4).strip()
            order_by = match.group(5).strip()

            # Clean up order_by for SQLite's PARTITION ORDER BY (remove the partition col prefix)
            partition_order = order_by
            if partition_order.startswith(partition_col):
                partition_order = (
                    partition_order[len(partition_col) :].lstrip(",").strip()
                )

            new_query = f"""
                WITH ranked AS (
                    SELECT {select_cols},
                           ROW_NUMBER() OVER (PARTITION BY {partition_col} ORDER BY {partition_order}) as rn
                    FROM {table_name}
                    WHERE {where_clause}
                )
                SELECT {select_cols}
                FROM ranked
                WHERE rn = 1
            """
            return self._conn.raw_sql(new_query, *args, **kwargs)

        return self._conn.raw_sql(query, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


def set_nspek_sqlite_connection(database_path: str) -> None:
    """Helper function to configure a connection to a SQLite database for NSPEK.

    Args:
        database_path: Path to the SQLite database file.
    """
    import ibis

    global _IS_POOLED_NSPEK, _CONNECTION_NSPEK, _CONNECTION_CALLABLE_NSPEK
    _IS_POOLED_NSPEK = False

    @contextmanager
    def _wrap_ibis_sqlite(*args: Any, **kwargs: Any) -> Iterator[BaseBackend]:
        conn = ibis.sqlite.connect(database_path)

        # Register custom PostgreSQL-compatible function mockups for SQLite
        raw_conn = conn.con

        try:
            raw_conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        try:
            raw_conn.execute("PRAGMA busy_timeout=30000;")
        except Exception:
            pass

        def date_trunc(unit, value):
            if not value:
                return None
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(value.split(".")[0])
                if unit == "month":
                    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(" ")
                elif unit == "year":
                    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(" ")
                return dt.isoformat(" ")
            except Exception:
                return value

        def now():
            from datetime import datetime
            return datetime.now().isoformat(" ")

        def nextval(seq_name):
            import time
            return int(time.time() * 1000) % 100000000

        def current_setting(setting_name):
            return _SQLITE_GUC.get(setting_name.lower(), "")

        raw_conn.create_function("DATE_TRUNC", 2, date_trunc)
        raw_conn.create_function("now", 0, now)
        raw_conn.create_function("nextval", 1, nextval)
        raw_conn.create_function("current_setting", 1, current_setting)

        # Attach the database to itself under expected Postgres schemas/aliases
        conn.raw_sql(f"ATTACH DATABASE '{database_path}' AS nspek_core")
        conn.raw_sql(f"ATTACH DATABASE '{database_path}' AS resultatregnskap")
        conn.raw_sql(f"ATTACH DATABASE '{database_path}' AS balanseregnskap")
        conn.raw_sql(f"ATTACH DATABASE '{database_path}' AS virksomhet")
        conn.raw_sql(f"ATTACH DATABASE '{database_path}' AS omloepsmidler")

        try:
            yield SQLiteDemoConnectionWrapper(conn)  # type: ignore[yield-type]
        finally:
            try:
                raw_conn.commit()
            except Exception:
                pass
            try:
                raw_conn.close()
            except Exception:
                pass

    _CONNECTION_CALLABLE_NSPEK = _wrap_ibis_sqlite


def set_nspek_connection(database_user: str | None = None) -> None:
    """Helper function to configure a pooled connection to a postgres database.

    Args:
        database_url: Connection url for the database. Gets passed to psycopg_pool.ConnectionPool as conninfo argument.
    """
    global _IS_POOLED_NSPEK, _CONNECTION_NSPEK, _CONNECTION_CALLABLE_NSPEK

    if _IS_POOLED_NSPEK is False:
        # SQLite connection has been explicitly configured, do not override with Postgres
        return

    DB_USER = (
        database_user if database_user else "nspek-developers@dapla-group-sa-p-ye.iam"
    )

    encoded_user = quote_plus(DB_USER)
    conn_url = f"postgresql://{encoded_user}@localhost:5432/nspek"
    if DB_USER.startswith("nspek-developers"):
        print(conn_url)

    _IS_POOLED_NSPEK = True

    # If a previous call already configured a pool, close it and drop its exit
    # hook so exactly one pool (and one atexit handler) is ever live. Safe
    # because every caller borrows connections through short-lived
    # ``with get_nspek_connection() as conn:`` blocks -- nothing holds a pooled
    # connection across this reconfiguration.
    if isinstance(_CONNECTION_NSPEK, ConnectionPool):
        atexit.unregister(_CONNECTION_NSPEK.close)
        _CONNECTION_NSPEK.close()

    pool = ConnectionPool(conninfo=conn_url, min_size=1, max_size=1)
    _CONNECTION_NSPEK = pool

    # psycopg_pool opens daemon worker ('pool-N-worker-M') and scheduler
    # threads as soon as the pool is created. If the pool is never closed those
    # threads are still running at interpreter shutdown, and psycopg_pool warns
    # "couldn't stop thread 'pool-1-worker-0' within 5.0 seconds" on exit (e.g.
    # when the app is stopped with Ctrl+C). Closing the pool on exit stops them
    # cleanly. ConnectionPool.close() is idempotent, so explicit closes
    # elsewhere stay safe. Registered before the validation below so the pool is
    # still cleaned up if connecting fails.
    atexit.register(pool.close)

    @contextmanager
    def _wrap_ibis_postgres(*args: Any, **kwargs: Any) -> Iterator[BaseBackend]:
        with pool.connection() as raw_conn:
            yield Backend.from_connection(raw_conn)

    with _wrap_ibis_postgres() as yielded_conn_object:
        if not isinstance(yielded_conn_object, BaseBackend):
            raise TypeError(
                f"Currently this framework only supports connections based on ibis-framework backend objects. Received '{type(yielded_conn_object)}'"
            )

    _CONNECTION_CALLABLE_NSPEK = _wrap_ibis_postgres


def _get_nspek_connection_object() -> object | None:
    """Getter function to retrieve the connection object.

    Used for retrieving the connection object the app is using as default after running 'set_connection'.
    """
    global _CONNECTION_NSPEK
    return _CONNECTION_NSPEK


def _get_nspek_connection_callable() -> Callable[..., Any] | None:
    """Getter function to retrieve the connection callable.

    Used for retrieving the connection callable the app is using as default after running 'set_connection'.
    """
    global _CONNECTION_CALLABLE_NSPEK
    return _CONNECTION_CALLABLE_NSPEK


@contextmanager
def get_nspek_connection(**kwargs: Any) -> Iterator[BaseBackend]:
    """Getter function to get the ibis connection object.

    Args:
        **kwargs: Leaves room for connections that require keyword arguments.

    Yields:
        conn: Connection object, primarily an ibis.Backend object.

    Example:
        with get_connection() as conn:
            t = conn.table('datatable')
            t.select([*variables]).to_pandas()

    Raises:
        ValueError: If no connection has been set using 'set_connection()'.
    """
    global _IS_POOLED_NSPEK, _CONNECTION_CALLABLE_NSPEK
    if not _CONNECTION_CALLABLE_NSPEK:
        raise ValueError("No connection has been set.")
    with _CONNECTION_CALLABLE_NSPEK(**kwargs) as conn:
        yield conn


if __name__ == "__main__":
    set_nspek_connection("strukt-naering-developers@dapla-group-sa-p-ye.iam")
    orgnr = "979443137"
    with get_nspek_connection() as conn:
        query = f"""
            SELECT DISTINCT ON (variabel)
                variabel,
                kommentar,
                opprettet,
                opprettet_av
            FROM nspek_core.kommentarfelt_test_2
            WHERE orgnr = '{orgnr}'
            AND nivaa = 'variabel'
            AND aktiv = true
            ORDER BY variabel, opprettet DESC
        """

        cursor = conn.raw_sql(query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    df = pd.DataFrame(rows, columns=columns)
    print(df)
