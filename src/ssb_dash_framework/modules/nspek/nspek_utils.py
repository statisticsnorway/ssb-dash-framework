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


def _build_nspek_conn_url(
    database_user: str,
    host: str = "localhost",
    port: int = 5432,
    database: str = "nspek",
) -> str:
    """Build the psycopg ``conninfo`` URL for the nspek postgres connection."""
    encoded_user = quote_plus(database_user)
    return f"postgresql://{encoded_user}@{host}:{port}/{database}"


def set_nspek_connection(
    database_user: str | None = None,
    host: str = "localhost",
    port: int = 5432,
    database: str = "nspek",
) -> None:
    """Helper function to configure a pooled connection to the nspek postgres database.

    Args:
        database_user: Database user (IAM principal) to connect as. Defaults to the
            ``nspek-developers`` service account.
        host: Database host. Defaults to "localhost" (e.g. a local CloudSQL proxy).
        port: Database port. Defaults to 5432.
        database: Database name. Defaults to "nspek". Override this (and host/port as
            needed) when the nspek data lives in a differently named database.
    """
    global _IS_POOLED_NSPEK, _CONNECTION_NSPEK, _CONNECTION_CALLABLE_NSPEK

    DB_USER = (
        database_user if database_user else "nspek-developers@dapla-group-sa-p-ye.iam"
    )

    conn_url = _build_nspek_conn_url(DB_USER, host=host, port=port, database=database)

    _IS_POOLED_NSPEK = True

    pool = ConnectionPool(conninfo=conn_url, min_size=1, max_size=1)
    _CONNECTION_NSPEK = pool

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
