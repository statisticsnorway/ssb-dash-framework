from abc import ABC
from abc import abstractmethod

import dash_bootstrap_components as dbc
from dash import html

from ssb_dash_framework import TabImplementation
from ssb_dash_framework import WindowImplementation


def test_tab_implementation():
    class test_module(ABC):
        _id_number = 0

        def __init__(self) -> None:
            self.module_number = test_module._id_number
            self.module_name = "Test"
            self.module_layout = html.Div()
            self.label = "Label"
            self.module_callbacks()

        @abstractmethod
        def layout(self):
            pass

        def module_callbacks(self):
            return ""

    class test_module_tab(TabImplementation, test_module):
        def __init__(self) -> None:
            """Initializes the AarsregnskapTab class."""
            test_module.__init__(self)
            TabImplementation.__init__(self)

    instanced_tab_module = test_module_tab()
    if not isinstance(instanced_tab_module.layout(), dbc.Tab):
        raise TypeError(
            f"Layout returned from tab implementation should be type 'dbc.Tab'. Returned: {type(instanced_tab_module.layout())}"
        )


def test_window_implementation():
    class test_module(ABC):
        _id_number = 0

        def __init__(self) -> None:
            self.module_number = test_module._id_number
            self.module_name = "Test"
            self.module_layout = html.Div()
            self.label = "Label"
            self.module_callbacks()

        @abstractmethod
        def layout(self):
            pass

        def module_callbacks(self):
            return ""

    class test_module_window(WindowImplementation, test_module):
        def __init__(self) -> None:
            """Initializes the AarsregnskapTab class."""
            test_module.__init__(self)
            WindowImplementation.__init__(self)

    instanced_window_module = test_module_window()
    if not isinstance(instanced_window_module.layout(), html.Div):
        raise TypeError(
            f"Layout returned from tab implementation should be type 'html.Div'. Returned: {type(instanced_window_module.layout())}"
        )
    if not hasattr(instanced_window_module, "_window_n"):
        raise AttributeError("Missing attribute '_window_n'")
    if not hasattr(instanced_window_module, "icon"):
        raise AttributeError("Missing attribute 'icon'")
