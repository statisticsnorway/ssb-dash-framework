from unittest.mock import patch

from ssb_dash_framework import BofInformation
from ssb_dash_framework import VariableSelectorOption


def test_import() -> None:
    assert BofInformation is not None

def test_base_class() -> None:
    from dash import html

    VariableSelectorOption("foretak")
    with patch.object(
        BofInformation, "_check_connection", lambda self: None
    ):  # This replaces the _check_connection method in the base class

        class test_implementation(BofInformation):
            def __init__(self) -> None:
                super().__init__()

            def layout(self) -> html.Div:
                return self.module_layout

        test_implementation()


