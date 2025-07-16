from ssb_dash_framework import FreeSearch
from ssb_dash_framework import FreeSearchTab
from ssb_dash_framework import FreeSearchWindow

from ..conftest import DummyDatabase


def test_import_freesearch() -> None:
    assert FreeSearch is not None
    assert FreeSearchTab is not None
    assert FreeSearchWindow is not None


def test_instantiation() -> None:
    FreeSearchTab(database=DummyDatabase())
    FreeSearchWindow(database=DummyDatabase())
