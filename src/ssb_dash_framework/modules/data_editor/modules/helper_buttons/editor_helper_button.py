# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
from logging import getLogger

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate

from ...meta import ContextABC

logger = getLogger(__name__)


class DataEditorHelperButton(ContextABC):
    """Base class for defining a helper button component."""

    modal_body: html.Div
    _id_number = 0

    def __init__(self, label: str) -> None:
        """Core functionality to register the component and make the button functional.

        After being initialized it registers itself to DataEditorRegistry.

        Args:
            label: The label to put on the button.
        """
        self.module_name = self.__class__.__name__
        self.module_number = DataEditorHelperButton._id_number
        DataEditorHelperButton._id_number += 1

        self.label = label
        self.button_callbacks()

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        if not hasattr(self, "modal_body"):
            raise AttributeError("Lacking 'modal_body' attribute.")
        return html.Div(
            [
                html.Div(
                    [
                        dbc.Button(
                            self.label,
                            id=f"{self.module_name}-{self.module_number}-button",
                            className="ssb-btn primary-btn",
                        ),
                        html.Span(
                            id=f"{self.module_name}-{self.module_number}-indicator",
                            className="helper-button-indicator",
                            children="",
                            style={"display": "none"},
                        ),
                    ],
                    style={"position": "relative", "display": "inline-block"},
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(self.label)),
                        dbc.ModalBody(self.modal_body),
                    ],
                    id=f"{self.module_name}-{self.module_number}-modal",
                    is_open=False,
                    className=f"{self.module_name}-helper-modal",
                ),
            ]
        )

    def button_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor Support Tables module."""

        @callback(
            Output(f"{self.module_name}-{self.module_number}-modal", "is_open"),
            Input(f"{self.module_name}-{self.module_number}-button", "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-modal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False
