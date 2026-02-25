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
from psycopg_pool import ConnectionPool

from ssb_dash_framework.utils import create_filter_dict
from ssb_dash_framework.utils import ibis_filter_with_dict

from ...setup.variableselector import VariableSelector
from ...utils.alert_handler import create_alert
from ...utils.config_tools.connection import _get_connection_object
from ...utils.config_tools.connection import get_connection
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
        variable_selector_instance: VariableSelector,
        cols_to_hide: list[str] | None = None,
    ) -> None:
        """Initializes the Altinn Editor primary table module.

        Args:
            time_units: List of time units to be used in the module.
            conn: Database connection object that must have a 'query' method.
            variable_selector_instance: An instance of VariableSelector for variable selection.
            cols_to_hide: A list of columns to ignore. Defaults to ["row_id","row_ids",*self.time_units,"skjema","refnr"].

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector. Or
                if connection object is neither EimerDBInstance or Ibis connection.
        """
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variableselector = variable_selector_instance
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        if cols_to_hide is None:
            self.cols_to_hide = [
                "row_id",
                "row_ids",
                *self.time_units,
                "skjema",
                "refnr",
            ]
        else:
            if not isinstance(cols_to_hide, list):
                raise TypeError(
                    f"Argument 'cols_to_hide' must be a list of strings. Received: {cols_to_hide}"
                )
            self.cols_to_hide = cols_to_hide
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
        # check if var-bedrift exists
        try:
            self.variableselector.get_option("var-bedrift", search_target="id")
            has_bedrift = True
        except ValueError:
            has_bedrift = False
            logger.debug("var-bedrift not available, skipping bedrift sorting")

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemadata", "rowData", allow_duplicate=True),
            Output("altinnedit-table-skjemadata", "columnDefs", allow_duplicate=True),
            Input("altinnedit-refnr", "value"),
            Input("altinnedit-option1", "value"),
            Input("var-ident", "value"),
            State("altinnedit-skjemaer", "value"),
            (
                State("var-bedrift", "value")
                if has_bedrift
                else State("altinnedit-refnr", "value")
            ),  # Dummy state if no bedrift
            self.variableselector.get_all_states(),
            prevent_initial_call=True,
        )
        def hovedside_update_altinnskjema(
            refnr: str,
            tabell: str,
            ident: str,
            skjema: str,
            bedrift_or_dummy: str,
            *args: Any,
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:

            # extract bedrift if it exists
            bedrift = bedrift_or_dummy if has_bedrift else None

            logger.debug(
                f"Args:\n"
                f"refnr: {refnr}\n"
                f"tabell: {tabell}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )

            if (
                refnr is None
                or tabell is None
                or skjema is None
                or any(arg is None for arg in args)
            ):
                logger.info("Returning nothing.")
                logger.debug(f"Args length: {len(args)}")
                return [], []

            filter_dict = create_filter_dict(
                self.time_units, args
            )  # May need args to be ints for eimerdb?

            with get_connection(necessary_tables=[tabell, "datatyper"]) as conn:
                columns = conn.table(tabell).columns
                if "variabel" in columns and "verdi" in columns:
                    long_format = True
                else:
                    long_format = False
                if long_format:
                    logger.debug("Processing long data")
                    try:
                        t = conn.table(tabell)
                        d = conn.table("datatyper")
                        d = d.filter(ibis_filter_with_dict(filter_dict))
                        partition_args = dict(zip(self.time_units, args, strict=False))
                        logger.debug(
                            f"partition_select:\n{create_partition_select(desired_partitions=self.time_units,skjema=skjema,**partition_args,)}"
                        )
                        # sort by bedrift if available
                        if bedrift and "ident" in t.columns:
                            t = t.order_by(
                                [_.ident.cases((bedrift, 0), else_=1), _.radnr]
                            )
                        else:
                            t = t.order_by(_.radnr)

                        df = t.drop(
                            [col for col in t.columns if col.endswith("_right")]
                            + ["datatype", "radnr", "tabell"]
                        ).to_pandas()
                        logger.debug(f"resultat dataframe:\n{df.head(2)}")
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

                        df = (
                            t.filter(ibis_filter_with_dict(filter_dict))
                            .filter(_.refnr == refnr)
                            .to_pandas()
                        )

                        # sort by bedrift if it exists
                        if bedrift and "ident" in df.columns:
                            df = df.sort_values(
                                by="ident",
                                key=lambda x: x.map(lambda v: 0 if v == bedrift else 1),
                            )

                        t = t.filter(_.refnr == refnr).join(d, "variabel", how="left")
                        t = t.filter(ibis_filter_with_dict(filter_dict))

                        # sort by bedrift if available
                        if bedrift and "ident" in t.columns:
                            t = t.mutate(
                                sort_priority=ibis.case()
                                .when(_.ident == bedrift, 0)
                                .else_(1)
                                .end()
                            ).order_by(["sort_priority", _.radnr])
                        else:
                            t = t.order_by(_.radnr)

                        df = t.drop(
                            [col for col in t.columns if col.endswith("_right")]
                            + ["datatype", "radnr", "tabell"]
                        ).to_pandas()
                        logger.debug(f"resultat dataframe:\n{df.head(2)}")
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
                    except Exception as e:
                        logger.error(
                            f"Error in hovedside_update_altinnskjema (long format): {e}",
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
            connection_object = _get_connection_object()
            if isinstance(connection_object, ConnectionPool):
                with get_connection() as conn:
                    period_where = [
                        f"{x} = '{edited[0]['data'][x]}'" for x in self.time_units
                    ]
                    ident = edited[0]["data"]["ident"]
                    refnr = edited[0]["data"]["refnr"]
                    value = edited[0]["value"]
                    old_value = edited[0]["oldValue"]
                    condition_str = " AND ".join(period_where)
                    columns = conn.table(tabell).columns
                    if "variabel" in columns and "verdi" in columns:
                        try:
                            variable = edited[0]["data"]["variabel"]
                            query = f"""
                                UPDATE {tabell}
                                SET verdi = '{value}'
                                WHERE variabel = '{variable}' AND ident = '{ident}' AND refnr = '{refnr}' AND {condition_str}
                            """
                            conn.raw_sql(query)
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
                            conn.raw_sql(query)
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

            elif isinstance(connection_object, EimerDBInstance):
                partition_args = dict(zip(self.time_units, args, strict=False))
                tables_editable_dict = {}
                data_dict = connection_object.tables

                for table, details in data_dict.items():
                    if table.startswith("skjemadata") and "schema" in details:
                        field_editable_dict = {
                            field["name"]: field.get("app_editable", False)
                            for field in details["schema"]
                        }
                        tables_editable_dict[table] = field_editable_dict

                table_editable_dict = tables_editable_dict[tabell]
                edited_column = edited[0]["colId"]

                schema = connection_object.tables[tabell]["schema"]
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
                        connection_object.query(
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
                raise TypeError(
                    f"Conection set by set_connection() is not a valid connection object. Is type: {type(connection_object)}"
                )
