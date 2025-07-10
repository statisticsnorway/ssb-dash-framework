import logging

from dash import callback
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from ...utils import create_alert

logger = logging.getLogger(__name__)

class AltinnEditorComment:

    def __init__(self, conn):
        self.conn = conn
        self.layout = self._create_layout()
        self.module_callbacks()

    def open_button(self):
        return dbc.Button(
            "Editeringskommentarer",
            id="altinn-comment-button",
            className="altinn-editor-module-button",
        )

    def kommentarmodal(self) -> dbc.Modal:
        """Returns a modal component containing editing comments."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Kommentarer")),
                dbc.ModalBody(
                    [
                        dbc.Row(
                            dag.AgGrid(
                                defaultColDef={
                                    "resizable": True,
                                    "sortable": True,
                                    "floatingFilter": True,
                                    "filter": "agTextColumnFilter",
                                },
                                id="altinnedit-kommentarmodal-table1",
                                dashGridOptions={"rowSelection": "single"},
                                columnSize="responsiveSizeToFit",
                                className="ag-theme-alpine-dark header-style-on-filter",
                            )
                        ),
                        dbc.Row(
                            [
                                dbc.Col(html.P(id="skjemadata-kommentarmodal-aar-p")),
                                dbc.Col(
                                    html.P(id="skjemadata-kommentarmodal-updatestatus")
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Lagre kommentar",
                                        id="skjemadata-kommentarmodal-savebutton",
                                    )
                                ),
                            ]
                        ),
                        dbc.Row(
                            dcc.Textarea(
                                id="skjemadata-kommentarmodal-aar-kommentar",
                                style={"width": "100%", "height": 300},
                            )
                        ),
                    ]
                ),
            ],
            id="skjemadata-kommentarmodal",
            is_open=False,
            size="xl",
        )
    
    def _create_layout(self):
        """Creates the layout for the Altinn Editor Comment module."""
        return html.Div(
            [
                self.open_button(),
                self.kommentarmodal(),
            ]
        )

    def module_callbacks(self):
            @callback(  # type: ignore[misc]
            Output("skjemadata-kommentarmodal", "is_open"),
            Input("altinnedit-option6", "n_clicks"),
            State("skjemadata-kommentarmodal", "is_open"),
        )
        def toggle_kommentarmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("altinnedit-kommentarmodal-table1", "rowData"),
            Output("altinnedit-kommentarmodal-table1", "columnDefs"),
            Input("altinnedit-option6", "n_clicks"),
            State("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
        )
        def kommentar_table(n_clicks, skjema, ident):
            if n_clicks is None:
                return no_update
            df = self.conn.query(
                f"SELECT * FROM skjemamottak WHERE ident = '{ident}'",
                partition_select={"skjema": [skjema]},
            )
            columns = [
                {
                    "headerName": col,
                    "field": col,
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output("skjemadata-kommentarmodal-aar-kommentar", "value"),
            Input("altinnedit-kommentarmodal-table1", "selectedRows"),
        )
        def comment_select(selected_row):
            if selected_row is not None:
                kommentar = selected_row[0]["kommentar"]
            else:
                kommentar = ""
            return kommentar

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("skjemadata-kommentarmodal-savebutton", "n_clicks"),
            State("altinnedit-kommentarmodal-table1", "selectedRows"),
            State("skjemadata-kommentarmodal-aar-kommentar", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_kommentar(n_clicks, selected_row, kommentar, skjema, alert_store):
            if n_clicks > 0 and selected_row is not None:
                try:
                    row_id = selected_row[0]["row_id"]
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET kommentar = '{kommentar}'
                        WHERE row_id = '{row_id}'
                        """,
                        partition_select={"skjema": [skjema]},
                    )
                    alert_store = [
                        create_alert(
                            "Kommentarfeltet er oppdatert!",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception as e:
                    alert_store = [
                        create_alert(
                            f"Oppdatering av kommentarfeltet feilet. {str(e)[:60]}",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                return alert_store
