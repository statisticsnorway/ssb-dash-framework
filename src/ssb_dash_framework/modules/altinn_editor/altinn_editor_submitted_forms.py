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
        self.time_units = time_units
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self._is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _is_valid(self) -> None:
        VariableSelector([], []).get_option("skjemaversjon")

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

    def module_callbacks(self) -> None:
        """Defines the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-skjemaversjonsmodal", "is_open"),
            Input("altinnedit-skjemaversjon-button", "n_clicks"),
            State("skjemadata-skjemaversjonsmodal", "is_open"),
        )
        def toggle_skjemaversjonsmodal(n_clicks: None | int, is_open: bool) -> bool:
            if n_clicks is None:
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaer", "options"),
            Output("altinnedit-skjemaer", "value"),
            Input("altinnedit-ident", "value"),
            self.variable_selector.get_inputs(),
        )
        def update_skjemaer(
            ident: str, *args: Any
        ) -> tuple[list[dict[str, str]], str | None]:
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
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            self.variable_selector.get_states(),
            prevent_initial_call=True,
        )
        def set_skjema_to_edited(
            edited: list[dict[str, Any]],
            skjema: str,
            alert_store: list[dict[str, Any]],
            *args: Any,
        ) -> list[dict[str, Any]] | None:
            if edited is None or skjema is None or any(arg is None for arg in args):
                return None

            partition_args = dict(zip(self.time_units, args, strict=False))
            variabel = edited[0]["colId"]
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
                    return [
                        create_alert(
                            f"Skjema {skjemaversjon} sin editeringsstatus er satt til {new_value}.",
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
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    return [
                        create_alert(
                            f"Skjema {skjemaversjon} sin aktivstatus er satt til {new_value}.",
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
                logging.debug(f"Tried to edit {variabel}, preventing update.")
                raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "rowData"),
            Output("altinnedit-table-skjemaer", "columnDefs"),
            Input("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
            self.variable_selector.get_states(),
        )
        def update_sidebar_table(
            skjema: str, ident: str, *args: Any
        ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
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
        def hovedside_update_valgt_rad(
            rows: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            if not rows:
                raise PreventUpdate

            selected_row = rows[0]
            return [selected_row]

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
        )
        def selected_skjemaversjon(selected_row: list[dict[str, Any]]) -> str:
            if not selected_row:
                raise PreventUpdate

            skjemaversjon = selected_row[0]["skjemaversjon"]
            return str(skjemaversjon)
