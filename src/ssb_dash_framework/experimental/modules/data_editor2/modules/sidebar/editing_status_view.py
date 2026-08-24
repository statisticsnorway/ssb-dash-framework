# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
import logging
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import callback_context as ctx
from dash import dcc
from dash import html
from dash import no_update
from dash.exceptions import PreventUpdate

from eimerdb import EimerDBInstance
from ibis import _
from psycopg_pool import ConnectionPool
import tzlocal
import time

from ssb_dash_framework import VariableSelector

from ......utils.config_tools.connection import _get_connection_object
from ......utils.config_tools.set_variables import get_ident
from ......utils.config_tools.set_variables import get_refnr
from ......utils.config_tools.set_variables import get_time_units
from ......utils.core_models import UpdateSkjemamottakAktiv
from ......utils.core_models import UpdateSkjemamottak
from .editing_sidebar_helper import DataEditorHelperSidebar

logger = logging.getLogger(__name__)

local_tz = tzlocal.get_localzone()


class DataEditorSidebarEditingStatus(DataEditorHelperSidebar):
    """A sidebar module for inspecting and updating the status of the selected form by 'refnr'.

    Contains functionality for:
    - Viewing all forms sent from the same 'ident'.
    - Setting its status. Whether the form is untouched, being processed or is reviewed.
    - Setting whether or not the form is 'active'. In the case of a single 'ident' sending more than one form, this module lets you set a specific 'refnr' as inactive.
    """

    _id_number = 0

    def __init__(self, status_options: list[dict[str, Any]] | None = None) -> None:
        """Initializes and registers the module.

        Args:
            status_options: What kinds of status codes can be set on a form. Defaults to:
                {"label": "Ubehandlet", "value": "UBEHANDLET"},
                {"label": "Under arbeid", "value": "UNDER_ARBEID"},
                {"label": "Ferdig", "value": "FERDIG"}
        """
        self.module_number = DataEditorSidebarEditingStatus._id_number
        self.module_name = self.__class__.__name__
        DataEditorSidebarEditingStatus._id_number += 1

        self.variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[
                get_ident(),
                get_time_units().name,
                "altinnskjema",
                get_refnr(),
            ],
        )

        self.status_options = (
            status_options
            if status_options
            else [
                {"label": "Ubehandlet", "value": "Ubehandlet"},
                {"label": "Under arbeid", "value": "Under arbeid"},
                {"label": "Ferdig", "value": "Ferdig"},
            ]
        )

        self.module_callbacks()
        super().__init__()

    def _create_layout(self) -> html.Div:
        form_selector = dbc.Modal(
            [
                dbc.ModalHeader("Innsendte skjemaer fra enheten"),
                dbc.ModalBody(
                    [
                        dag.AgGrid(
                            id=f"{self.module_name}-{self.module_number}-form-table",
                            className="ag-theme-alpine ag-theme-ssb mb-2",
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={"rowSelection": "single"},
                        )
                    ]
                ),
            ],
            id=f"{self.module_name}-{self.module_number}-form-table-modal",
            size="xl",
        )
        return html.Div(
            [
                dcc.Store(id="skjemamottak-status-signal"),
                form_selector,
                dbc.Row("Editeringsstatus"),
                dbc.Row(
                    "Viser skjema:",
                    id=f"{self.module_name}-{self.module_number}-refnr-text-row",
                ),
                dbc.Row(
                    dbc.Button(
                        id=f"{self.module_name}-{self.module_number}-button",
                        children="Se innsendinger",
                        className="ssb-btn primary-btn",
                    )
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Row("Status"),
                                dbc.Row(
                                    dcc.RadioItems(
                                        id=f"{self.module_name}-{self.module_number}-radioitems",
                                        options=self.status_options,
                                        className="ssb-radio-buttons",
                                    )
                                ),
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Row("Aktiv"),
                                dbc.Row(
                                    html.Div(
                                        className="ssb-checkbox d-flex align-items-center",
                                        children=[
                                            dcc.Checklist(
                                                id=f"{self.module_name}-{self.module_number}-checkbox",
                                                options=[
                                                    {"label": "", "value": "Aktiv"}
                                                ],
                                            ),
                                            html.Label("Ja", className="mb-1 ms-2"),
                                        ],
                                    )
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        )

    def module_callbacks(self) -> None:
        """Registers the callbacks for the module."""

        @callback(
            Output(f"{self.module_name}-{self.module_number}-checkbox", "value"),
            Output(f"{self.module_name}-{self.module_number}-radioitems", "value"),
            Output(
                f"{self.module_name}-{self.module_number}-refnr-text-row", "children"
            ),
            self.variableselector.get_input(get_refnr()),
            Input("skjemamottak-status-signal", "data"),
            State(f"{self.module_name}-{self.module_number}-checkbox", "value"),
            State(f"{self.module_name}-{self.module_number}-radioitems", "value"),
        )
        def set_initial_status(refnr, status_signal, current_checkbox, current_radio):

            if not refnr:
                raise PreventUpdate

            data = self.fetcher.get_form_status(refnr)
            if data is None:
                raise PreventUpdate

            new_checkbox = ["Aktiv"] if data.active else []
            new_radio = data.status

            checkbox_out = (
                new_checkbox if new_checkbox != current_checkbox else no_update
            )
            radio_out = new_radio if new_radio != current_radio else no_update

            return (
                checkbox_out,
                radio_out,
                f"Viser skjema: {refnr}",
            )

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("skjemamottak-status-signal", "data", allow_duplicate=True),
            Input(f"{self.module_name}-{self.module_number}-checkbox", "value"),
            Input(f"{self.module_name}-{self.module_number}-radioitems", "value"),
            self.variableselector.get_state(get_refnr()),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_status(
            aktiv_status,
            status_code,
            refnr,
            alert_store,
        ):

            triggered_id = ctx.triggered_id

            if triggered_id == f"{self.module_name}-{self.module_number}-checkbox":

                update_to_apply = UpdateSkjemamottakAktiv(
                    refnr=refnr, value=bool(aktiv_status)
                )

            elif triggered_id == f"{self.module_name}-{self.module_number}-radioitems":

                update_to_apply = UpdateSkjemamottak(
                    refnr=refnr,
                    column="status",
                    value=status_code,
                )

            else:
                raise PreventUpdate

            if isinstance(_get_connection_object(), EimerDBInstance):
                feedback = update_to_apply.update_eimer()

            elif isinstance(_get_connection_object(), ConnectionPool):
                feedback = update_to_apply.update_ibis()

            else:
                raise NotImplementedError

            return [feedback, *alert_store], time.time()

        @callback(
            Output(f"{self.module_name}-{self.module_number}-form-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-form-table", "columnDefs"),
            Output(
                f"{self.module_name}-{self.module_number}-form-table-modal", "is_open"
            ),
            inputs = {
                "click": Input(f"{self.module_name}-{self.module_number}-button", "n_clicks"),
                "ident": self.variableselector.get_state(get_ident()),
                "time_units": self.variableselector.get_state(get_time_units().name)
            }
        )
        def view_refnrs_by_ident(click: int | None, ident: str | None, time_units: str):
            """Populates a table showing all relevant received forms from the relevant 'ident'."""
            if ctx.triggered_id != f"{self.module_name}-{self.module_number}-button":
                raise PreventUpdate
            
            if ident is None:
                raise PreventUpdate
                
            data = self.fetcher.get_refnrs_by_period_ident(self.settings, ident, time_units)

            if data is None:
                raise PreventUpdate

            return (
                data.to_dict("records"),
                [{"field": x, "headerName": x} for x in data.columns],
                True,
            )
            
            

        @callback(
            self.variableselector.get_output_object(get_refnr()),  # oppdater refnr
            self.variableselector.get_output_object(
                "altinnskjema"
            ),  # oppdater altinnskjema
            Input(
                f"{self.module_name}-{self.module_number}-form-table", "selectedRows"
            ),
            self.variableselector.get_input(get_refnr()),
            self.variableselector.get_input("altinnskjema"),
            prevent_initial_call=True,
        )
        def selected_refnr(
            selected_row: list[dict[str, Any]], current_refnr, current_altinnskjema
        ):

            logger.debug(f"Args:\nselected_row: {selected_row}")
            if not selected_row:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate

            refnr = selected_row[0]["refnr"]
            skjema = selected_row[0]["skjema"]

            return (
                refnr if refnr != current_refnr else no_update,
                skjema if skjema != current_altinnskjema else no_update,
            )
