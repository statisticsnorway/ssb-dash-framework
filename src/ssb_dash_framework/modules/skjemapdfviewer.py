import base64
import logging

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate
import gcsfs

from ..utils.base_classes import ModuleBase
from ..setup.variableselector import VariableSelector

logger = logging.getLogger(__name__)

class SkjemapdfViewer(ModuleBase):
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
        self.pdf_folder_path = pdf_folder_path

        self.is_valid(form_identifier)

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

    def layout(self) -> html.Div:
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


    def module_callbacks(self) -> None:
        """Register Dash callbacks for the SkjemapdfViewer module.

        Notes:
            - The first callback updates the form identifier input field.
            - The second callback fetches and encodes the PDF file as a data URI for display in the iframe.
        """

        @callback(  # type: ignore[misc]
            Output("skjemapdf-input", "value"),
            VariableSelector.get_refnr(Input),
        )
        def update_form(refnr: str) -> str:
            """Update the form identifier input field.

            Args:
                orgnr: The selected organization number.

            Returns:
                str: The updated organization number value.
            """
            logger.debug("Args:\n" + f"refnr: {refnr}")
            return refnr

        @callback(  # type: ignore[misc]
            Output("skjemapdf-iframe1", "src"),
            VariableSelector.get_refnr(Input),
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
                fs = gcsfs.GCSFileSystem()
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


