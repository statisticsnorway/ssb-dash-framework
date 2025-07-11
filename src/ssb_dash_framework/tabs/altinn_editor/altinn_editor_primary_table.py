import logging

import dash_ag_grid as dag
from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils.alert_handler import create_alert
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorPrimaryTable:

    def __init__(self, time_units, conn, variable_selector_instance) -> None:
        self.time_units = time_units
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _create_layout(self):
        return html.Div(
            id="altinn-editor-primary-table",
            style={
                "height": "100%",
                "width": "100%",
            },
            children=[
                
                dag.AgGrid(
                    id="altinnedit-table-skjemadata",
                    className="ag-theme-alpine-dark header-style-on-filter",
                    style={"width": "100%", "height": "90%"},
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

    def layout(self):
        return self.module_layout

    def module_callbacks(self):
        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemadata", "rowData"),
            Output("altinnedit-table-skjemadata", "columnDefs"),
            Input("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
        )
        def hovedside_update_altinnskjema(skjemaversjon, tabell, skjema, *args):
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
            if long_format == True:
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
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                            "flex": 2 if col == "variabel" else 1,
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
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
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
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
        def select_variabel(click, row_data):
            if row_data is None:
                return no_update
            return row_data[click["rowIndex"]]["variabel"]

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemadata", "cellValueChanged"),
            State("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            self.variable_selector.get_states(),
            prevent_initial_call=True,
        )
        def update_table(edited, tabell, skjema, alert_store, *args):
            if edited is None:
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

                if table_editable_dict[edited_column] == True:
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
                        if long_format == True:
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
                    return f"Kolonnen {edited_column} kan ikke editeres!"
