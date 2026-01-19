from collections.abc import Callable
from typing import Any

import ibis
from eimerdb import EimerDBInstance

from .core_query_functions import conn_is_ibis

_CONNECTION_METHOD = None


def create_connection(backend, **kwargs: Any):
    if backend == "ibis":
        set_connection(lambda: ibis.connect(**kwargs))
    elif backend == "eimerdb":
        bucket_name: str = kwargs.get("bucket_name", None)
        if bucket_name is None:
            raise ValueError(
                "When using eimerdb it requires the 'bucket_name' keyword argument."
            )
        eimer_name: str = kwargs.get("eimer_name", None)
        if eimer_name is None:
            raise ValueError(
                "When using eimerdb it requires the 'eimer_name' keyword argument."
            )
        set_connection(
            lambda: EimerDBInstance(
                bucket_name=bucket_name,
                eimer_name=eimer_name,
            )
        )
    else:
        raise NotImplementedError(
            f"Connection of type '{backend}' is not implemented. Use either 'ibis' or 'eimerdb'."
        )


def set_connection(connection_method: Callable):
    test_connection = connection_method()
    if isinstance(test_connection, EimerDBInstance) or conn_is_ibis(test_connection):
        globals()["_CONNECTION_METHOD"] = connection_method
    else:
        raise NotImplementedError(
            "Only backends of type 'ibis' or 'eimerdb' is currently supported."
        )


def get_connection():
    return globals()["_CONNECTION_METHOD"]()
