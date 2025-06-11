import logging

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from ..modules.skjemapdfviewer import SkjemapdfViewer
from ..utils import WindowImplementation

logger = logging.getLogger(__name__)


class SkjemapdfViewerWindow(WindowImplementation, SkjemapdfViewer):
    """Implementation of the SkjemapdfViewer as a window."""

    def __init__(
        self, pdf_folder_path: str, form_identifier: str = "skjemaversjon"
    ) -> None:
        """Initialize the SkjemapdfViewerWindow class.

        This class is a subclass of SkjemapdfViewer and is used to create a window for viewing PDF files.

        Args:
            pdf_folder_path (str): The path to the folder containing PDF files.
            form_identifier (str): The identifier for the form. Defaults to "skjemaversjon".
        """
        SkjemapdfViewer.__init__(form_identifier, pdf_folder_path)
        WindowImplementation.__init__(
            self,
        )


