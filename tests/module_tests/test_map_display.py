from ssb_dash_framework import MapDisplay
from ssb_dash_framework import MapDisplayTab
from ssb_dash_framework import MapDisplayWindow


def test_import() -> None:
    assert MapDisplay is not None
    assert MapDisplayTab is not None
    assert MapDisplayWindow is not None
