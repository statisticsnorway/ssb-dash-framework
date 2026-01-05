import base64
import logging
from abc import ABC
from abc import abstractmethod

import dash_bootstrap_components as dbc
from dapla import FileClient
from dash import callback
from dash import html
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class SkjemapdfViewer(ABC):
    """Module for displaying PDF forms in a tab."""

    def __init__(
        self,
        form_identifier: str,
        pdf_folder_path: str,
    ) -> None:
        """Initialize the SkjemapdfViewer module.

        Args:
            form_identifier: The identifier for the form. This should match the VariableSelector value.
            pdf_folder_path: The path to the folder containing the PDF files.
        """
        self.label = "🗎 Skjema"
        self.variableselector = VariableSelector([form_identifier], [])
        self.pdf_folder_path = pdf_folder_path
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self.is_valid(form_identifier)
        module_validator(self)

    def is_valid(self, form_identifier: str) -> None:
        """Validate the form identifier and PDF folder path.

        Args:
            form_identifier: The identifier for the form.

        Raises:
            ValueError: If the form identifier is not found in the VariableSelector.
        """
        if f"var-{form_identifier}" not in [
            x.id for x in VariableSelector._variableselectoroptions
        ]:
            raise ValueError(
                f"var-{form_identifier} not found in the VariableSelector. Please add it using '''VariableSelectorOption('{form_identifier}')'''"
            )
        if self.pdf_folder_path.endswith("/"):
            self.pdf_folder_path = self.pdf_folder_path[:-1]

    def _create_layout(self) -> html.Div:
        """Generate the layout for the SkjemapdfViewer module.

        Returns:
            html.Div: A Div element containing input fields for the form identifier
                      and an iframe to display the PDF content.
        """
        layout = html.Div(
            className="skjemapdfviewer",
            children=[
                dbc.Container(
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Label("Skjema-id"),
                                            dbc.Input("skjemapdf-input"),
                                        ]
                                    )
                                ),
                            ]
                        ),
                        html.Iframe(
                            className="skjemapdf-pdf-iframe",
                            id="skjemapdf-iframe1",
                        ),
                    ],
                    fluid=True,
                ),
            ],
        )
        logger.debug("Generated layout")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the FreeSearch module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Register Dash callbacks for the SkjemapdfViewer module.

        Notes:
            - The first callback updates the form identifier input field.
            - The second callback fetches and encodes the PDF file as a data URI for display in the iframe.
        """
        dynamic_states = [
            self.variableselector.get_all_inputs(),
            self.variableselector.get_all_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("skjemapdf-input", "value"),
            *dynamic_states,
        )
        def update_form(orgnr: str) -> str:
            """Update the form identifier input field.

            Args:
                orgnr: The selected organization number.

            Returns:
                str: The updated organization number value.
            """
            logger.debug("Args:\n" + f"orgnr: {orgnr}")
            return orgnr

        @callback(  # type: ignore[misc]
            Output("skjemapdf-iframe1", "src"),
            *dynamic_states,
        )
        def update_pdfskjema_source(form_identifier: str) -> str | None:
            """Fetch and encode the PDF source based on the form identifier.

            Args:
                form_identifier: The form identifier input value.

            Returns:
                str | None: A data URI for the PDF file, encoded in base64, or None if the file is not found.

            Raises:
                PreventUpdate: If the form identifier is not provided.
            """
            logger.debug("Args:\n" + f"form_identifier: {form_identifier}")
            if not form_identifier:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            path_to_file = f"{self.pdf_folder_path}/{form_identifier}.pdf"
            logger.debug(f"Trying to open file: {path_to_file}")
            try:
                fs = FileClient.get_gcs_file_system()
                with fs.open(
                    f"{self.pdf_folder_path}/{form_identifier}.pdf",
                    "rb",
                ) as f:
                    pdf_bytes = f.read()

                pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
                pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
            except FileNotFoundError:
                logger.debug(f"Returning None. Could not open file: {path_to_file}")
                return None
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
            return pdf_data_uri

        logger.debug("Generated callbacks")


class SkjemapdfViewerTab(TabImplementation, SkjemapdfViewer):
    """SkjemapdfViewerTab is an implementation of the SkjemapdfViewer module as a tab in a Dash application."""

    def __init__(self, pdf_folder_path: str, form_identifier: str = "refnr") -> None:
        """Initializes the SkjemapdfViewerTab class.

        Args:
            pdf_folder_path: The path to the folder containing PDF files.
            form_identifier: The identifier for the form. This should be the VariableSelector value that matches the PDF file name.
                Defaults to "refnr".
        """
        SkjemapdfViewer.__init__(self, form_identifier, pdf_folder_path)
        TabImplementation.__init__(self)


class SkjemapdfViewerWindow(WindowImplementation, SkjemapdfViewer):
    """Implementation of the SkjemapdfViewer as a window."""

    def __init__(self, pdf_folder_path: str, form_identifier: str = "refnr") -> None:
        """Initialize the SkjemapdfViewerWindow class.

        This class is a subclass of SkjemapdfViewer and is used to create a window for viewing PDF files.

        Args:
            pdf_folder_path: The path to the folder containing PDF files.
            form_identifier: The identifier for the form. Defaults to "refnr".
        """
        SkjemapdfViewer.__init__(self, form_identifier, pdf_folder_path)
        WindowImplementation.__init__(
            self,
        )
