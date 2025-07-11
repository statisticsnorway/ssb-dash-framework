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
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Skjemaversjon", className="card-title"),
                    dbc.Input(
                        id="altinnedit-skjemaversjon",
                        type="text",
                        className="mb-2",
                    ),
                    dbc.Button(
                        "Se alle",
                        id="altinnedit-skjemaversjon-button",
                        type="text",
                    ),
                ]
            ),
            className="mb-2",
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
