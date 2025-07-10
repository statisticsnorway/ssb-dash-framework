import base64
import logging
from abc import ABC
from abc import abstractmethod
from typing import ClassVar

import dash_bootstrap_components as dbc
from dapla import FileClient
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class Aarsregnskap(ABC):
    """Module for displaying annual financial statements (Årsregnskap).

    Attributes:
        label (str): Label for the module when initialized, displayed as "Årsregnskap".
    """

    _id_number: ClassVar[int] = 0

    def __init__(
        self,
    ) -> None:
        """Initialize the Aarsregnskap component.

        Sets up the label, validates required variables, and initializes the
        layout and callbacks for the module.
        """
        self.module_number = Aarsregnskap._id_number
        self.module_name = self.__class__.__name__
        Aarsregnskap._id_number += 1
        self.label = "Årsregnskap"
        self.icon = "🧾"
        self._is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _is_valid(self) -> None:
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
            className="aarsregnskap",
            children=[
                dbc.Container(
                    fluid=True,
                    className="aarsregnskap-container",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Label("År"),
                                            dbc.Input(
                                                id="tab-aarsregnskap-input-aar",
                                                type="number",
                                            ),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Label("Orgnr"),
                                            dbc.Input(
                                                id="tab-aarsregnskap-input-orgnr"
                                            ),
                                        ]
                                    )
                                ),
                            ],
                            className="aarsregnskap-aar-foretak-row",
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.Iframe(
                                    className="aarsregnskap-pdf-iframe",
                                    id="tab-aarsregnskap-iframe",
                                ),
                                className="aarsregnskap-pdf-col",
                            ),
                            className="aarsregnskap-pdf-row",
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
            Output("tab-aarsregnskap-input-aar", "value"),
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
            Output("tab-aarsregnskap-input-orgnr", "value"),
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
            Output("tab-aarsregnskap-iframe", "src"),
            Input("tab-aarsregnskap-input-aar", "value"),
            Input("tab-aarsregnskap-input-orgnr", "value"),
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
            path_to_file = f"gs://ssb-skatt-naering-data-delt-naeringspesifikasjon-selskap-prod/aarsregn/g{aar}/{orgnr}_{aar}.pdf"
            logger.debug(f"Trying to open file: {path_to_file}")
            try:
                fs = FileClient.get_gcs_file_system()
                with fs.open(
                    path_to_file,
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


class AarsregnskapTab(TabImplementation, Aarsregnskap):
    """AarsregnskapTab is an implementation of the Aarsregnskap module as a tab in a Dash application."""

    def __init__(self) -> None:
        """Initializes the AarsregnskapTab class."""
        Aarsregnskap.__init__(self)
        TabImplementation.__init__(self)


class AarsregnskapWindow(WindowImplementation, Aarsregnskap):
    """AarsregnskapWindow is an implementation of the Aarsregnskap module as a window in a Dash application."""

    def __init__(self) -> None:
        """Initializes the AarsregnskapWindow class."""
        Aarsregnskap.__init__(self)
        WindowImplementation.__init__(self)
