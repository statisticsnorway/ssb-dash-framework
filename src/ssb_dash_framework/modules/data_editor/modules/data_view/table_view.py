import logging
from typing import Any

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
from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_refnr
from .....utils.config_tools.set_variables import get_time_units
from .....utils.core_models import UpdateSkjemadata
from ...utils import EditorSettings
from .base import DataEditorDataView

logger = logging.getLogger(__name__)


class DataEditorTable(DataEditorDataView):
    """Requires table selector."""

    _id_number = 0

    def __init__(self, settings: EditorSettings) -> None:
        """Initializes a DataEditorTable for selected tables and forms.

        Args:
            applies_to_tables: A list of tables that the module should apply to.
            applies_to_forms: A list of forms that the module should apply to.
        """
        self.module_number = DataEditorTable._id_number
        self.module_name = self.__class__.__name__
        DataEditorTable._id_number += 1
        self.time_units = get_time_units()
        self.refnr = get_refnr()
        self.variable_selector = VariableSelector(
            selected_inputs=[
                self.time_units.name,
                "altinnskjema",
                get_refnr(),
            ],  # Order of inputs is not random!
            selected_states=[],
        )
        self.uneditable_columns = {"id", get_ident(), get_refnr(), "skjema", "variabel"}
        self.divname = f"{self.module_name}-{self.module_number}"
        self.module_callbacks()
        super().__init__(
            applies_to_tables=settings.form_data_table,
            applies_to_forms=settings.form_list,
        )
        # print(self)

    def __str__(self):
        return (
            f"{self.module_name}(#{self.module_number})\n"
            f"  tables : {self.applies_to_tables}\n"
            f"  forms  : {self.applies_to_forms}\n"
            f"  divname: {self.divname}\n"
        )

    def _create_layout(self) -> html.Div:
        return html.Div(
            id=f"{self.divname}",
            style={"display": "none"},
            children=[
                dag.AgGrid(
                    id=f"{self.module_name}-{self.module_number}-aggrid",
                    className="ag-theme-alpine ag-theme-ssb mb-2",
                    style={"width": "100%", "height": "90vh"},
                    defaultColDef={
                        "resizable": True,
                        "sortable": True,
                        "floatingFilter": True,
                        "filter": "agTextColumnFilter",
                        "flex": 1,
                    },
                    dashGridOptions={"rowHeight": 38},
                ),
            ],
        )

    def module_callbacks(self) -> None:
        """Registers the necessary callbacks."""

        @callback(
            Output(f"{self.module_name}-{self.module_number}-aggrid", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-aggrid", "columnDefs"),
            inputs={
                "selected_table": Input("dataeditortableselector", "value"),
                "form": self.variable_selector.get_input("altinnskjema"),
                "refnr": self.variable_selector.get_input(get_refnr()),
                "period": self.variable_selector.get_input(get_time_units().name),
            },
            # self.variable_selector.get_all_callback_objects(),
        )
        def read_table(selected_table: str, form, refnr, period):
            """Populate the table view with data."""
            if selected_table not in self.applies_to_tables:
                logger.info("Preventing update: table mismatch.")
                raise PreventUpdate

            if self.applies_to_forms and form not in self.applies_to_forms:
                logger.info("Preventing update: form mismatch.")
                raise PreventUpdate

            filter_dict = create_filter_dict(
                variables=[self.time_units.name, "skjema", "refnr"],
                values=[period, form, refnr],
            )

            logger.debug(f"Filterdict: {filter_dict}")

            with get_connection() as conn:
                t = conn.table(selected_table)
                df = t.filter(ibis_filter_with_dict(filter_dict)).to_pandas()

            logger.debug(f"Results from query:\n{df.head()}")

            columndefs = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": col
                    in [
                        "row_id",
                        "row_ids",
                        "enhetsinfo_row_ids",
                        self.time_units.name,
                        "skjema",
                        "refnr",
                    ],
                    "editable": False if col in self.uneditable_columns else True,
                    "flex": 2 if col == "variabel" else 1,
                }
                for col in df.columns
            ]
            logger.debug(f"Returning:\n{df.head()}")
            return df.to_dict("records"), columndefs

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(
                f"{self.module_name}-{self.module_number}-aggrid", "cellValueChanged"
            ),
            State("dataeditortableselector", "value"),
            State(f"{self.module_name}-{self.module_number}-aggrid", "columnDefs"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_table(edited, table: str, columndefs, alert_store):
            """Updates the data in the backend."""
            logger.info("Attempting to update data.")
            columns = [col["field"] for col in columndefs]
            if "variabel" in columns and "verdi" in columns:
                long = True
                variabel = edited[0]["data"]["variabel"]
            else:
                long = False
                variabel = edited[0]["colId"]

            update = UpdateSkjemadata(
                table=table,
                long=long,
                ident=edited[0]["data"]["ident"],
                refnr=edited[0]["data"]["refnr"],
                column=edited[0]["colId"],
                variable=variabel,
                value=edited[0]["value"],
                old_value=edited[0]["oldValue"],
            )
            logger.info(update)
            if isinstance(_get_connection_object(), EimerDBInstance):
                logger.debug("Attempting to update using eimerdb logic.")
                feedback = update.update_eimer(long)
            elif isinstance(_get_connection_object(), ConnectionPool):
                logger.debug("Attempting to update using ibis logic.")
                feedback = update.update_ibis(long)
            return [feedback, *alert_store]

        @callback(  # type: ignore[misc]
            self.variable_selector.get_output_object("variabel"),
            Input(f"{self.module_name}-{self.module_number}-aggrid", "cellClicked"),
            State(f"{self.module_name}-{self.module_number}-aggrid", "rowData"),
            self.variable_selector.get_state("variabel"),
            prevent_initial_call=True,
        )
        def send_variabel_to_variableselector(
            click: dict[str, Any],
            row_data: list[dict[str, Any]],
            statistikkvariabel: str,
        ) -> str:
            """Make it possible to click the table and affect the VariableSelector."""
            logger.debug(f"Args:\nclick: {click}\nrow_data: {row_data}")

            if not click or not row_data:
                raise PreventUpdate

            columns = list(row_data[0].keys())

            long_format = "variabel" in columns and "verdi" in columns
            if long_format:
                variable = str(row_data[click["rowIndex"]]["variabel"])
                if variable == statistikkvariabel:
                    raise PreventUpdate
                return variable

            column = click.get("colId")  # wide format
            if column == statistikkvariabel:
                raise PreventUpdate

            if column in ("aar", "ident", "skjema", "refnr", "tabell"):
                raise PreventUpdate

            return str(column)
