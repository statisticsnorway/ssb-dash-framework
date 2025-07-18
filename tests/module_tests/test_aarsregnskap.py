from ssb_dash_framework import Aarsregnskap
from ssb_dash_framework import AarsregnskapTab
from ssb_dash_framework import AarsregnskapWindow


def test_import() -> None:
    assert Aarsregnskap is not None
    assert AarsregnskapTab is not None
    assert AarsregnskapWindow is not None
