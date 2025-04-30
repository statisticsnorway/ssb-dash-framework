import logging

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from ..modules.skjemapdfviewer import SkjemapdfViewer
from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


class SkjemapdfViewerWindow(SkjemapdfViewer):
    def __init__(self, pdf_folder_path, form_identifier="skjemaversjon"):
        """Initialize the FreeSearchWindow class.

        Args:
            database: The database connection or object used for querying.
        """
        super().__init__(form_identifier, pdf_folder_path)
        self.callbacks()

    def layout(self) -> html.Div:
        """Generate the layout for the FreeSearch window.

        Returns:
            html.Div: A Div element containing:
                - A modal with a title and body for the FreeSearch module layout.
                - A sidebar button to toggle the modal.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Skjema PDF viewer")),
                        dbc.ModalBody(self.module_layout),
                    ],
                    id="skjemapdf-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("🔍", "skjemapdf", "sidebar-skjemapdf-button"),
            ]
        )
        logger.debug("Generated layout")
        return layout

    def callbacks(self):
        """Define the callbacks for the FreeSearch window.

        This includes a callback to toggle the visibility of the modal window.
        """

        @callback(  # type: ignore[misc]
            Output("skjemapdf-modal", "is_open"),
            Input("sidebar-skjemapdf-button", "n_clicks"),
            State("skjemapdf-modal", "is_open"),
        )
        def freesearch_modal_toggle(n: int, is_open: bool) -> bool:
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
