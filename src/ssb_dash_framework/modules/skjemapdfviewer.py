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

logger = logging.getLogger(__name__)


class SkjemapdfViewer(ABC):
    """Module for displaying PDF forms in a tab.

    Attributes:
        label (str): Label for the tab, displayed as "🗎 Skjema".
        pdf_folder_path (str): Path to the folder containing the PDF files.
    """

    def __init__(
        self,
        form_identifier: str,
        pdf_folder_path: str,
    ) -> None:
        """Initialize the SkjemapdfViewer module.

        Args:
            form_identifier (str): The identifier for the form. This should match the VariableSelector value.
            pdf_folder_path (str): The path to the folder containing the PDF files.
        """
        self.label = "🗎 Skjema"
        self.variableselector = VariableSelector([form_identifier], [])
        self.pdf_folder_path = pdf_folder_path
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self.is_valid(form_identifier)

    def is_valid(self, form_identifier: str) -> None:
        """Validate the form identifier and PDF folder path.

        Args:
            form_identifier (str): The identifier for the form.

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
            style={"height": "100%", "display": "flex", "flexDirection": "column"},
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
                            id="skjemapdf-iframe1",
                            style={"width": "100%", "height": "80vh"},
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
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("skjemapdf-input", "value"),
            *dynamic_states,
        )
        def update_form(orgnr: str) -> str:
            """Update the form identifier input field.

            Args:
                orgnr (str): The selected organization number.

            Returns:
                str: The updated organization number value.
            """
            return orgnr

        @callback(  # type: ignore[misc]
            Output("skjemapdf-iframe1", "src"),
            *dynamic_states,
        )
        def update_pdfskjema_source(form_identifier: str) -> str | None:
            """Fetch and encode the PDF source based on the form identifier.

            Args:
                form_identifier (str): The form identifier input value.

            Returns:
                str | None: A data URI for the PDF file, encoded in base64, or None if the file is not found.

            Raises:
                PreventUpdate: If the form identifier is not provided.
            """
            if not form_identifier:
                raise PreventUpdate
            try:
                print(f"{self.pdf_folder_path}/{form_identifier}.pdf")
                fs = FileClient.get_gcs_file_system()
                with fs.open(
                    f"{self.pdf_folder_path}/{form_identifier}.pdf",
                    "rb",
                ) as f:
                    pdf_bytes = f.read()

                pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
                pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
            except FileNotFoundError:
                return None
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
            return pdf_data_uri

        logger.debug("Generated callbacks")
