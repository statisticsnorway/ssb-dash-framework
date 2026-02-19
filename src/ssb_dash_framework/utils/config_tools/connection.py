from collections.abc import Callable

from psycopg_pool import ConnectionPool

_IS_POOLED: bool | None = None
_CONNECTION_INSTANCE: object | None = None
_CONNECTION_CALLABLE: Callable | None = None


def set_postgres_connection(database_url):
    global _IS_POOLED, _CONNECTION_INSTANCE, _CONNECTION_CALLABLE
    _IS_POOLED = True
    pool = ConnectionPool(conninfo=database_url, min_size=1, max_size=1)

    _CONNECTION_CALLABLE = pool.connection()


def set_eimerdb_connection():
    global _IS_POOLED, _CONNECTION_INSTANCE, _CONNECTION_CALLABLE
    _IS_POOLED = False


def get_connection():
    global _IS_POOLED, _CONNECTION_INSTANCE, _CONNECTION_CALLABLE


def set_connection():
    global _IS_POOLED, _CONNECTION_INSTANCE, _CONNECTION_CALLABLE
