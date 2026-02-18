from collections.abc import Generator

import ibis
import pytest

from ssb_dash_framework import VariableSelector
from ssb_dash_framework import set_connection


@pytest.fixture(autouse=True)
def clear_VariableSelector_variableselectoroptions() -> Generator[None, None, None]:
    """Automatically clears the VariableSelector registry before each test.

    This ensures that each test starts with an empty codelist (so VariableSelector
    sees no codes unless the test explicitly creates some). After yielding to
    the test, it clears the registry again.

    Yields:
        None: Control is yielded to the test, after which the registry is cleared.
    """
    VariableSelector._variableselectoroptions.clear()
    yield
    VariableSelector._variableselectoroptions.clear()


@pytest.fixture(autouse=True, scope="session")
def ibis_polars_conn():
    print("Setting up connection...")
    # Example: create a DB connection, API client, etc.
    ibis_polars_conn = ibis.polars.connect()
    yield ibis_polars_conn


@pytest.fixture(autouse=True, scope="session")
def set_connection_testing():
    print("Setting up connection...")
    # Example: create a DB connection, API client, etc.
    set_connection(lambda: ibis.polars.connect(), pooled_connection=False)
