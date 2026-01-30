from ssb_dash_framework import FreeSearch
from ssb_dash_framework import FreeSearchTab
from ssb_dash_framework import FreeSearchWindow


def test_import_freesearch() -> None:
    assert FreeSearch is not None, "FreeSearch is not importable"
    assert FreeSearchTab is not None, "FreeSearchTab is not importable"
    assert FreeSearchWindow is not None, "FreeSearchWindow is not importable"


def test_instantiation(ibis_polars_conn) -> None:
    FreeSearchTab()
    FreeSearchWindow()
    FreeSearchTab(conn=ibis_polars_conn)
    FreeSearchWindow(conn=ibis_polars_conn)
