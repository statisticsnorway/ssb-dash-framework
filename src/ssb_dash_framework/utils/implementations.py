import logging

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


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
                        dbc.ModalHeader(dbc.ModalTitle(self.label)),
                        dbc.ModalBody(self.get_module_layout()),
                    ],
                    id=f"{self._window_n}-{self.module_name}-modal",
                    size="xl",
                    fullscreen="xxl-down",
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

        @callback(  # type: ignore[misc]
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
