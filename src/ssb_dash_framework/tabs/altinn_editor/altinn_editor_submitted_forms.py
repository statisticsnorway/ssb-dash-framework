import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorSubmittedForms:

    def __init__(self, time_units, conn, variable_selector_instance):
        self.time_units = time_units
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self._is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _is_valid(self):
        VariableSelector([], []).get_option("skjemaversjon")

    def _create_layout(self):
        return html.Div(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Skjemaversjon", className="card-title"),
                            dbc.Input(
                                id="altinnedit-skjemaer",
                                type="text",
                            ),
                            dbc.Button(
                                "Se alle",
                                id="altinnedit-skjemaversjon-button",
                                type="text",
                            ),
                        ],
                    ),
                    className="mb-2",
                ),
                self.submitted_forms_modal(),
            ]
        )

    def layout(self):
        return self.module_layout

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
            Output("altinnedit-skjemaer", "options"),
            Output("altinnedit-skjemaer", "value"),
            Input("altinnedit-ident", "value"),
            self.variable_selector.get_inputs(),
        )
        def update_skjemaer(ident, *args):
            if ident is None or any(arg is None for arg in args):
                return [], None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                skjemaer = self.conn.query(
                    f"SELECT * FROM enheter WHERE ident = '{ident}'",
                    create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=None,
                        **partition_args,
                    ),
                )["skjemaer"][0]

                skjemaer = [item.strip() for item in skjemaer.split(",")]
                skjemaer_dd_options = [
                    {"label": item, "value": item} for item in skjemaer
                ]
                options = skjemaer_dd_options
                value = skjemaer_dd_options[0]["value"]
                return options, value
            except Exception as e:
                logger.error(f"Error in update_skjemaer: {e}", exc_info=True)
                return [], None

        @callback(  # type: ignore[misc]
            Output(
                "skjemadata-hovedtabell-updatestatus", "children", allow_duplicate=True
            ),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
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
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
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
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
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
            self.variable_selector.get_states(),
        )
        def update_sidebar_table(skjema, ident, *args):
            logger.debug(f"Inputs. Skjema: {skjema}, Ident: {ident}, Args: {args}")
            if skjema is None or ident is None or any(arg is None for arg in args):
                return None, None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"""SELECT skjemaversjon, dato_mottatt, editert, aktiv
                    FROM skjemamottak WHERE ident = '{ident}' AND aktiv = True
                    ORDER BY dato_mottatt DESC""",
                    create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=skjema,
                        **partition_args,
                    ),
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
