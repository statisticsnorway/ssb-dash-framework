import logging

import dash_ag_grid as dag
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate
from eimerdb import EimerDBInstance
from psycopg_pool import ConnectionPool

from ssb_dash_framework.utils.core_query_functions import create_filter_dict
from ssb_dash_framework.utils.core_query_functions import ibis_filter_with_dict

from .....setup.variableselector import VariableSelector
from .....utils.config_tools.connection import _get_connection_object
from .....utils.config_tools.connection import get_connection
from .....utils.core_models import UpdateSkjemadata
from ..core import DataEditorDataView

logger = logging.getLogger(__name__)


class DataEditorTable(DataEditorDataView):
    """Requires table selector."""

    _id_number = 0

    def __init__(self, applies_to_table) -> None:
        self.module_number = DataEditorTable._id_number
        self.module_name = self.__class__.__name__
        DataEditorTable._id_number += 1
        self.time_units = ["aar"]  # TODO fix, make set/get time_units functions
        self.refnr = "refnr"  # TODO fix, maybe make set/get for refnr?
        self.variable_selector = VariableSelector(
            selected_inputs=[*self.time_units, "refnr"], selected_states=[]
        )
        self.divname = f"{self.module_name}-{self.module_number}"
        self.module_callbacks()
        super().__init__(applies_to_table=applies_to_table)

    def _create_layout(self):
        return html.Div(
            id=f"{self.divname}",
            style={
                "height": "100vh",
                "width": "100%",
            },
            children=[
                dag.AgGrid(
                    id=f"dataeditor-table-{self._id_number}-aggrid",
                    className="ag-theme-alpine header-style-on-filter",
                    style={"width": "100%", "height": "90vh"},
                    defaultColDef={
                        "resizable": True,
                        "sortable": True,
                        "floatingFilter": True,
                        "editable": True,
                        "filter": "agTextColumnFilter",
                        "flex": 1,
                    },
                    dashGridOptions={"rowHeight": 38},
                ),
            ],
        )

    def module_callbacks(self):
        @callback(
            Output(f"dataeditor-table-{self._id_number}-aggrid", "rowData"),
            Output(f"dataeditor-table-{self._id_number}-aggrid", "columnDefs"),
            Input("dataeditortableselector", "value"),
            self.variable_selector.get_all_callback_objects(),
        )
        def read_table(value, *args: list[str]):
            # Prevent unneccessary callbacks
            if value not in self.applies_to_table:
                raise PreventUpdate

            if isinstance(_get_connection_object(), EimerDBInstance):
                N = len(self.time_units)
                args = list(args)
                args = [int(x) for x in args[:N]] + args[N:]

            filter_dict = create_filter_dict(
                variables=[*self.time_units, "refnr"], values=args
            )

            print(filter_dict)

            with get_connection() as conn:
                t = conn.table(value)
                df = t.filter(ibis_filter_with_dict(filter_dict)).to_pandas()

            columndefs = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": col
                    in [
                        "row_id",
                        "row_ids",
                        *self.time_units,
                        "skjema",
                        "refnr",
                    ],
                    "flex": 2 if col == "variabel" else 1,
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columndefs

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"dataeditor-table-{self._id_number}-aggrid", "cellValueChanged"),
            State("dataeditortableselector", "value"),
            State(f"dataeditor-table-{self._id_number}-aggrid", "columnDefs"),
            prevent_initial_call=True,
        )
        def update_table(edited, table, columndefs):
            logger.info("Attempting to update data.")
            columns = [col["field"] for col in columndefs]
            if "variabel" in columns and "verdi" in columns:
                long = True
            else:
                long = False
            long_variabel = edited[0]["data"]["variabel"]
            update = UpdateSkjemadata(
                table=table,
                long=long,
                refnr=edited[0]["data"]["refnr"],
                column=edited[0]["colId"],
                variable=long_variabel if long else edited[0]["colId"],
                value=edited[0]["value"],
                old_value=edited[0]["oldValue"],
            )
            logger.info(update)
            if isinstance(_get_connection_object(), EimerDBInstance):
                logger.debug("Attempting to update using eimerdb logic.")
                feedback = update.update_eimer(long)
            elif isinstance(_get_connection_object(), ConnectionPool):
                logger.debug("Attempting to update using ibis logic.")
                feedback = update.update_ibis()
            return feedback
