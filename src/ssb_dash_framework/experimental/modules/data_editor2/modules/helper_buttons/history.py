# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
import logging

import dash_ag_grid as dag
import tzlocal
from dash import Input
from dash import Output
from dash import callback
from dash import html
from ibis import _
import dash_bootstrap_components as dbc

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from .editor_helper_button import DataEditorHelperButton

logger = logging.getLogger(__name__)

local_tz = tzlocal.get_localzone()


class DataEditorHistory(DataEditorHelperButton):
    """This module provides supporting tables for the DataEditor.

    It adds a button that opens a modal with tabs containing tables with extra informatiion.

    Note:
        Adding your own supporting tables is not supported at this time.
    """


    def __init__(
        self,
        applies_to_tables: list[str] | None = None,
        applies_to_forms: list[str] | None = None,
    ) -> None:
        """Initializes the DataEditorEditorSupportTables module."""
        self.module_number = DataEditorHistory._id_number
        self.module_name = self.__class__.__name__
  
        self.variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[get_refnr(), get_time_units().name],
        )
        self.modal_body = self._create_modal_body()

        super().__init__(label="Historikk")

        self.module_callbacks()

    def _create_modal_body(self) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        dbc.Label("Skjul insert-data"),
                        dbc.Checklist(
                            options=[{"label": "Altinn3", "value": 1}],
                            value=[1],
                            id=f"{self.module_name}-{self.module_number}-toggle",
                            inline=True,
                            switch=True,
                        ),
                    ],
                    className=f"{self.module_name}-toggle-bar",
                ),
                html.Div(
                    dag.AgGrid(
                        id=f"{self.module_name}-{self.module_number}-table",
                        className="ag-theme-alpine ag-theme-ssb mb-2",
                        dashGridOptions={"enableCellTextSelection": True},
                        defaultColDef={"filter": True, "resizable": True},
                        columnSize="responsiveSizeToFit",
                    ),
                    className=f"{self.module_name}-table",
                ),
            ],
            className=f"{self.module_name}-body",
        )

    def module_callbacks(self):
        @callback(
            Output(f"{self.module_name}-{self.module_number}-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-table", "columnDefs"),
            Input(f"{self.module_name}-{self.module_number}-modal", "is_open"),
            Input(f"{self.module_name}-{self.module_number}-toggle", "value"),
            *self.variableselector.get_all_callback_objects(),
        )
        def update_history_view(is_open, insert_toggle: bool, refnr, *args):
            df = self.fetcher.get_history(refnr)
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "filter": True,
                    "resizable": True,
                    "hide": col
                    in [
                        "skjema",
                        "refnr",
                    ],
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columns
            