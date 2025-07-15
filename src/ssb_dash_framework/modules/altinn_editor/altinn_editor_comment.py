import logging
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils import create_alert

logger = logging.getLogger(__name__)


class AltinnEditorComment:
    """Module for viewing and editing comments in the Altinn Editor."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor Comment module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
            AssertionError: If the connection object does not have a 'query' method.
        """
        assert hasattr(
            conn, "query"
        ), (  # Necessary because of mypy
            "The database object must have a 'query' method."
        )
        self.time_units = time_units
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.module_layout = self._create_layout()
        self.module_callbacks()

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

    def _create_layout(self) -> html.Div:
        """Creates the layout for the Altinn Editor Comment module."""
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label(
                            "Editeringskommentar",
                            className="mb-1",
                        ),
                        dbc.Button(
                            "Se kommentarer",
                            id="altinn-comment-button",
                            className="w-100",
                        ),
                    ]
                ),
                self.kommentarmodal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout for the Altinn Editor Comment module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Altinn Editor Comment module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-kommentarmodal", "is_open"),
            Input("altinn-comment-button", "n_clicks"),
            State("skjemadata-kommentarmodal", "is_open"),
        )
        def toggle_kommentarmodal(n_clicks: None | int, is_open: bool) -> bool:
            if n_clicks is None:
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("altinnedit-kommentarmodal-table1", "rowData"),
            Output("altinnedit-kommentarmodal-table1", "columnDefs"),
            Input("altinn-comment-button", "n_clicks"),
            State("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
        )
        def kommentar_table(
            n_clicks: None | int, skjema: str, ident: str
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            if n_clicks is None:
                raise PreventUpdate
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
        def comment_select(selected_row: list[dict[str, int | float | str]]) -> str:
            return selected_row[0]["kommentar"] if selected_row is not None else ""

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("skjemadata-kommentarmodal-savebutton", "n_clicks"),
            State("altinnedit-kommentarmodal-table1", "selectedRows"),
            State("skjemadata-kommentarmodal-aar-kommentar", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_kommentar(
            n_clicks: None | int,
            selected_row: list[dict[str, int | float | str]],
            kommentar: str,
            skjema: str,
            alert_store: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            if n_clicks and n_clicks > 0 and selected_row:
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
