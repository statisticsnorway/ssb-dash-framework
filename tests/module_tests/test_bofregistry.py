from unittest.mock import patch

from ssb_dash_framework import BofInformation
from ssb_dash_framework import BofInformationTab
from ssb_dash_framework import BofInformationWindow
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert BofInformation is not None
    assert BofInformationTab is not None
    assert BofInformationWindow is not None


def test_base_class() -> None:
    set_variables(["foretak"])
    with patch.object(
        BofInformation, "_check_connection", lambda self: None
    ):  # This replaces the _check_connection method in the base class

        class test_implementation(BofInformation):
            def __init__(self) -> None:
                super().__init__()

            def layout(self):
                pass

        test_implementation()


def test_tab():
    set_variables(["foretak"])
    with patch.object(
        BofInformation, "_check_connection", lambda self: None
    ):  # This replaces the _check_connection method in the base class
        BofInformationTab()


def test_window():
    set_variables(["foretak"])
    with patch.object(
        BofInformation, "_check_connection", lambda self: None
    ):  # This replaces the _check_connection method in the base class
        BofInformationWindow()
