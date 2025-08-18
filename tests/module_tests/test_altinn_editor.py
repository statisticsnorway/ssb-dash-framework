from ssb_dash_framework import AltinnSkjemadataEditor
from ssb_dash_framework import set_variables

from ..conftest import DummyDatabase


def test_import() -> None:
    assert AltinnSkjemadataEditor is not None


def test_instantiation() -> None:
    set_variables(["year", "quarter", "refnr"])
    AltinnSkjemadataEditor(
        time_units=["year", "quarter"], conn=DummyDatabase(), variable_connection={}
    )
