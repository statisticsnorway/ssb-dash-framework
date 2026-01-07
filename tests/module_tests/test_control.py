from ssb_dash_framework import AltinnControlViewTab
from ssb_dash_framework import AltinnControlViewWindow
from ssb_dash_framework import ControlView
from ssb_dash_framework import ControlViewTab
from ssb_dash_framework import ControlViewWindow


def test_import() -> None:
    assert ControlView is not None
    assert ControlViewTab is not None
    assert ControlViewWindow is not None
    assert AltinnControlViewTab is not None
    assert AltinnControlViewWindow is not None
