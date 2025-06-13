import logging
from typing import Protocol

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


class TabModule(Protocol):
    """A protocol that defines the expected interface for a module to be used in a tab.

    Attributes:
        label (str): The label for the tab.
        module_name (str): The name of the module, used for generating unique IDs.
        module_layout (html.Div): The layout to display inside the tab.

    Methods:
        layout() -> dbc.Tab: Returns the layout of the module inside a tab.
    """

    label: str
    module_name: str
    module_layout: html.Div

    def layout(self) -> dbc.Tab:
        """This method should return the layout of the module inside a tab."""
        ...


class TabImplementation:
    """A mixin class to implement a module inside a tab.

    Dependencies:
        - self.label (str): The label for the tab.
        - self.module_name (str): The name of the module, used for generating unique IDs.
        - self.module_layout (html.Div): The layout to display inside the tab.

    Note:
        - This class should be used as a mixin in a module class.
        - If necessary, you can override the `get_module_layout` method to further customize the layout inside the tab.
    """

    # Attributes that must be defined in the class using this mixin
    label: str
    module_name: str
    module_layout: html.Div

    def __init__(self) -> None:
        """Initialize the tab implementation.

        This class is used to create a tab to put in the tab_list.
        """
        if not hasattr(self, "label"):
            raise AttributeError(
                "The class must have a 'label' attribute to use TabImplementation."
            )
        if not hasattr(self, "module_name"):
            raise AttributeError(
                "The class must have a 'module_name' attribute to use TabImplementation."
            )

    def layout(self) -> dbc.Tab:
        """Generate the layout for the module as a tab.

        Returns:
            html.Div: The layout containing the module layout.
        """
        layout = dbc.Tab(
            html.Div(
                style={"height": "94vh", "width": "100%", "display": "flex"},
                children=self.get_module_layout(),
            ),
            label=self.label,
        )
        logger.debug("Generated layout")
        return layout

    def get_module_layout(self) -> html.Div:
        """Get the layout of the module.

        Works as is, but can be overridden if needed.
        """
        if not hasattr(self, "module_layout"):
            raise AttributeError(
                "The class using WindowImplementation must define 'module_layout'."
            )
        return self.module_layout


class WindowModule(Protocol):
    """A protocol that defines the expected interface for a module to be used in a window.

    Attributes:
        label (str): The label for the window.
        module_name (str): The name of the module, used for generating unique IDs.
        module_layout (html.Div): The layout to display inside the window.

    Methods:
        layout() -> html.Div: Returns the layout of the module inside a window.
    """

    label: str
    module_name: str
    module_layout: html.Div

    def layout(self) -> html.Div:
        """This method should return the layout of the module inside a window."""
        ...


class WindowImplementation:
    """A mixin class to implement a module inside a modal.

    Dependencies:
        - self.label (str): The label for the modal and sidebar button.
        - self.module_name (str): The name of the module, used for generating unique IDs.
        - self.module_layout (html.Div): The layout to display inside the modal.

    Note:
        - This class should be used as a mixin in a module class.
        - If necessary, you can override the `get_module_layout` method to further customize the layout inside the modal.
    """

    _window_number = (
        0  # Used to differentiate ids used in callbacks to open/close modal.
    )

    # Attributes that must be defined in the class using this mixin
    label: str
    module_name: str
    module_layout: html.Div

    def __init__(
        self,
    ) -> None:
        """Initialize the window implementation.

        This class is used to create a modal window for the module.
        """
        if not hasattr(self, "label"):
            raise AttributeError(
                "The class must have a 'label' attribute to use WindowImplementation."
            )
        if not hasattr(self, "module_name"):
            raise AttributeError(
                "The class must have a 'module_name' attribute to use WindowImplementation."
            )

        self._window_n = WindowImplementation._window_number
        self.window_callbacks()
        WindowImplementation._window_number += 1

    def layout(self) -> html.Div:
        """Generate the layout for the modal window.

        This method creates a modal window with a header and a body containing the module layout.
        It also creates a sidebar button to toggle the modal.

        Returns:
            html.Div: The layout containing the modal and the sidebar button.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                dbc.Row(
                                    [
                                        dbc.Col(self.label),
                                        dbc.Col(
                                            dbc.Button(
                                                "Fullscreen visning",
                                                id=f"{self._window_n}-{self.module_name}-modal-fullscreen",
                                            ),
                                        ),
                                    ],
                                    align="center",
                                    justify="between",
                                    className="w-100",
                                )
                            )
                        ),
                        dbc.ModalBody(
                            html.Div(
                                children=self.get_module_layout(),
                                style = {"heigth":"100vh",}
                            )
                        ),
                    ],
                    id=f"{self._window_n}-{self.module_name}-modal",
                    size="xl",
                    fullscreen="xxl-down",
                    style={
                        "width": "100%",
                        "display":"flex"
                    }
                ),
                sidebar_button(
                    "🔍",
                    f"{self.label}",
                    f"sidebar-{self._window_n}-{self.module_name}-modal-button",
                ),
            ]
        )
        logger.debug("Generated layout")
        return layout

    def get_module_layout(self) -> html.Div:
        """Get the layout of the module.

        Works as is, but can be overridden if needed.
        """
        if not hasattr(self, "module_layout"):
            raise AttributeError(
                "The class using WindowImplementation must define 'module_layout'."
            )
        return self.module_layout

    def window_callbacks(self) -> None:
        """Define the callbacks for the module window.

        This includes a callback to toggle the visibility of the modal window.
        """

        @callback(
            Output(f"{self._window_n}-{self.module_name}-modal", "is_open"),
            Input(
                f"sidebar-{self._window_n}-{self.module_name}-modal-button", "n_clicks"
            ),
            State(f"{self._window_n}-{self.module_name}-modal", "is_open"),
        )
        def _modal_toggle(n: int, is_open: bool) -> bool:
            """Toggle the state of the modal window.

            Args:
                n (int): Number of clicks on the toggle button.
                is_open (bool): Current state of the modal (open/closed).

            Returns:
                bool: The new state of the modal (open/closed).
            """
            logger.info("Toggle modal")
            if n:
                return not is_open
            return is_open

        @callback(
            Output(f"{self._window_n}-{self.module_name}-modal", "fullscreen"),
            Input(f"{self._window_n}-{self.module_name}-modal-fullscreen", "n_clicks"),
            State(f"{self._window_n}-{self.module_name}-modal", "fullscreen"),
        )
        def toggle_fullscreen_modal(
            n_clicks: int, fullscreen_state: str | bool
        ) -> str | bool:
            if n_clicks > 0:
                if fullscreen_state is True:
                    fullscreen = "xxl-down"
                else:
                    fullscreen = True
                return fullscreen
