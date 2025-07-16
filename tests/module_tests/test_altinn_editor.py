from typing import Any

from ssb_dash_framework import AltinnSkjemadataEditor
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert AltinnSkjemadataEditor is not None


class DummyDatabase:

    def __init__(self) -> None:
        """Initializes the dummy class."""
        self.tables: dict[str, Any] = {}

    def query(self, *args: Any, **kwargs: Any) -> Any:
        return []

    def query_changes(self, *args: Any, **kwargs: Any) -> Any:
        return []


def test_instantiation() -> None:
    set_variables(["year", "quarter", "skjemaversjon"])
    AltinnSkjemadataEditor(
        time_units=["year", "quarter"], conn=DummyDatabase(), variable_connection={}
    )
