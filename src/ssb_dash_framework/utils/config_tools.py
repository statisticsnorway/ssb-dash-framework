from collections.abc import Callable

from eimerdb import EimerDBInstance

from .core_query_functions import conn_is_ibis

_CONNECTION_METHOD: None | object = None


def set_connection(connection_method: Callable) -> None:
    """Function for setting the connection function to use in the framework app.

    Example:
        Using ibis postgres:
            import ibis
            set_connection(
                lambda: ibis.postgres.connect(
                    host="localhost",
                    port=5432,
                    user="strukt-naering-developers@dapla-group-sa-p-ye.iam",
                    password="",  # or provide password if needed
                    database="strukt-naering",
                )
            )

        Using eimerdb:
            import eimerdb as db
            set_connection(
                lambda: db.EimerDBInstance(
                    bucket_name = "my-bucket",
                    eimer_name = "my_eimerdb"
                )
            )
    """
    test_connection = connection_method()
    if isinstance(test_connection, EimerDBInstance) or conn_is_ibis(test_connection):
        globals()["_CONNECTION_METHOD"] = connection_method
    else:
        raise NotImplementedError(
            "Only backends of type 'ibis' or 'eimerdb' is currently supported."
        )


def get_connection() -> object:
    """Function for getting the connection using the function defined with 'set_connection'."""
    connection_object = globals()["_CONNECTION_METHOD"]()
    if not connection_object:
        raise ValueError(
            "No connection method defined, use 'set_connection()' to set a method for connecting to data."
        )
    return connection_object
