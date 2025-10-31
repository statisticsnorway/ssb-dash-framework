import logging
from typing import Any

import dash_ag_grid as dag
import ibis
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from eimerdb import EimerDBInstance
from ibis import _

from ssb_dash_framework.utils import conn_is_ibis
from ssb_dash_framework.utils import ibis_filter_with_dict

from ...setup.variableselector import VariableSelector
from ...utils.alert_handler import create_alert
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorPrimaryTable:
    """Module creating the primary editing table for the Altinn Editor.

    Note:
        Is in a separate class from the view to futureproof, in future is possible to replace or even make customizable.
    """

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor primary table module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
            AssertionError: If the connection object does not have a 'query' method.
        """
        print("Test: ", conn_is_ibis(conn))
        if not isinstance(conn, EimerDBInstance) and not conn_is_ibis(conn):
            raise TypeError(
                f"The database object must be 'EimerDBInstance' or ibis connection. Received: {type(conn)}"
            )
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variableselector = variable_selector_instance
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.module_layout = self._create_layout()
        self._is_valid()
        self.module_callbacks()

    def _is_valid(self) -> None:
        VariableSelector([], []).get_option(
            "var-statistikkvariabel", search_target="id"
        )

    def _create_layout(self) -> html.Div:
        """Creates the module layout."""
        return html.Div(
            id="altinn-editor-primary-table",
            style={
                "height": "100vh",
                "width": "100%",
            },
            children=[
                dag.AgGrid(
                    id="altinnedit-table-skjemadata",
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

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemadata", "rowData"),
            Output("altinnedit-table-skjemadata", "columnDefs"),
            Input("altinnedit-refnr", "value"),
            Input("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            self.variableselector.get_all_states(),
        )
        def hovedside_update_altinnskjema(
            refnr: str, tabell: str, skjema: str, *args: Any
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
            logger.debug(
                f"Args:\n"
                f"refnr: {refnr}\n"
                f"tabell: {tabell}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )
            if isinstance(self.conn, EimerDBInstance):
                conn = ibis.polars.connect()
                data = self.conn.query(f"SELECT * FROM {tabell}")
                conn.create_table(tabell, data)
                datatyper = self.conn.query("SELECT * FROM datatyper")
                conn.create_table("datatyper", datatyper)
            elif conn_is_ibis(self.conn):
                conn = self.conn
            else:
                raise TypeError("Connection object is invalid type.")
            columns = conn.table(tabell).columns
            if "variabel" in columns and "verdi" in columns:
                long_format = True
            else:
                long_format = False

            if (
                refnr is None
                or tabell is None
                or skjema is None
                or any(arg is None for arg in args)
            ):
                logger.debug("Returning nothing.")
                return None, None
            filter_dict = {"aar": "2024"}
            if long_format:
                logger.debug("Processing long data")
                try:
                    t = conn.table(tabell)
                    d = conn.table("datatyper")
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    logger.debug(
                        f"partition_select:\n{create_partition_select(desired_partitions=self.time_units,skjema=skjema,**partition_args,)}"
                    )

                    t = (
                        t.filter(_.refnr == refnr)
                        .join(d, "variabel", how="left")
                        .order_by(_.radnr)
                    )
                    t = t.filter(ibis_filter_with_dict(filter_dict))
                    df = t.drop(
                        [col for col in t.columns if col.endswith("_right")]
                        + ["datatype", "radnr", "tabell"]
                    ).to_pandas()
                    logger.debug(f"resultat dataframe:\n{df.head(2)}")
                    columndefs = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                            "flex": 2 if col == "variabel" else 1,
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columndefs
                except Exception as e:
                    logger.error(
                        f"Error in hovedside_update_altinnskjema (long format): {e}",
                        exc_info=True,
                    )
                    return None, None
            else:
                logger.debug("Processing wide data")
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    t = conn.table(tabell)
                    
                    df = t.filter(ibis_filter_with_dict(filter_dict)).filter(_.refnr == refnr).to_pandas()
                    columndefs = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columndefs
                except Exception as e:
                    logger.error(
                        f"Error in hovedside_update_altinnskjema (wide format): {e}",
                        exc_info=True,
                    )
                    return None, None

        @callback(  # type: ignore[misc]
            Output("var-statistikkvariabel", "value"),
            Input("altinnedit-table-skjemadata", "cellClicked"),
            State("altinnedit-table-skjemadata", "rowData"),
        )
        def select_variabel(
            click: dict[str, Any], row_data: list[dict[str, Any]]
        ) -> str:
            logger.debug(f"Args:\nclick: {click}\nrow_data: {row_data}")
            if not click:
                raise PreventUpdate
            return str(row_data[click["rowIndex"]]["variabel"])

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemadata", "cellValueChanged"),
            State("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            self.variableselector.get_all_states(),
            prevent_initial_call=True,
        )
        def update_table(
            edited: list[dict[str, dict[str, Any] | Any]],
            tabell: str,
            skjema: str,
            alert_store: list[dict[str, Any]],
            *args: Any,
        ) -> list[dict[str, Any]]:
            logger.debug(
                f"Args:\n"
                f"edited: {edited}\n"
                f"tabell: {tabell}\n"
                f"skjema: {skjema}\n"
                f"alert_store: {alert_store}\n"
                f"args: {args}"
            )
            if conn_is_ibis(self.conn):
                period_where = [f"{x} = '{edited[0]['data'][x]}'" for x in self.time_units]
                ident = edited[0]['data']["ident"]
                refnr = edited[0]['data']["refnr"]
                value = edited[0]["value"]
                old_value = edited[0]["oldValue"]
                condition_str = " AND ".join(period_where)
                columns = self.conn.table(tabell).columns
                if "variabel" in columns and "verdi" in columns:
                    try:
                        variable = edited[0]['data']["variabel"]
                        query = f"""
                            UPDATE {tabell}
                            SET verdi = '{value}'
                            WHERE variabel = '{variable}' AND ident = '{ident}' AND refnr = '{refnr}' AND {condition_str}
                        """
                        self.conn.raw_sql(query)
                        alert_store = [
                            create_alert(
                                f"ident: {ident}, variabel: {variable} er oppdatert fra {old_value} til {value}!",
                                "success",
                                ephemeral=True,
                            ),
                            *alert_store,
                        ]
                    except Exception as e:
                        raise e
                else:
                    try:
                        variable = edited[0]["colId"]
                        query = f"""
                            UPDATE {tabell}
                            SET {variable} = '{value}'
                            WHERE ident = '{ident}' AND refnr = '{refnr}' AND {condition_str}
                        """
                        self.conn.raw_sql(query)
                        alert_store = [
                            create_alert(
                                f"ident: {ident}, {variable} er oppdatert fra {old_value} til {value}!",
                                "success",
                                ephemeral=True,
                            ),
                            *alert_store,
                        ]
                    except Exception as e:
                        raise e
                return alert_store
                
            elif isinstance(self.conn, EimerDBInstance):
                partition_args = dict(zip(self.time_units, args, strict=False))
                tables_editable_dict = {}
                data_dict = self.conn.tables

                for table, details in data_dict.items():
                    if table.startswith("skjemadata") and "schema" in details:
                        field_editable_dict = {
                            field["name"]: field.get("app_editable", False)
                            for field in details["schema"]
                        }
                        tables_editable_dict[table] = field_editable_dict

                table_editable_dict = tables_editable_dict[tabell]
                edited_column = edited[0]["colId"]

                schema = self.conn.tables[tabell]["schema"]
                columns = {field["name"] for field in schema}
                if "variabel" in columns and "verdi" in columns:
                    long_format = True
                else:
                    long_format = False

                if table_editable_dict[edited_column] is True:
                    old_value = edited[0]["oldValue"]
                    new_value = edited[0]["value"]
                    row_id = edited[0]["data"]["row_id"]
                    ident = edited[0]["data"]["ident"]

                    try:
                        self.conn.query(
                            f"""UPDATE {tabell}
                            SET {edited_column} = '{new_value}'
                            WHERE row_id = '{row_id}'
                            """,
                            partition_select=create_partition_select(
                                desired_partitions=self.time_units,
                                skjema=skjema,
                                **partition_args,
                            ),
                        )
                        if long_format:
                            variabel = edited[0]["data"]["variabel"]
                            alert_store = [
                                create_alert(
                                    f"ident: {ident}, variabel: {variabel} er oppdatert fra {old_value} til {new_value}!",
                                    "success",
                                    ephemeral=True,
                                ),
                                *alert_store,
                            ]
                        else:
                            alert_store = [
                                create_alert(
                                    f"ident: {ident}, {edited_column} er oppdatert fra {old_value} til {new_value}!",
                                    "success",
                                    ephemeral=True,
                                ),
                                *alert_store,
                            ]
                    except Exception as e:
                        alert_store = [
                            create_alert(
                                f"Oppdateringa feilet. {str(e)[:60]}",
                                "danger",
                                ephemeral=True,
                            ),
                            *alert_store,
                        ]
                    return alert_store
                else:
                    alert_store = [
                        create_alert(
                            f"Kolonnen {edited_column} kan ikke editeres!",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                    return alert_store
            else:
                raise TypeError(f"Conection 'self.conn' is not a valid connection object. Is type: {type(self.conn)}")