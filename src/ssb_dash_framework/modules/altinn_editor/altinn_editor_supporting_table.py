# TODO: Add functionality to add more types of helper things into the module.
import logging
from collections.abc import Callable

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import ibis
import pandas as pd
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from eimerdb import EimerDBInstance
from ibis import _

from ssb_dash_framework.setup import VariableSelector
from ssb_dash_framework.utils import conn_is_ibis

from ...utils.core_query_functions import conn_is_ibis
from .altinn_editor_utility import AltinnEditorStateTracker

logger = logging.getLogger(__name__)


class AltinnSupportTable:
    """Class for adding a supporting table to the component in AltinnSkjemadataEditor.

    In order to use it you need to connect it to inputs, preferably variables contained in the AltinnSkjemadataEditor such as 'altinnedit-ident', but it also supports connecting it to the VariableSelector.
    """

    suptable_id = 0

    def __init__(
        self,
        label: str,
        get_data_func: Callable[..., pd.DataFrame],
        inputs: list[str] | None = None,
        variableselector: VariableSelector | None = None,
    ) -> None:
        self.label = label
        self.inputs = inputs
        self.get_data_func = get_data_func
        if variableselector:
            self.variableselector = variableselector
        else:
            self.variableselector = VariableSelector([], [])
        self.suptable_id = AltinnSupportTable.suptable_id
        AltinnSupportTable.suptable_id += 1
        AltinnEditorSupportTables.support_components.append(self.support_table_layout())
        self.support_table_callbacks()

    def is_valid(self) -> None:
        if self.inputs:
            for input in self.inputs:
                if input not in AltinnEditorStateTracker.valid_altinnedit_options:
                    raise ValueError(
                        f"Invalid value passed in 'inputs'. Received '{input}', expected one of {AltinnEditorStateTracker.valid_altinnedit_options}"
                    )

    def support_table_content(self) -> html.Div:
        return html.Div(
            dag.AgGrid(
                defaultColDef={"editable": False},
                id=f"support-table-{self.suptable_id}",
            )
        )

    def support_table_callbacks(self) -> None:
        @callback(
            Output(f"support-table-{self.suptable_id}", "rowData"),
            Output(f"support-table-{self.suptable_id}", "columnDefs"),
            *[[Input(_id, "value") for _id in self.inputs] if self.inputs else []],
            *self.variableselector.get_all_callback_objects(),
        )
        def load_support_table_data(*args):
            logger.info(
                f"Running get_data_func for table '{self.label}' using args: {args}"
            )
            data = self.get_data_func(*args)
            return data.to_dict("records"), [{"field": col} for col in data.columns]

    def support_table_layout(self):
        return dbc.Tab(
            self.support_table_content(),
            label=self.label,
            tab_id=f"support-table-{self.label}-{self.suptable_id}",
        )


def add_year_diff_support_table(conn):
    def year_diff_support_table_get_data_func(ident, year):
        if conn_is_ibis(conn):
            logger.info("Assuming is ibis connection.")
            connection = conn
        elif isinstance(conn, EimerDBInstance):
            connection = ibis.polars.connect()
            data = conn.query(
                f"SELECT * FROM skjemadata_hoved WHERE ident = {ident} AND aar = {year}"
            )
            connection.create_table("skjemadata_hoved", data)
        else:
            raise TypeError("Wah")
        s = connection.table("skjemadata_hoved")
        return s.filter(_.ident == ident).to_pandas()

    AltinnSupportTable(
        label="Endring fra fjorår",
        inputs=["altinnedit-ident", "altinnedit-aar"],
        get_data_func=year_diff_support_table_get_data_func,
    )


class AltinnEditorSupportTables:
    """This module provides supporting tables for the Altinn editor.

    It adds a button that opens a modal with tabs containing tables with extra informatiion.

    Note:
        Adding your own supporting tables is not supported at this time.
    """

    support_components = []

    def __init__(
        self,
    ) -> None:
        """Initializes the AltinnEditorSupportTables module."""
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def add_default_tables(self, tables_to_add: list[str], conn):
        for table in tables_to_add:
            if table == "aar_til_fjoraar":
                add_year_diff_support_table(conn)
            else:
                raise ValueError(
                    f"Table named '{table}' not among available default tables."
                )

    def support_tables_modal(self) -> dbc.Modal:
        """Return a modal component containing tab content."""
        hjelpetabellmodal = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Hjelpetabeller")),
                dbc.ModalBody(
                    html.Div(
                        [
                            dbc.Tabs(
                                [*AltinnEditorSupportTables.support_components],
                                id="skjemadata-hjelpetabellmodal-tabs",
                            ),
                        ],
                    ),
                ),
            ],
            id="skjemadata-hjelpetabellmodal",
            is_open=False,
            size="xl",
        )
        logger.debug("Created support tables modal")
        return hjelpetabellmodal

    def _create_layout(self) -> html.Div:
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label(
                            "Hjelpetabeller",
                            className="mb-1",
                        ),
                        dbc.Button(
                            "Se hjelpetabeller",
                            id="altinn-support-tables-button",
                            className="w-100",
                        ),
                    ]
                ),
                self.support_tables_modal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout for the Altinn Editor Support Tables module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Registers the callbacks for the Altinn Editor Support Tables module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-hjelpetabellmodal", "is_open"),
            Input("altinn-support-tables-button", "n_clicks"),
            State("skjemadata-hjelpetabellmodal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False
