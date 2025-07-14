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


class AltinnEditorUnitDetails:

    def __init__(
        self, time_units, conn, variable_connection, variable_selector_instance
    ):
        self.time_units = time_units
        self.conn = conn
        self.variable_connection = variable_connection
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.layout = self._create_layout()
        self.module_callbacks()

    def unit_details_modal(self):
        """Returns a modal component containing a table with enhetsinfo."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Enhetsinfo")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={"editable": True},
                        id="skjemadata-enhetsinfomodal-table1",
                        className="ag-theme-alpine-dark header-style-on-filter",
                    ),
                    className="d-flex flex-column justify-content-center align-items-center",
                ),
            ],
            id="skjemadata-enhetsinfomodal",
            is_open=False,
            size="xl",
        )

    def _create_layout(self):
        return html.Div(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Skjemaversjon", className="card-title"),
                            dbc.Input(
                                id="altinnedit-skjemaversjon",
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
                self.unit_details_modal(),
            ]
        )

    def module_callbacks(self):
        @callback(  # type: ignore[misc]
            Output("skjemadata-enhetsinfomodal-table1", "rowData"),
            Output("skjemadata-enhetsinfomodal-table1", "columnDefs"),
            Input("altinnedit-ident", "value"),
            self.variable_selector.get_inputs(),
        )
        def update_enhetsinfotabell(ident, *args):
            if ident is None or any(arg is None for arg in args):
                logger.debug(
                    f"update_enhetsinfotabell is lacking input, returning None. ident is {ident} Received args: %s",
                    args,
                )
                return None, None
            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"SELECT * FROM enhetsinfo WHERE ident = '{ident}'",
                    create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=None,
                        **partition_args,
                    ),
                )
                df.drop(columns=["row_id"], inplace=True)
                columns = [{"headerName": col, "field": col} for col in df.columns]
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(f"Error in update_enhetsinfotabell: {e}", exc_info=True)
                return None, None

        @callback(  # type: ignore[misc]
            Output("skjemadata-enhetsinfomodal", "is_open"),
            Input("altinnedit-enhetsinfo-button", "n_clicks"),
            State("skjemadata-enhetsinfomodal", "is_open"),
        )
        def toggle_enhetsinfomodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-sidebar-enhetsinfo", "children"),
            Input("skjemadata-enhetsinfomodal-table1", "rowData"),
        )
        def update_sidebar(enhetsinfo_rows):
            if not enhetsinfo_rows:
                return html.P("Ingen enhetsinfo tilgjengelig.")

            return [
                html.Div(
                    [html.Strong(row["variabel"] + ": "), html.Span(str(row["verdi"]))],
                    style={"margin-bottom": "5px"},
                )
                for row in enhetsinfo_rows
            ]

        for output_id, variable in self.variable_connection.items():

            @callback(  # type: ignore[misc]
                Output(output_id, "value", allow_duplicate=True),
                Input("skjemadata-enhetsinfomodal-table1", "rowData"),
                prevent_initial_call=True,
            )
            def update_variable(row_data, variable=variable):
                if row_data is None:
                    return ""
                for row in row_data:
                    if row.get("variabel") == variable:
                        return row.get("verdi", "")
                return ""
