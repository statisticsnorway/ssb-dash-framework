from collections.abc import Generator
from typing import Any

import pytest

from ssb_dash_framework.setup.variableselector import VariableSelector


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


class DummyDatabase:
    """Dummy class for mocking a database connection during initialization."""

    def __init__(self) -> None:
        """Initializes the dummy class."""
        self.tables: dict[str, Any] = {}

    def query(self, *args: Any, **kwargs: Any) -> Any:
        return []

    def query_changes(self, *args: Any, **kwargs: Any) -> Any:
        return []
