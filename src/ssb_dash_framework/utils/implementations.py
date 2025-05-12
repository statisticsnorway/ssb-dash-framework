import logging
from abc import ABC

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


class WindowImplementation(ABC):

    _window_number = (
        0  # Used to differentiate ids used in callbacks to open/close modal.
    )

    def __init__(
        self,
    ):
        print("Hello from the WindowImplementation")
        self._window_n = WindowImplementation._window_number
        print(WindowImplementation._window_number)
        self.title = self.label
        self.module_name = self.module_name
        print(WindowImplementation._window_number)

        self.window_callbacks()
        print(WindowImplementation._window_number)

        WindowImplementation._window_number += 1
        print(WindowImplementation._window_number)

    def layout(self):
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(self.label)),
                        dbc.ModalBody(self.module_layout),
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
