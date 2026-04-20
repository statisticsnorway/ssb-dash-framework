import logging
import threading
import time
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
from .....utils.core_models import UpdateSkjemadata
from ..core import DataEditorDataView

logger = logging.getLogger(__name__)

# Two-level cache for read_table results.
#
# _row_cache   — keyed by (table_name, sorted filter items); holds (rowData, columnDefs).
#                Invalidated per-table when a cell edit is committed.
# _col_cache   — keyed by table_name; holds columnDefs only.
#                Never invalidated (schema doesn't change at runtime).
#
# Both are protected by a single lock. The lock is NOT held during the postgres query
# so other threads can service cache hits while one thread is fetching.
_row_cache: dict[str, tuple[list, list]] = {}
_col_cache: dict[str, list] = {}
_cache_lock = threading.Lock()


class DataEditorTable(DataEditorDataView):
    """Requires table selector."""

    _id_number = 0

    def __init__(
        self,
        applies_to_tables: list[str],
        applies_to_forms: list[str],
        initial_rowdata: list[dict] | None = None,
        initial_coldefs: list[dict] | None = None,
    ) -> None:
        """Initializes a DataEditorTable for selected tables and forms.

        Args:
            applies_to_tables: A list of tables that the module should apply to.
            applies_to_forms: A list of forms that the module should apply to.
            initial_rowdata: Optional row data to embed in the layout on first render,
                bypassing the callback round-trip for the initial page load.
            initial_coldefs: Optional column definitions paired with initial_rowdata.
        """
        self.module_number = DataEditorTable._id_number
        self.module_name = self.__class__.__name__
        DataEditorTable._id_number += 1
        self.time_units = ["aar"]  # TODO fix, make set/get time_units functions
        self.refnr = "refnr"  # TODO fix, maybe make set/get for refnr?
        self._initial_rowdata = initial_rowdata
        self._initial_coldefs = initial_coldefs
        self.variable_selector = VariableSelector(
            selected_inputs=[
                *self.time_units,
                "altinnskjema",
                "refnr",
            ],  # Order of inputs is not random!
            selected_states=[],
        )
        self.divname = f"{self.module_name}-{self.module_number}"
        self.module_callbacks()
        super().__init__(
            applies_to_tables=applies_to_tables, applies_to_forms=applies_to_forms
        )
        print(self)

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
            style={
                "height": "100vh",
                "width": "100%",
            },
            children=[
                dag.AgGrid(
                    id=f"{self.module_name}-{self.module_number}-aggrid",
                    className="ag-theme-alpine header-style-on-filter",
                    style={"width": "100%", "height": "90vh"},
                    rowData=self._initial_rowdata,
                    columnDefs=self._initial_coldefs,
                    defaultColDef={
                        "resizable": True,
                        "sortable": True,
                        "floatingFilter": True,
                        "editable": True,
                        "filter": "agTextColumnFilter",
                        "flex": 1,
                    },
                    dashGridOptions={
                        "rowHeight": 38,
                        "suppressColumnVirtualisation": True,
                        "animateRows": False,
                    },
                ),
            ],
        )

    def module_callbacks(self) -> None:
        """Registers the necessary callbacks."""

        @callback(
            Output(f"{self.module_name}-{self.module_number}-aggrid", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-aggrid", "columnDefs"),
            Input("dataeditortableselector", "value"),
            self.variable_selector.get_all_callback_objects(),
            prevent_initial_call=self._initial_rowdata is not None,
        )
        def read_table(selected_table: str, *args: list[str]):
            """Populate the table view with data."""
            if (
                selected_table not in self.applies_to_tables
                or args[len(self.time_units)] not in self.applies_to_forms
            ):
                logger.info("Preventing update.")
                raise PreventUpdate

            if isinstance(_get_connection_object(), EimerDBInstance):
                N = len(self.time_units)
                args = list(args)
                args[:N] = map(int, args[:N])

            filter_dict = create_filter_dict(
                variables=[*self.time_units, "skjema", "refnr"], values=args
            )

            cache_key = f"{selected_table}:{sorted(filter_dict.items())}"

            # Fast path: return cached result without touching the database.
            with _cache_lock:
                cached = _row_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                msg = f"[PERF] read_table cache hit — {selected_table}: 0.000s"
                logger.info(msg)
                print(msg, flush=True)
                return cached

            # Cache miss: query postgres, build columndefs, populate both caches.
            start = time.perf_counter()
            with get_connection() as conn:
                t = conn.table(selected_table)
                df = t.filter(ibis_filter_with_dict(filter_dict)).to_pandas()
            elapsed = time.perf_counter() - start
            msg = f"[PERF] read_table cache miss — {selected_table}: {elapsed:.3f}s ({len(df)} rows)"
            logger.info(msg)
            print(msg, flush=True)

            with _cache_lock:
                if selected_table not in _col_cache:
                    _col_cache[selected_table] = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col in ["row_id", "row_ids", *self.time_units, "skjema", "refnr"],
                            "flex": 2 if col == "variabel" else 1,
                        }
                        for col in df.columns
                    ]
                columndefs = _col_cache[selected_table]
                result = df.to_dict("records"), columndefs
                _row_cache[cache_key] = result

            return result

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
            else:
                long = False
            long_variabel = edited[0]["data"]["variabel"]
            update = UpdateSkjemadata(
                table=table,
                long=long,
                ident=edited[0]["data"]["ident"],
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
                feedback = update.update_ibis(long)

            # Invalidate all cached results for this table so the next read
            # reflects the committed edit.
            with _cache_lock:
                stale = [k for k in _row_cache if k.startswith(f"{table}:")]
                for k in stale:
                    del _row_cache[k]

            return [feedback, *alert_store]

        @callback(  # type: ignore[misc]
            self.variable_selector.get_output_object("variabel"),
            Input(f"{self.module_name}-{self.module_number}-aggrid", "cellClicked"),
            State(f"{self.module_name}-{self.module_number}-aggrid", "rowData"),
            prevent_initial_call=True,
        )
        def send_variabel_to_variableselector(
            click: dict[str, Any], row_data: list[dict[str, Any]]
        ) -> str:
            """Make it possible to click the table and affect the VariableSelector."""
            logger.debug(f"Args:\nclick: {click}\nrow_data: {row_data}")

            if not click or not row_data:
                raise PreventUpdate

            columns = list(row_data[0].keys())

            long_format = "variabel" in columns and "verdi" in columns
            if long_format:
                return str(row_data[click["rowIndex"]]["variabel"])

            column = click.get("colId")  # wide format
            if column in ("aar", "ident", "skjema", "refnr", "tabell"):
                raise PreventUpdate

            return str(column)
