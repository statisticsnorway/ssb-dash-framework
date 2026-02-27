from collections.abc import Callable
from collections.abc import Iterator
from contextlib import AbstractContextManager
from contextlib import contextmanager
from typing import Any

import ibis
from eimerdb import EimerDBInstance
from ibis.backends import BaseBackend
from ibis.backends.postgres import Backend
from psycopg_pool import ConnectionPool

_IS_POOLED: bool | None = None
_CONNECTION: object | None = None
_CONNECTION_CALLABLE: Callable[..., Any] | None = None


def _get_connection_object() -> object | None:
    """Getter function to retrieve the connection object.

    Used for retrieving the connection object the app is using as default after running 'set_connection'.
    """
    global _CONNECTION
    return _CONNECTION


def _get_connection_callable() -> Callable[..., Any] | None:
    """Getter function to retrieve the connection callable.

    Used for retrieving the connection callable the app is using as default after running 'set_connection'.
    """
    global _CONNECTION_CALLABLE
    return _CONNECTION_CALLABLE


@contextmanager
def get_connection(**kwargs: Any) -> Iterator[BaseBackend]:
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
    global _IS_POOLED, _CONNECTION_CALLABLE
    if not _CONNECTION_CALLABLE:
        raise ValueError("No connection has been set.")
    with _CONNECTION_CALLABLE(**kwargs) as conn:
        yield conn


def set_connection(
    connection_func: Callable[..., AbstractContextManager[BaseBackend]],
    is_pooled: bool = False,
) -> None:
    """Setter function to set the function for generating ibis connection objects.

    Args:
        connection_func: Callable that needs to provide an ibis connection using '@contextmanager' decorator that and yielding an ibis connection.
        is_pooled: Indicates if the connection method utilizes pooling. Defaults to False.

    Raises:
        TypeError: If yielded connection object is not an ibis.BaseBackend object.
    """
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE

    _IS_POOLED = is_pooled

    with connection_func() as yielded_conn_object:
        if not isinstance(yielded_conn_object, BaseBackend):
            raise TypeError(
                f"Currently this framework only supports connections based on ibis-framework backend objects. Received '{type(yielded_conn_object)}'"
            )

    _CONNECTION_CALLABLE = connection_func


def set_postgres_connection(
    database_url: str, pool_min_size: int = 1, pool_max_size: int = 1
) -> None:
    """Helper function to configure a pooled connection to a postgres database.

    Args:
        database_url: Connection url for the database. Gets passed to psycopg_pool.ConnectionPool as conninfo argument.
        pool_min_size: The minimum size of the pool. Defaults to 1.
        pool_max_size: The maximum size of the pool. Defaults to 1.
    """
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE
    _IS_POOLED = True

    pool = ConnectionPool(
        conninfo=database_url, min_size=pool_min_size, max_size=pool_max_size
    )
    _CONNECTION = pool

    @contextmanager
    def _wrap_ibis_postgres(*args: Any, **kwargs: Any) -> Iterator[BaseBackend]:
        with pool.connection() as raw_conn:
            yield Backend.from_connection(raw_conn)

    set_connection(_wrap_ibis_postgres)


def set_eimerdb_connection(
    bucket_name: str, eimer_name: str, tables_default: list[str] | None = None
) -> None:
    """Helper function to configure a ssb-dash-framework compatible connection to an eimerdb database.

    Works by reading the data from eimerdb, creating an in-memory duckdb database for the read data, and then creating an ibis connection to that in-memory duckdb database.
    Could probably be optimized to reuse the same in-memory database, but as the future of eimerdb is unsure that might be a waste of time.

    Args:
        bucket_name: The name of the Google Cloud Storage bucket where the EimerDB database is hosted.
        eimer_name: The name of the EimerDB instance, the database name so to speak.
        tables_default: Default tables to load when nothing else is specified. Some modules require a pre-set selection of tables to be loaded into the duckdb database to function properly.
            This argument provides a way to affect which tables are loaded by default.
            If left as None, it defaults to using 'DEFAULT_TABLES' which are 'enheter', 'kontaktinfo', 'skjemamottak', 'skjemadata_hoved' and 'datatyper'

    Raises:
        ValueError: If the default tables provided is not a list of strings.
    """
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE
    _IS_POOLED = False
    _CONNECTION = EimerDBInstance(
        bucket_name=bucket_name,
        eimer_name=eimer_name,
    )

    DEFAULT_TABLES = [
        "enheter",
        "kontaktinfo",
        "skjemamottak",
        "skjemadata_hoved",
        "datatyper",
    ]
    if tables_default is None:
        necessary_tables_default = DEFAULT_TABLES

    if not isinstance(tables_default, list) or not all(
        isinstance(item, str) for item in tables_default
    ):
        raise ValueError(
            f"'tables_default' must be list[str]. Received: {tables_default!r}"
        )

    @contextmanager
    def _eimer_ibis_converter(
        necessary_tables: list[str] | None = None,
        partition_select: None | dict[str, list[Any]] = None,
    ) -> Iterator[BaseBackend]:
        global _CONNECTION
        conn = ibis.connect("duckdb://")

        tables_to_read = necessary_tables or necessary_tables_default

        if not isinstance(necessary_tables_default, list) or not all(
            isinstance(item, str) for item in necessary_tables_default
        ):
            raise ValueError(
                f"'necessary_tables_default' must be list[str]. "
                f"Received: {necessary_tables_default!r}"
            )

        if "enheter" in tables_to_read:
            enheter = _CONNECTION.query(
                "SELECT * FROM enheter",
                partition_select=partition_select,
            )
            conn.create_table("enheter", enheter)
        if "kontaktinfo" in tables_to_read:
            kontaktinfo = _CONNECTION.query(
                "SELECT * FROM kontaktinfo",
                partition_select=partition_select,
            )
            conn.create_table("kontaktinfo", kontaktinfo)
        if "skjemamottak" in tables_to_read:
            skjemamottak = _CONNECTION.query(
                "SELECT * FROM skjemamottak",
                partition_select=partition_select,
            )
            conn.create_table("skjemamottak", skjemamottak)
        if "skjemadata_hoved" in tables_to_read:
            skjemadata = _CONNECTION.query(
                "SELECT * FROM skjemadata_hoved",
                partition_select=partition_select,
            )
            conn.create_table("skjemadata_hoved", skjemadata)
        if "datatyper" in tables_to_read:
            datatyper = _CONNECTION.query(
                "SELECT * FROM datatyper",
                partition_select=partition_select,
            )
            conn.create_table("datatyper", datatyper)

        yield conn

    _CONNECTION_CALLABLE = _eimer_ibis_converter
