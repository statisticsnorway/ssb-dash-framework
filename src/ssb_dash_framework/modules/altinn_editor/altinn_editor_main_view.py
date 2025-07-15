import logging
from collections.abc import Callable

import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...setup.variableselector import VariableSelector
from .altinn_editor_comment import AltinnEditorComment
from .altinn_editor_contact import AltinnEditorContact
from .altinn_editor_control import AltinnEditorControl
from .altinn_editor_history import AltinnEditorHistory
from .altinn_editor_primary_table import AltinnEditorPrimaryTable
from .altinn_editor_submitted_forms import AltinnEditorSubmittedForms
from .altinn_editor_supporting_table import AltinnEditorSupportTables
from .altinn_editor_unit_details import AltinnEditorUnitDetails

logger = logging.getLogger(__name__)


class AltinnSkjemadataEditor:
    """A fully functional module for editing Altinn forms.

    This module contains submodules with specific functionality.
    """

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_connection: dict[str, str],
        sidepanels: None = None,
        top_panels: None = None,
    ) -> None:
        """Initialize the Altinn Skjemadata Editor module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_connection (dict[str, str]): Dict containing the name of characteristics from the dataset as keys and the variable selector name associated with it as value.
            sidepanels (None): Later might be used for customizing sidepanel modules.
            top_panels (None): Later might be used for customizing top-panel modules.
        """
        self.icon = "🗊"
        self.label = "Data editor"

        self.time_units = time_units
        self.conn = conn
        self.variable_connection = variable_connection

        self.variableselector = VariableSelector(
            selected_inputs=[], selected_states=self.time_units
        )

        self.primary_table = AltinnEditorPrimaryTable(
            time_units=self.time_units,
            conn=self.conn,
            variable_selector_instance=self.variableselector,
        )
        # Below is futureproofing in case of increasing modularity
        if sidepanels is None:
            self.sidepanels = [
                AltinnEditorSubmittedForms(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorUnitDetails(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_connection=self.variable_connection,
                    variable_selector_instance=self.variableselector,
                ),
            ]
        if top_panels is None:
            self.top_panels = [
                AltinnEditorSupportTables(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorContact(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorHistory(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorControl(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorComment(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
            ]

        self.module_callbacks()

    def get_skjemadata_table_names(self) -> list[dict[str, str]]:
        """Retrieves the names of all the skjemadata-tables in the eimerdb."""
        all_tables = list(self.conn.tables.keys())
        skjemadata_tables = [
            element for element in all_tables if element.startswith("skjemadata")
        ]
        return [{"label": item, "value": item} for item in skjemadata_tables]

    def skjemadata_table_selector(self) -> dbc.Col:
        """Makes a dropdown for selecting which 'skjemadata' table to view."""
        skjemadata_table_names = self.get_skjemadata_table_names()
        return dbc.Col(
            dbc.Form(
                [
                    dbc.Label("Tabell", className="mb-1"),
                    dcc.Dropdown(
                        id="altinnedit-option1",
                        options=skjemadata_table_names,
                        value=skjemadata_table_names[0]["value"],
                    ),
                ]
            ),
            md=2,
        )

    def _create_layout(self) -> html.Div:
        return html.Div(
            id="altinn-editor-main-view",
            style={
                "height": "100vh",
                "width": "100%",
            },
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                id="altinn-editor-sidepanels",
                                style={
                                    "height": "100%",
                                    "width": "100%",
                                },
                                children=[
                                    *[
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        unit, className="card-title"
                                                    ),
                                                    html.Div(
                                                        style={
                                                            "display": "grid",
                                                            "grid-template-columns": "100%",
                                                        },
                                                        children=[
                                                            dbc.Input(
                                                                id=f"altinnedit-{unit}",
                                                                type="number",
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                style={"max-height": "100%"},
                                            ),
                                            style={"max-height": "100%"},
                                        )
                                        for unit in self.time_units
                                    ],
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "ident", className="card-title"
                                                ),
                                                dbc.Input(
                                                    id="altinnedit-ident", type="text"
                                                ),
                                            ]
                                        ),
                                        className="mb-2",
                                    ),
                                    *[
                                        sidepanel_module.layout()
                                        for sidepanel_module in self.sidepanels
                                    ],
                                ],
                            ),
                            width=1,
                        ),
                        dbc.Col(
                            [
                                dbc.Row(
                                    id="altinn-editor-top-panels",
                                    children=[
                                        self.skjemadata_table_selector(),
                                        *[
                                            dbc.Col(top_panel.layout(), md=2)
                                            for top_panel in self.top_panels
                                        ],
                                    ],
                                ),
                                dbc.Row(
                                    html.Div(
                                        children=[self.primary_table.layout()],
                                    )
                                ),
                            ]
                        ),
                    ]
                )
            ],
        )

    def layout(self) -> html.Div:
        """Generates the layout for the Altinn Skjemadata Editor tab."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Defines the callbacks for the module."""

        def generate_callback(unit: str) -> Callable[[str], str]:
            @callback(  # type: ignore[misc]
                Output(f"altinnedit-{unit}", "value"),
                Input(f"var-{unit}", "value"),
            )
            def callback_function(value: str) -> str:
                return value

            return callback_function

        for unit in self.time_units:
            generate_callback(unit)

        @callback(  # type: ignore[misc]
            Output("altinnedit-ident", "value"),
            Input("var-ident", "value"),
        )
        def aar_to_tab(ident: str) -> str:
            return ident
