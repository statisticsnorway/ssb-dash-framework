from dash import html

from ssb_dash_framework import module_validator


def test_validation() -> None:
    class test_module:
        _id_number = 0

        def __init__(self) -> None:
            self.module_number = test_module._id_number
            self.module_name = "Test"
            self.module_layout = html.Div()
            self.label = "Label"
            self.module_callbacks()
            module_validator(self)

        def layout(self) -> None:
            pass

        def module_callbacks(self) -> None:
            pass

    test_module()
