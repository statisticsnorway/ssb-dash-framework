import logging
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorHistory:
    """Module for viewing the editing history for the selected observation."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor History module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query_changes' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
            AssertionError: If the connection object does not have a 'query_changes' method.
        """
        assert hasattr(
            conn, "query_changes"
        ), "The database object must have a 'query_changes' method."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.time_units = time_units
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def history_modal(self) -> dbc.Modal:
        """Creates the history modal."""
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

    def _create_layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label(
                            "Historikk",
                            className="mb-1",
                        ),
                        dbc.Button(
                            "Se historikk",
                            id="altinn-history-button",
                            className="w-100",
                        ),
                    ]
                ),
                self.history_modal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Defines callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal", "is_open"),
            Input("altinn-history-button", "n_clicks"),
            State("skjemadata-historikkmodal", "is_open"),
        )
        def toggle_historikkmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal-table1", "rowData"),
            Output("skjemadata-historikkmodal-table1", "columnDefs"),
            Input("skjemadata-historikkmodal", "is_open"),
            State("altinnedit-option1", "value"),
            State("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
        )
        def historikktabell(
            is_open: bool,
            tabell: str,
            selected_row: list[dict[str, int | float | str]],
            skjema: str,
            *args: Any,
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, str | bool]] | None]:
            logger.debug(
                f"Args:\n"
                f"is_open: {is_open}\n"
                f"tabell: {tabell}\n"
                f"selected_row: {selected_row}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )
            if is_open:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    refnr = selected_row[0]["refnr"]
                    df = self.conn.query_changes(
                        f"""SELECT * FROM {tabell}
                        WHERE refnr = '{refnr}'
                        ORDER BY datetime DESC
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
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
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
