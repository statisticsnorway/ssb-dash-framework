import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

logger = logging.getLogger(__name__)


class AltinnEditorSubmittedForms:

    def __init__(self):
        self.layout = self._create_layout()
        self.module_callbacks()

    def open_button(self):
        return dbc.Button(
            "Historikk",
            id="altinn-history-button",
            className="altinn-editor-module-button",
        )

    def submitted_forms_modal(self) -> dbc.Modal:
        """Returns a modal component with a table containing all the skjema versions."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Skjemaversjoner")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={
                            "resizable": True,
                            "sortable": True,
                            "floatingFilter": True,
                            "filter": "agTextColumnFilter",
                        },
                        id="altinnedit-table-skjemaer",
                        dashGridOptions={"rowSelection": "single"},
                        columnSize="responsiveSizeToFit",
                        className="ag-theme-alpine-dark header-style-on-filter",
                    ),
                ),
            ],
            id="skjemadata-skjemaversjonsmodal",
            is_open=False,
            size="xl",
        )

    def module_callbacks(self):
        @callback(  # type: ignore[misc]
            Output("skjemadata-skjemaversjonsmodal", "is_open"),
            Input("altinnedit-skjemaversjon-button", "n_clicks"),
            State("skjemadata-skjemaversjonsmodal", "is_open"),
        )
        def toggle_skjemaversjonsmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-hjelpetabellmodal-table1", "rowData"),
            Output("skjemadata-hjelpetabellmodal-table1", "columnDefs"),
            Input("skjemadata-hjelpetabellmodal-tabs", "active_tab"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            Input("skjemadata-hjelpetablellmodal-dd", "value"),
            State("altinnedit-option1", "value"),
            State("altinnedit-ident", "value"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def hjelpetabeller(
            tab, selected_row, rullerende_var, tabell, ident, skjema, *args
        ):
            if tab == "modal-hjelpetabeller-tab1":
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    partition_select = self.create_partition_select(
                        skjema=skjema, **partition_args
                    )
                    partition_select_no_skjema = self.create_partition_select(
                        skjema=None, **partition_args
                    )
                    updated_partition_select = self.update_partition_select(
                        partition_select, rullerende_var
                    )
                    skjemaversjon = selected_row[0]["skjemaversjon"]
                    column_name_expr_outer = SQL_COLUMN_CONCAT.join(
                        [f"s.{unit}" for unit in self.time_units]
                    )
                    column_name_expr_inner = SQL_COLUMN_CONCAT.join(
                        [f"t2.{unit}" for unit in self.time_units]
                    )

                    group_by_clause = ", ".join(
                        [f"s.{unit}" for unit in self.time_units]
                    )

                    query = f"""
                        SELECT
                            s.variabel,
                            {column_name_expr_outer} AS time_combination,
                            SUM(CAST(s.verdi AS NUMERIC)) AS verdi
                        FROM {tabell} AS s
                        JOIN (
                            SELECT
                                {column_name_expr_inner} AS time_combination,
                                t2.ident,
                                t2.skjemaversjon,
                                t2.dato_mottatt
                            FROM
                                skjemamottak AS t2
                            WHERE aktiv = True
                            QUALIFY
                                ROW_NUMBER() OVER (PARTITION BY time_combination, t2.ident ORDER BY t2.dato_mottatt DESC) = 1
                        ) AS mottak_subquery ON
                            {column_name_expr_outer} = mottak_subquery.time_combination
                            AND s.ident = mottak_subquery.ident
                            AND s.skjemaversjon = mottak_subquery.skjemaversjon
                        JOIN (
                        SELECT * FROM datatyper AS d
                        ) AS subquery ON s.variabel = subquery.variabel
                        WHERE s.ident = '{ident}' AND subquery.datatype = 'int'
                        GROUP BY s.variabel, subquery.radnr, {group_by_clause}
                        ORDER BY subquery.radnr
                        ;
                    """

                    df = self.conn.query(
                        query.format(ident=ident),
                        partition_select={
                            tabell: updated_partition_select,
                            "datatyper": partition_select_no_skjema,
                        },
                    )

                    df_wide = df.pivot(
                        index="variabel", columns="time_combination", values="verdi"
                    ).reset_index()

                    df_wide = df_wide.rename(
                        columns={
                            col: f"verdi_{col}" if col != "variabel" else col
                            for col in df_wide.columns
                        }
                    )

                    df_wide.columns.name = None

                    def extract_numeric_sum(col_name):
                        numbers = list(map(int, re.findall(r"\d+", col_name)))
                        return sum(numbers) if numbers else 0

                    time_columns_sorted = sorted(
                        [col for col in df_wide.columns if col.startswith("verdi_")],
                        key=extract_numeric_sum,
                    )

                    if len(time_columns_sorted) >= 2:
                        latest_col = max(time_columns_sorted, key=extract_numeric_sum)
                        prev_col = min(time_columns_sorted, key=extract_numeric_sum)
                        df_wide["diff"] = df_wide[latest_col] - df_wide[prev_col]
                        df_wide["pdiff"] = (df_wide["diff"] / df_wide[prev_col]) * 100
                        df_wide["pdiff"] = df_wide["pdiff"].round(2).astype(str) + " %"
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                        }
                        for col in df_wide.columns
                    ]
                    return df_wide.to_dict("records"), columns
                except Exception as e:
                    logger.error(f"Error in hjelpetabeller: {e}", exc_info=True)
                    return None, None

        @callback(  # type: ignore[misc]
            Output(
                "skjemadata-hovedtabell-updatestatus", "children", allow_duplicate=True
            ),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def set_skjema_to_edited(edited, skjema, *args):
            if edited is None or skjema is None or any(arg is None for arg in args):
                return None

            partition_args = dict(zip(self.time_units, args, strict=False))
            variabel = edited[0]["colId"]
            old_value = edited[0]["oldValue"]
            new_value = edited[0]["value"]
            skjemaversjon = edited[0]["data"]["skjemaversjon"]

            if variabel == "editert":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET editert = {new_value}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    return f"Skjema {skjemaversjon} sin editeringsstatus er satt til {new_value}."
                except Exception:
                    return "En feil skjedde under oppdatering av editeringsstatusen"
            elif variabel == "aktiv":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET aktiv = {new_value}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    return f"Skjema {skjemaversjon} sin aktivstatus er satt til {new_value}."
                except Exception:
                    return "En feil skjedde under oppdatering av editeringsstatusen"

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "rowData"),
            Output("altinnedit-table-skjemaer", "columnDefs"),
            Input("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
            *self.create_callback_components("State"),
        )
        def update_sidebar_table(skjema, ident, *args):
            if skjema is None or ident is None or any(arg is None for arg in args):
                return None, None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"""SELECT skjemaversjon, dato_mottatt, editert, aktiv
                    FROM skjemamottak WHERE ident = '{ident}' AND aktiv = True
                    ORDER BY dato_mottatt DESC""",
                    self.create_partition_select(skjema=skjema, **partition_args),
                )
                columns = [
                    (
                        {"headerName": col, "field": col, "editable": True}
                        if col in ["editert", "aktiv"]
                        else {"headerName": col, "field": col}
                    )
                    for col in df.columns
                ]
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(f"Error in update_sidebar_table: {e}", exc_info=True)
                return None, None

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "selectedRows"),
            Input("altinnedit-table-skjemaer", "rowData"),
            prevent_initial_call=True,
        )
        def hovedside_update_valgt_rad(rows):
            if not rows:
                return None

            selected_row = rows[0]
            return [selected_row]

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
        )
        def selected_skjemaversjon(selected_row):
            if not selected_row:
                return None

            skjemaversjon = selected_row[0]["skjemaversjon"]
            return skjemaversjon
