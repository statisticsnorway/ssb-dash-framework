import base64
import logging
from abc import ABC

import dash_bootstrap_components as dbc
from dapla import FileClient
from dash import callback
from dash import html
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector

logger = logging.getLogger(__name__)


class SkjemapdfViewer(ABC):
    """Tab for displaying annual financial statements (Årsregnskap).

    Attributes:
        label (str): Label for the tab, displayed as "🧾 Årsregnskap".
    """

    def __init__(
        self,
        form_identifier,
        pdf_folder_path,
    ) -> None:
        """Initialize the skjemapdf component."""
        self.label = "🗎 Skjema"
        self.variableselector = VariableSelector([form_identifier], [])
        self.pdf_folder_path = pdf_folder_path
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def is_valid(self):
        if f"var-{form_identifier}" not in [
            x.id for x in VariableSelector._variableselectoroptions
        ]:
            raise ValueError(
                f"var-{form_identifier} not found in the VariableSelector. Please add it using '''VariableSelectorOption('{form_identifier}')'''"
            )
        if self.pdf_folder_path.endswith("/"):
            self.pdf_folder_path = self.pdf_folder_path[:-1]

    def _create_layout(self) -> html.Div:
        """Generate the layout for the Årsregnskap tab.

        Returns:
            html.Div: A Div element containing input fields for year and organization number
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

    def module_callbacks(self) -> None:
        """Register Dash callbacks for the skjema pdf tab."""
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("skjemapdf-input", "value"),
            *dynamic_states,
        )
        def update_form(orgnr: str) -> str:
            """Update the organization number input field.

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
            """Fetch and encode the PDF source based on the year and organization number.

            Args:
                form_identifier (str): The form identification input value.

            Returns:
                str: A data URI for the PDF file, encoded in base64.

            Raises:
                PreventUpdate: If the year or organization number is not provided.
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
