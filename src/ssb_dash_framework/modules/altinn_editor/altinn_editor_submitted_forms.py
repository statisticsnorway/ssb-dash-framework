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
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorSubmittedForms:
    """Module for viewing and selecting between submitted forms, and choose if they are active and/or checked."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor submitted forms module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

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
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self._is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _is_valid(self) -> None:
        VariableSelector([], []).get_option("refnr")

    def _create_layout(self) -> html.Div:
        """Creates the module layout."""
        return html.Div(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("skjemaer", className="card-title"),
                            dcc.Dropdown(id="altinnedit-skjemaer"),
                        ]
                    ),
                    className="mb-2",
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("refnr", className="card-title"),
                            dbc.Input(
                                id="altinnedit-refnr",
                                type="text",
                            ),
                            dbc.Button(
                                "Se alle",
                                id="altinnedit-refnr-button",
                                type="text",
                            ),
                        ],
                    ),
                    className="mb-2",
                ),
                self.submitted_forms_modal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the module layout."""
        return self.module_layout

    def submitted_forms_modal(self) -> dbc.Modal:
        """Returns a modal component with a table containing all the skjema versions."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("refnrer")),
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
                        className="ag-theme-alpine header-style-on-filter",
                    ),
                ),
            ],
            id="skjemadata-refnrsmodal",
            is_open=False,
            size="xl",
        )

    def module_callbacks(self) -> None:
        """Defines the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-refnrsmodal", "is_open"),
            Input("altinnedit-refnr-button", "n_clicks"),
            State("skjemadata-refnrsmodal", "is_open"),
        )
        def toggle_refnrsmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaer", "options"),
            Output("altinnedit-skjemaer", "value"),
            Input("altinnedit-ident", "value"),
            self.variableselector.get_all_inputs(),
        )
        def update_skjemaer(
            ident: str, *args: Any
        ) -> tuple[list[dict[str, str]], str | None]:
            logger.debug(f"Args:\nident: {ident}\nargs: {args}")
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
                )["skjema"][0]

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
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            self.variableselector.get_all_states(),
            prevent_initial_call=True,
        )
        def set_skjema_to_edited(
            edited: list[dict[str, Any]],
            skjema: str,
            alert_store: list[dict[str, Any]],
            *args: Any,
        ) -> list[dict[str, Any]] | None:
            logger.debug(
                f"Args:\n"
                f"edited: {edited}\n"
                f"skjema: {skjema}\n"
                f"alert_store: {alert_store}\n"
                f"args: {args}"
            )
            if edited is None or skjema is None or any(arg is None for arg in args):
                return None

            partition_args = dict(zip(self.time_units, args, strict=False))
            variabel = edited[0]["colId"]
            new_value = edited[0]["value"]
            refnr = edited[0]["data"]["refnr"]

            if variabel == "editert":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET editert = {new_value}
                        WHERE refnr = '{refnr}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    return [
                        create_alert(
                            f"Skjema {refnr} sin editeringsstatus er satt til {new_value}.",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception:
                    return [
                        create_alert(
                            "En feil skjedde under oppdatering av editeringsstatusen",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
            elif variabel == "aktiv":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET aktiv = {new_value}
                        WHERE refnr = '{refnr}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    return [
                        create_alert(
                            f"Skjema {refnr} sin aktivstatus er satt til {new_value}.",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception:
                    return [
                        create_alert(
                            "En feil skjedde under oppdatering av aktivstatusen",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
            else:
                logger.debug(f"Tried to edit {variabel}, preventing update.")
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "rowData"),
            Output("altinnedit-table-skjemaer", "columnDefs"),
            Input("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
            self.variableselector.get_all_states(),
        )
        def update_sidebar_table(
            skjema: str, ident: str, *args: Any
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
            logger.debug(f"Args:\nskjema: {skjema}\nident: {ident}\nargs: {args}")
            if skjema is None or ident is None or any(arg is None for arg in args):
                return None, None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"""SELECT refnr, dato_mottatt, editert, aktiv
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
        def hovedside_update_valgt_rad(
            rows: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            logger.debug(f"Args:\nrows: {rows}")
            if not rows:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate

            selected_row = rows[0]
            return [selected_row]

        @callback(  # type: ignore[misc]
            Output("altinnedit-refnr", "value"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
        )
        def selected_refnr(selected_row: list[dict[str, Any]]) -> str:
            logger.debug(f"Args:\nselected_row: {selected_row}")
            if not selected_row:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate

            refnr = selected_row[0]["refnr"]
            return str(refnr)
