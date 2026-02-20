from collections.abc import Callable
from contextlib import contextmanager

from eimerdb import EimerDBInstance
from ibis.backends.postgres import Backend
from psycopg_pool import ConnectionPool

_IS_POOLED: bool | None = None
_CONNECTION: object | None = None
_CONNECTION_CALLABLE: Callable | None = None


def set_eimerdb_connection(  # TODO: Test
    bucket_name,
    eimer_name,
):
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE
    _IS_POOLED = False
    _CONNECTION = EimerDBInstance(
        bucket_name=bucket_name,
        eimer_name=eimer_name,
    )

    @contextmanager
    def _eimer_ibis_converter(
        necessary_tables: list[str] | None = None, partition_select=None
    ):
        global _CONNECTION_INSTANCE
        conn = ibis.connect("duckdb://")
        if necessary_tables is None:
            necessary_tables = [
                "enheter",
                "kontaktinfo",
                "skjemamottak",
                "skjemadata",
                "datatyper",
            ]
        if "enheter" in necessary_tables:
            enheter = _CONNECTION_INSTANCE.query(
                "SELECT * FROM enheter",
                partition_select=partition_select,
            )
            conn.create_table("enheter", enheter)
        if "kontaktinfo" in necessary_tables:
            kontaktinfo = _CONNECTION_INSTANCE.query(
                "SELECT * FROM kontaktinfo",
                partition_select=partition_select,
            )
            conn.create_table("kontaktinfo", kontaktinfo)
        if "skjemamottak" in necessary_tables:
            skjemamottak = _CONNECTION_INSTANCE.query(
                "SELECT * FROM skjemamottak",
                partition_select=partition_select,
            )
            conn.create_table("skjemamottak", skjemamottak)
        if "skjemadata" in necessary_tables:
            skjemadata = _CONNECTION_INSTANCE.query(
                "SELECT * FROM skjemadata_hoved",
                partition_select=partition_select,
            )
            conn.create_table("skjemadata_hoved", skjemadata)
        if "datatyper" in necessary_tables:
            datatyper = _CONNECTION_INSTANCE.query(
                "SELECT * FROM datatyper",
                partition_select=partition_select,
            )
            conn.create_table("datatyper", datatyper)

        yield conn

    _CONNECTION_CALLABLE = _eimer_ibis_converter


def set_postgres_connection(database_url):
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE
    _IS_POOLED = True

    pool = ConnectionPool(conninfo=database_url, min_size=1, max_size=1)
    _CONNECTION = pool

    @contextmanager
    def _wrap_ibis_postgres():
        with pool.connection() as raw_conn:
            yield Backend.from_connection(raw_conn)

    set_connection(_wrap_ibis_postgres)


@contextmanager
def get_connection(*args, **kwargs):
    global _IS_POOLED, _CONNECTION_CALLABLE
    if not _CONNECTION_CALLABLE:
        raise ValueError("No connection has been set.")
    with _CONNECTION_CALLABLE(*args, **kwargs) as conn:
        yield conn


def set_connection(connection_func, is_pooled=False):
    global _IS_POOLED, _CONNECTION, _CONNECTION_CALLABLE

    _IS_POOLED = is_pooled

    _CONNECTION_CALLABLE = connection_func
