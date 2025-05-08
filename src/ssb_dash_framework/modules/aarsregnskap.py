import base64
import logging
from abc import ABC
from abc import abstractmethod

import dash_bootstrap_components as dbc
from dapla import FileClient
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector

logger = logging.getLogger(__name__)


class Aarsregnskap(ABC):
    """Module for displaying annual financial statements (Årsregnskap).

    Attributes:
        label (str): Label for the module when initialized, displayed as "🧾 Årsregnskap".
    """

    def __init__(
        self,
    ) -> None:
        """Initialize the Aarsregnskap component.

        Sets up the label, validates required variables, and initializes the
        layout and callbacks for the module.
        """
        self.label = "🧾 Årsregnskap"
        self._is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _is_valid(self):
        """Validates the presence of required variables in VariableSelector.

        Raises:
            ValueError: If required variables ('var-aar' or 'var-foretak') are
                not found in the VariableSelector.
        """
        if "var-aar" not in [x.id for x in VariableSelector._variableselectoroptions]:
            raise ValueError(
                "var-aar not found in the VariableSelector. Please add it using '''VariableSelectorOption('aar')'''"
            )
        if "var-foretak" not in [
            x.id for x in VariableSelector._variableselectoroptions
        ]:
            raise ValueError(
                "var-foretak not found in the VariableSelector. Please add it using '''VariableSelectorOption('foretak')'''"
            )

    def _create_layout(self) -> html.Div:
        """Generates the layout for the Årsregnskap module.

        Returns:
            html.Div: A Div element containing input fields for year and
            organization number, and an iframe to display the PDF content.
        """
        layout = html.Div(
            style={"height": "94vh", "display": "flex", "flexDirection": "column"},
            children=[
                dbc.Container(
                    fluid=True,
                    style={"display": "flex", "flexDirection": "column", "flex": "1"},
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Label("År"),
                                            dbc.Input(
                                                id="tab-aarsregnskap-input1",
                                                type="number",
                                            ),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Label("Orgnr"),
                                            dbc.Input(id="tab-aarsregnskap-input2"),
                                        ]
                                    )
                                ),
                            ],
                            style={"flex": "0 0 auto"},
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.Iframe(
                                    id="tab-aarsregnskap-iframe1",
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "border": "none",
                                    },
                                ),
                                style={"flex": "1", "minHeight": 0},
                            ),
                            style={"flex": "1", "overflow": "hidden"},
                        ),
                    ],
                ),
            ],
        )
        logger.debug("Generated layout")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the Aarsregnskap module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Registers Dash callbacks for the Årsregnskap module."""

        @callback(  # type: ignore[misc]
            Output("tab-aarsregnskap-input1", "value"),
            Input("var-aar", "value"),
        )
        def update_aar(aar: int) -> int:
            """Update the year input field based on the selected year.

            Args:
                aar (int): The selected year.

            Returns:
                int: The updated year value.
            """
            return aar

        @callback(  # type: ignore[misc]
            Output("tab-aarsregnskap-input2", "value"),
            Input("var-foretak", "value"),
        )
        def update_orgnr(orgnr: str) -> str:
            """Update the organization number input field.

            Args:
                orgnr (str): The selected organization number.

            Returns:
                str: The updated organization number value.
            """
            return orgnr

        @callback(  # type: ignore[misc]
            Output("tab-aarsregnskap-iframe1", "src"),
            Input("tab-aarsregnskap-input1", "value"),
            Input("tab-aarsregnskap-input2", "value"),
        )
        def update_pdf_source(aar: int, orgnr: str) -> str | None:
            """Fetch and encode the PDF source based on the year and organization number.

            Args:
                aar (int): The year input value.
                orgnr (str): The organization number input value.

            Returns:
                str: A data URI for the PDF file, encoded in base64.

            Raises:
                PreventUpdate: If the year or organization number is not provided.
            """
            if not aar or not orgnr:
                raise PreventUpdate
            try:
                fs = FileClient.get_gcs_file_system()
                with fs.open(
                    f"gs://ssb-skatt-naering-data-delt-naeringspesifikasjon-selskap-prod/aarsregn/g{aar}/{orgnr}_{aar}.pdf",
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
