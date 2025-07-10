import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


class AltinnEditorHistory:

    def __init__(self):
        self.layout = self._create_layout()
        self.module_callbacks()

    def open_button(self):
        return dbc.Button(
            "Historikk",
            id="altinn-history-button",
            className="altinn-editor-module-button",
        )

    def history_modal(self):
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Historikk")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={"editable": True},
                        id="skjemadata-historikkmodal-table1",
                        className="ag-theme-alpine-dark header-style-on-filter",
                    ),
                    className="d-flex flex-column justify-content-center align-items-center",
                ),
            ],
            id="skjemadata-historikkmodal",
            is_open=False,
            size="xl",
        )

    def _create_layout(self):
        return html.Div(
            [
                self.open_button(),
                self.history_modal(),
            ]
        )

    def module_callbacks(self):
        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal", "is_open"),
            Input("altinn-history-button", "n_clicks"),
            State("skjemadata-historikkmodal", "is_open"),
        )
        def toggle_historikkmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal-table1", "rowData"),
            Output("skjemadata-historikkmodal-table1", "columnDefs"),
            Input("skjemadata-historikkmodal", "is_open"),
            State("altinnedit-option1", "value"),
            State("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
        )
        def historikktabell(is_open, tabell, selected_row, skjema, *args):
            if is_open:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    skjemaversjon = selected_row[0]["skjemaversjon"]
                    df = self.conn.query_changes(
                        f"""SELECT * FROM {tabell}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        ORDER BY datetime DESC
                        """,
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    if df is None:
                        df = pd.DataFrame(columns=["ingen", "data"])
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
                except Exception as e:
                    logger.error(f"Error in historikktabell: {e}", exc_info=True)
                    return None, None
            else:
                raise PreventUpdate
