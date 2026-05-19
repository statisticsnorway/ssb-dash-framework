import base64
import logging
from abc import ABC
from abc import abstractmethod
from typing import ClassVar
from PIL import Image
import io

import gcsfs
import dash_bootstrap_components as dbc
from dash import callback, clientside_callback, dcc, html
from dash.dependencies import Input, State
from dash.dependencies import Output
from dash.exceptions import PreventUpdate
from dash import ClientsideFunction

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator
from ..utils.alert_handler import create_alert

logger = logging.getLogger(__name__)


class Aarsregnskap(ABC):
    """Module for displaying annual financial statements (Årsregnskap).

    Attributes:
        module_number: Sequential ID of the module instance.
        module_name: Name of the module class.
        label: User-visible label of the module, shown as "Årsregnskap".
        icon: Emoji icon representing the module.
        module_layout: The UI layout object returned by ``_create_layout()``.
    """

    _id_number: ClassVar[int] = 0
    module_number: int
    module_name: str
    label: str
    icon: str
    module_layout: html.Div

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
        if (
            "var-foretak"
            not in [  # TODO: Make it possible to define a separate value for fetching årsregnskap? Or keep it locked to foretak?
                x.id for x in VariableSelector._variableselectoroptions
            ]
        ):
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
                dcc.Store(id="tab-aarsregnskap-zoom-store"),
                dbc.Container(
                    fluid=True,
                    className="aarsregnskap-container",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        className="ssb-input",
                                        children=[
                                            html.Label("orgnr"),
                                            html.Div(
                                                className="input-wrapper",
                                                children=[
                                                    dbc.Input(
                                                        id="tab-aarsregnskap-input-orgnr",
                                                        type="text",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        className="ssb-input",
                                        children=[
                                            html.Label("år"),
                                            html.Div(
                                                className="input-wrapper",
                                                children=[
                                                    dbc.Input(
                                                        id="tab-aarsregnskap-input-aar",
                                                        type="number",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    )
                                ),
                                dbc.Col(
                                    html.A(
                                        dbc.Button(
                                            "Åpne i Brønnøysundregisteret",
                                            className="ssb-btn primary-btn",
                                            size="sm",
                                        ),
                                        id="tab-aarsregnskap-brreg-link",
                                        href="",
                                        target="_blank",
                                    ),
                                ),
                            ],
                            className="aarsregnskap-aar-foretak-row",
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "-",
                                                id="tab-aarsregnskap-zoom-out",
                                                size="sm",
                                            ),
                                            html.Span(
                                                "100%",
                                                id="tab-aarsregnskap-zoom-label",
                                                style={"margin": "0 8px"},
                                            ),
                                            dbc.Button(
                                                "+",
                                                id="tab-aarsregnskap-zoom-in",
                                                size="sm",
                                            ),
                                        ],
                                        id="tab-aarsregnskap-zoom-controls",
                                        style={
                                            "display": "none",
                                            "marginBottom": "8px",
                                        },
                                    ),
                                    html.Iframe(
                                        className="aarsregnskap-pdf-iframe",
                                        id="tab-aarsregnskap-iframe",
                                    ),
                                    html.Div(
                                        id="tab-aarsregnskap-img-container",
                                        style={"display": "none"},
                                        className="tab-aarsregnskap-img-container",
                                    ),
                                ],
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
                aar: The selected year.

            Returns:
                The updated year value.
            """
            logger.debug(f"Args:\naar: {aar}\n")
            return aar

        @callback(  # type: ignore[misc]
            Output("tab-aarsregnskap-input-orgnr", "value"),
            Input("var-foretak", "value"),
        )
        def update_orgnr(orgnr: str) -> str:
            """Update the organization number input field.

            Args:
                orgnr: The selected organization number.

            Returns:
                The updated organization number value.
            """
            logger.debug(f"Args:\norgnr: {orgnr}\n")
            return orgnr

        @callback(
            Output("tab-aarsregnskap-iframe", "src"),
            Output("tab-aarsregnskap-img-container", "children"),
            Output("tab-aarsregnskap-iframe", "style"),
            Output("tab-aarsregnskap-img-container", "style"),
            Output("tab-aarsregnskap-zoom-controls", "style"),
            Output("tab-aarsregnskap-brreg-link", "href"),
            Output("alert_store", "data", allow_duplicate=True),
            Input("tab-aarsregnskap-input-aar", "value"),
            Input("tab-aarsregnskap-input-orgnr", "value"),
            State("alert_store", "data"),
            prevent_initial_call="initial_duplicate",
        )
        def update_pdf_source(aar: int, orgnr: str, alert_store):
            """Fetch and encode the PDF source based on the year and organization number.
            If PDF cannot be found, it fetches the TIF-file instead (if it exists), and styles it like a PDF.
            Returns an alert to the user if neither can be found.

            Args:
                aar: The year input value.
                orgnr: The organization number input value.
                alert_store: Alert setup.

            Returns:
                A data URI for the PDF/TIF file, encoded in base64.
            """
            show_iframe = {"display": "block"}
            hide_iframe = {"display": "none"}
            show_div = {"display": "block"}
            hide_div = {"display": "none"}
            brreg_link = f"https://virksomhet.brreg.no/nb/oppslag/enheter/{orgnr}"

            if not aar or not orgnr:
                raise PreventUpdate

            fs = gcsfs.GCSFileSystem()
            base_path = f"gs://ssb-skatt-naering-data-delt-naeringspesifikasjon-selskap-prod/bildefil/g{aar}/{orgnr}_{aar}"

            MAX_SIZE = 1_000_000

            # Try PDF first
            try:
                with fs.open(f"{base_path}.pdf", "rb") as f:
                    pdf_bytes = f.read()

                if len(pdf_bytes) > MAX_SIZE:
                    import fitz  # pymupdf

                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    images = []
                    for page in doc:
                        pix = page.get_pixmap(dpi=72)
                        img = Image.frombytes(
                            "RGB", [pix.width, pix.height], pix.samples
                        )
                        images.append(img)
                    pdf_buffer = io.BytesIO()
                    images[0].save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=images[1:],
                    )
                    pdf_buffer.seek(0)
                    pdf_bytes = pdf_buffer.getvalue()
                    logger.info(f"Compressed PDF, new size: {len(pdf_bytes)} bytes")

                encoded = base64.b64encode(pdf_bytes).decode("utf-8")
                logger.info(f"Found PDF file, size: {len(pdf_bytes)} bytes")
                return (
                    f"data:application/pdf;base64,{encoded}",
                    [],
                    show_iframe,
                    hide_div,
                    {"display": "none"},
                    brreg_link,
                    [],
                )

            except FileNotFoundError:
                logger.debug("PDF not found, trying TIF")

            # Try TIF - convert each page to PNG
            try:
                with fs.open(f"{base_path}.tif", "rb") as f:
                    tif_bytes = f.read()
                tif_image = Image.open(io.BytesIO(tif_bytes))
                img_elements = []
                try:
                    while True:
                        png_buffer = io.BytesIO()
                        tif_image.copy().convert("RGB").save(png_buffer, format="PNG")
                        png_buffer.seek(0)
                        encoded = base64.b64encode(png_buffer.getvalue()).decode(
                            "utf-8"
                        )
                        img_elements.append(
                            html.Img(
                                src=f"data:image/png;base64,{encoded}",
                                style={
                                    "width": "100%",
                                    "display": "block",
                                    "marginBottom": "4px",
                                },
                            )
                        )
                        tif_image.seek(tif_image.tell() + 1)
                except EOFError:
                    pass
                return (
                    None,
                    img_elements,
                    hide_iframe,
                    show_div,
                    {"display": "block"},
                    brreg_link,
                    [],
                )
            except FileNotFoundError:
                logger.debug("TIF not found either")
                alert_store = [
                    create_alert(
                        message=f"Hverken PDF eller TIF av årsregnskapet funnet for årgang {aar}!",
                        color="warning",
                        duration=8,
                        ephemeral=True,
                    ),
                    *alert_store,
                ]
                return (
                    None,
                    [],
                    hide_iframe,
                    hide_div,
                    {"display": "none"},
                    brreg_link,
                    alert_store,
                )

        clientside_callback(
            ClientsideFunction(namespace="aarsregnskap", function_name="zoom"),
            Output("tab-aarsregnskap-zoom-store", "data"),
            Input("tab-aarsregnskap-zoom-in", "n_clicks"),
            Input("tab-aarsregnskap-zoom-out", "n_clicks"),
        )


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
