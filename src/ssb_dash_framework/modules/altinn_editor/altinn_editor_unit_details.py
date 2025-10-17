import logging
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorUnitDetails:
    """Module for viewing details about the selected unit."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
        variable_connection: dict[str, str],
    ) -> None:
        """Initializes the Altinn Editor Unit Details module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.
            variable_connection (dict[str, str]): Dict containing the name of characteristics from the dataset as keys and the variable selector name associated with it as value.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
            AssertionError: If the connection object does not have a 'query' method.
        """
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variableselector = variable_selector_instance
        self.variable_connection = variable_connection
        self.time_units = [self.variableselector.get_option(x).id for x in time_units]
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def unit_details_modal(self) -> dbc.Modal:
        """Returns a modal component containing a table with enhetsinfo."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Enhetsinfo")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={"editable": True},
                        id="skjemadata-enhetsinfomodal-table1",
                        className="ag-theme-alpine header-style-on-filter",
                    ),
                    className="d-flex flex-column justify-content-center align-items-center",
                ),
            ],
            id="skjemadata-enhetsinfomodal",
            is_open=False,
            size="xl",
        )

    def _create_layout(self) -> html.Div:
        """Creates the layout of the module."""
        return html.Div(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Enhetsinfo", className="card-title"),
                            dbc.Button(
                                "Se alle",
                                id="altinnedit-enhetsinfo-button",
                                type="text",
                            ),
                        ],
                    ),
                    className="mb-2",
                ),
                html.Div(id="skjemadata-sidebar-enhetsinfo"),
                self.unit_details_modal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-enhetsinfomodal-table1", "rowData"),
            Output("skjemadata-enhetsinfomodal-table1", "columnDefs"),
            Input("altinnedit-ident", "value"),
            self.variableselector.get_all_inputs(),
        )
        def update_enhetsinfotabell(
            ident: str, *args: Any
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, str | bool]] | None]:
            logger.debug(f"Args:\nident: {ident}\nargs: {args}")
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
        def toggle_enhetsinfomodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-sidebar-enhetsinfo", "children"),
            Input("skjemadata-enhetsinfomodal-table1", "rowData"),
        )
        def update_sidebar(
            enhetsinfo_rows: list[dict[str, Any]],
        ) -> list[html.Div] | html.P:  # TODO: Reduce amount of information sent here
            logger.debug(f"Args:\nenhetsinfo_rows: {enhetsinfo_rows}")
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
            def update_variable(
                row_data: list[dict[str, Any]], variable: str = variable
            ) -> str:
                logger.debug(f"Args:\nrow_data: {row_data}\nvariable: {variable}")
                for row in row_data:
                    if row.get("variabel") == variable:
                        return str(row.get("verdi", ""))
                logger.info(
                    f"Variable '{variable}' not found in row data, returning empty string."
                )
                return ""
