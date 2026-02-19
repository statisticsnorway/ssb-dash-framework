import logging
from typing import Any
from typing import Protocol

import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from eimerdb import EimerDBInstance

from ...setup.variableselector import VariableSelector
from ...utils.core_query_functions import conn_is_ibis
from .altinn_editor_comment import AltinnEditorComment
from .altinn_editor_contact import AltinnEditorContact
from .altinn_editor_control import AltinnEditorControl
from .altinn_editor_history import AltinnEditorHistory
from .altinn_editor_primary_table import AltinnEditorPrimaryTable
from .altinn_editor_submitted_forms import AltinnEditorSubmittedForms
from .altinn_editor_supporting_table import AltinnEditorSupportTables
from .altinn_editor_supporting_table import add_year_diff_support_table
from .altinn_editor_unit_details import AltinnEditorUnitDetails
from .altinn_editor_utility import AltinnEditorStateTracker

logger = logging.getLogger(__name__)


class AltinnEditorModule(Protocol):
    """Protocol to make mypy accept looping through modules and using the method layout() on them."""

    def layout(self) -> Any:
        """Returns layout."""
        ...


class AltinnSkjemadataEditor:
    """A fully functional module for editing Altinn forms.

    This module contains submodules with specific functionality.

    It requires a set table structure.
    """

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        starting_table: str | None = None,
        variable_connection: dict[str, str] | None = None,
        sidepanels: None = None,
        top_panels: None = None,
        primary_view: None = None,
    ) -> None:
        """Initialize the Altinn Skjemadata Editor module.

        Args:
            time_units: List of time units to be used in the module.
            conn: Database connection object that must have a 'query' method.
            starting_table: Table to be selected by default in module. If None, defaults to first table it finds.
            variable_connection: Dict containing the name of characteristics from the dataset as keys and the variable selector name associated with it as value.
            sidepanels: Later might be used for customizing sidepanel modules.
            top_panels: Later might be used for customizing top-panel modules.
            primary_view: Later might be used for replacing the primary table with different views.
        """
        AltinnEditorStateTracker.register_option("altinnedit-option1")
        AltinnEditorStateTracker.register_option("altinnedit-ident")

        self.icon = "🗊"
        self.label = "Data editor"

        add_year_diff_support_table(conn)
        self.conn = conn
        self.variable_connection = variable_connection if variable_connection else {}

        self.variableselector = VariableSelector(
            selected_inputs=[], selected_states=time_units
        )
        self.time_units_unaltered = time_units
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.starting_table = starting_table

        # Below is futureproofing in case of increasing modularity
        if primary_view is None:
            self.primary_table = AltinnEditorPrimaryTable(
                time_units=time_units,
                conn=self.conn,
                variable_selector_instance=self.variableselector,
            )
        if sidepanels is None:
            self.sidepanels: list[AltinnEditorModule] = [
                AltinnEditorSubmittedForms(
                    time_units=time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorUnitDetails(
                    time_units=time_units,
                    conn=self.conn,
                    variable_connection=self.variable_connection,
                    variable_selector_instance=self.variableselector,
                ),
            ]
        if top_panels is None:
            self.top_panels: list[AltinnEditorModule] = [
                AltinnEditorSupportTables(),
                AltinnEditorContact(
                    time_units=time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorHistory(
                    time_units=time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorControl(
                    time_units=time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorComment(
                    conn=self.conn,
                ),
            ]
        self.is_valid()
        self.module_callbacks()

    def is_valid(self) -> None:
        """Checks that all VariableSelector options required are defined."""
        VariableSelector([], []).get_option("var-ident", search_target="id")

    def get_skjemadata_table_names(self) -> list[dict[str, str]]:
        """Retrieves the names of all the skjemadata-tables in the eimerdb."""
        if isinstance(self.conn, EimerDBInstance):
            all_tables = list(self.conn.tables.keys())
            skjemadata_tables = [
                element for element in all_tables if element.startswith("skjemadata")
            ]
        elif conn_is_ibis(self.conn):
            skjemadata_tables = [
                table
                for table in self.conn.list_tables()
                if table.startswith("skjemadata_")
            ]
        else:
            raise TypeError(
                f"Connection object conn supplied to 'AltinnSkjemadataEditor' is not supported. Received: {type(self.conn)}"
            )
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
                        value=(
                            self.starting_table
                            if self.starting_table
                            else skjemadata_table_names[0]["value"]
                        ),
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
                                                        title, className="card-title"
                                                    ),
                                                    html.Div(
                                                        style={
                                                            "display": "grid",
                                                            "grid-template-columns": "100%",
                                                        },
                                                        children=[
                                                            dbc.Input(
                                                                id=f"altinnedit-{_id}",
                                                                type="number",
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                style={"max-height": "100%"},
                                            ),
                                            style={"max-height": "100%"},
                                        )
                                        for title, _id in zip(
                                            self.time_units_unaltered,
                                            self.time_units,
                                            strict=False,
                                        )
                                    ],
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "Ident", className="card-title"
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

        def generate_callback(unit: str) -> Any:
            """Makes connections between in-module time variables and variableselector time variables."""

            @callback(  # type: ignore[misc]
                Output(f"altinnedit-{unit}", "value"),
                Input(f"var-{unit}", "value"),
            )
            def callback_function(value: str) -> str:
                logger.debug(f"Args:\nvalue: {value}")
                return value

            return callback_function

        for unit in self.time_units:
            generate_callback(unit)

        @callback(  # type: ignore[misc]
            Output("altinnedit-ident", "value"),
            Input("var-ident", "value"),
        )
        def aar_to_tab(ident: str) -> str:
            logger.debug(f"Args:\nident: {ident}")
            return ident
