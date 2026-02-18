import logging
from collections.abc import Callable
from urllib.parse import quote_plus

import ibis
from eimerdb import EimerDBInstance
from sqlalchemy import create_engine

from .core_query_functions import conn_is_ibis

logger = logging.getLogger(__name__)

_CONNECTION_FACTORY: None | Callable[[], object] = None
_CONNECTION_INSTANCE: None | object = None
_IS_POOLED: bool = False


def set_connection_postgres(
    user: str,
    host: str,
    port: int,
    database: str,
    password: str | None = None,
) -> None:
    """Sets connection to a postgres connection.

    Args:
        user: Username for database.
        host: Host adress to database
        port: Port to database.
        database: Name of the database.
        password: Password for the database.
    """
    global _IS_POOLED

    user_enc = quote_plus(user)

    # Build engine URL
    if password:
        password_enc = quote_plus(password)
        engine_url = f"postgresql+psycopg2://{user_enc}:{password_enc}@{host}:{port!s}/{database}"
    else:
        engine_url = f"postgresql+psycopg2://{user_enc}@{host}:{port!s}/{database}"
    # Create engine
    engine = create_engine(engine_url)
    print(engine_url)

    set_connection(lambda: ibis.postgres.connect(engine), pooled_connection=True)


def set_connection_eimerdb(bucket_name: str, eimer_name: str) -> None:
    """Sets connection to an eimerdb connection.

    Args:
        bucket_name: Name of the bucket for your eimerdb database.
        eimer_name: Name of your eimerdb database.
    """
    set_connection(
        lambda: EimerDBInstance(
            bucket_name=bucket_name,
            eimer_name=eimer_name,
        ),
        pooled_connection=False,
    )


def set_connection(
    connection_factory: Callable[[], object], pooled_connection: bool
) -> None:
    """Sets up the primary method for how the app will connect to your data.

    This is intended for advanced users, for a more guided setup use one of the other 'set_connection_' methods for your specific data storage.

    Args:
        connection_factory: Factory method to create connection objects.
        pooled_connection: Decides if 'get_connection' returns different connection objects or reuses the same connection object.

    Raises:
        NotImplementedError: If connection_factory output object is not 'EimerDBInstance' or 'ibis' connection.
    """
    global _CONNECTION_FACTORY, _CONNECTION_INSTANCE, _IS_POOLED

    if pooled_connection:
        _IS_POOLED = True

    test_connection = connection_factory()

    if isinstance(test_connection, EimerDBInstance):
        logger.info("Registered 'EimerDBInstance' connection.")
    elif conn_is_ibis(test_connection):
        if hasattr(test_connection, "close"):
            test_connection.close()
        logger.info("Registered 'ibis.backend' connection.")
    else:
        raise NotImplementedError(
            "Only backends of type 'ibis' or 'eimerdb' is currently supported."
        )
    del test_connection

    _CONNECTION_INSTANCE = connection_factory() if not _IS_POOLED else None
    _CONNECTION_FACTORY = connection_factory


def get_connection() -> object:
    """Function for getting the connection using the function defined with 'set_connection'."""
    global _CONNECTION_FACTORY, _CONNECTION_INSTANCE, _IS_POOLED

    if _CONNECTION_FACTORY is None:
        raise ValueError("No connection factory defined. Call set_connection first.")

    if _IS_POOLED:
        return _CONNECTION_FACTORY()
    else:
        return _CONNECTION_INSTANCE
