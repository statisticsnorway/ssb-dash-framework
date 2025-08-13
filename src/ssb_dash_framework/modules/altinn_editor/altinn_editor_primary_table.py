import logging
from typing import Any

import dash_ag_grid as dag
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

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
        self.time_units = time_units
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        assert hasattr(
            conn, "tables"
        ), "The database object must have a 'tables' attribute."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.module_layout = self._create_layout()
        self.module_callbacks()

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
                    className="ag-theme-alpine-dark header-style-on-filter",
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
            Input("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
        )
        def hovedside_update_altinnskjema(
            skjemaversjon: str, tabell: str, skjema: str, *args: Any
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
            logger.debug(
                f"Args:\n"
                f"skjemaversjon: {skjemaversjon}\n"
                f"tabell: {tabell}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )
            schema = self.conn.tables[tabell]["schema"]
            columns = {field["name"] for field in schema}
            if "variabel" in columns and "verdi" in columns:
                long_format = True
            else:
                long_format = False

            if (
                skjemaversjon is None
                or tabell is None
                or skjema is None
                or any(arg is None for arg in args)
            ):
                return None, None
            if long_format:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    df = self.conn.query(
                        f"""
                        SELECT t.*, subquery.radnr
                        FROM {tabell} AS t
                        JOIN (
                            SELECT aar, radnr, tabell, variabel
                            FROM datatyper
                        ) AS subquery
                        ON subquery.aar = t.aar AND subquery.variabel = t.variabel
                        WHERE t.skjemaversjon = '{skjemaversjon}'
                        AND subquery.tabell = '{tabell}'
                        ORDER BY subquery.radnr ASC
                        """,
                        partition_select={
                            tabell: create_partition_select(
                                desired_partitions=self.time_units,
                                skjema=skjema,
                                **partition_args,
                            ),
                            "datatyper": create_partition_select(
                                desired_partitions=self.time_units,
                                skjema=None,
                                **partition_args,
                            ),
                        },
                    )
                    df.drop(columns=["radnr"], inplace=True)
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
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    df = self.conn.query(
                        f"""
                        SELECT * FROM {tabell}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
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
                        f"Error in hovedside_update_altinnskjema (non-long format): {e}",
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
            if row_data is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            return str(row_data[click["rowIndex"]]["variabel"])

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemadata", "cellValueChanged"),
            State("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            self.variable_selector.get_states(),
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
            if edited is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            else:
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
