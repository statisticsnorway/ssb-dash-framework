import logging

from dash import html

from ..modules.skjemapdfviewer import SkjemapdfViewer

logger = logging.getLogger(__name__)


class SkjemapdfViewerTab(SkjemapdfViewer):
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
        super().__init__(form_identifier, pdf_folder_path)

    def layout(self) -> html.Div:
        """Generates the layout for the SkjemapdfViewer module as a tab.

        Returns:
            html.Div: The layout of the SkjemapdfViewer tab.
        """
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
