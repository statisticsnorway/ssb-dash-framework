import logging

from dash import html

from ..modules.skjemapdfviewer import SkjemapdfViewer
from ..utils import TabImplementation

logger = logging.getLogger(__name__)


class SkjemapdfViewerTab(TabImplementation, SkjemapdfViewer):
    """SkjemapdfViewerTab is an implementation of the SkjemapdfViewer module as a tab in a Dash application."""

    def __init__(
        self, pdf_folder_path: str, form_identifier: str = "skjemaversjon"
    ) -> None:
        """Initializes the SkjemapdfViewerTab class.

        Args:
            pdf_folder_path (str): The path to the folder containing PDF files.
            form_identifier (str): The identifier for the form. This should be the VariableSelector value that matches the PDF file name.
                Defaults to "skjemaversjon".
        """
        SkjemapdfViewer.__init__(form_identifier, pdf_folder_path)
        TabImplementation.__init__(self)
