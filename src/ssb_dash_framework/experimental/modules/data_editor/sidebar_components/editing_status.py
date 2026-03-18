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

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.core_query_functions import create_filter_dict
from ssb_dash_framework.utils.core_query_functions import ibis_filter_with_dict

from .....utils.config_tools.connection import _get_connection_object
from .....utils.config_tools.connection import get_connection
from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_time_units
from .....utils.core_models import UpdateSkjemamottakAktiv
from .....utils.core_models import UpdateSkjemamottakStatus
from ..core import DataEditorHelperSidebar
import logging
from psycopg_pool import ConnectionPool


logger = logging.getLogger(__name__)

class DataEditorSidebarEditingStatus(DataEditorHelperSidebar):
    _id_number = 0

    def __init__(self, status_options=None) -> None:
        self.module_number = DataEditorSidebarEditingStatus._id_number
        self.module_name = self.__class__.__name__
        DataEditorSidebarEditingStatus._id_number += 1

        self.variableselector = VariableSelector(
            selected_inputs=[], selected_states=[get_ident(), *get_time_units().keys()]
        )

        self.status_options = status_options if status_options else [
            {"label": "Ubehandlet", "value": "UBEHANDLET"},
            {"label": "Under arbeid", "value": "UNDER_ARBEID"},
            {"label": "Ferdig", "value": "FERDIG"}
        ]

        self.module_callbacks()
        super().__init__()

    def _create_layout(self):
        form_selector = dbc.Modal(
            [
                dbc.ModalHeader("Innsendte skjemaer fra enheten"),
                dbc.ModalBody(
                    [
                        dag.AgGrid(
                            id=f"{self.module_name}-{self.module_number}-form-table"
                        )
                    ]
                ),
            ],
            id=f"{self.module_name}-{self.module_number}-form-table-modal",
            size="xl",
        )
        return html.Div(
            [
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
                                    )
                                ),
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Row("Aktiv"),
                                dbc.Row(
                                    dcc.Checklist(
                                        id=f"{self.module_name}-{self.module_number}-checkbox",
                                        options={"Aktiv": True},
                                    )
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        )

    def module_callbacks(self):
        @callback(
            Output(f"{self.module_name}-{self.module_number}-checkbox", "value"),
            Output(f"{self.module_name}-{self.module_number}-radioitems", "value"),
            Output(
                f"{self.module_name}-{self.module_number}-refnr-text-row", "children"
            ),
            Output("alert_store", "data", allow_duplicate=True),
            self.variableselector.get_input("refnr"),
            Input(f"{self.module_name}-{self.module_number}-checkbox", "value"),
            Input(f"{self.module_name}-{self.module_number}-radioitems", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def set_initial_values_and_update_status(
            refnr, aktiv_status, status_code, alert_store
        ):
            triggered_id = ctx.triggered_id
            refnr_input_id = self.variableselector.get_input("refnr").component_id

            if triggered_id == refnr_input_id:
                with get_connection() as conn:
                    t = conn.table("skjemamottak")
                    data = t.filter(_.refnr == refnr).to_pandas()
                return (
                    ["Aktiv"] if data["aktiv"].item() else [],
                    "Ferdig" if data["editert"].item() else "Ikke påbegynt",
                    f"Viser for {refnr}",
                    no_update,
                )

            if triggered_id == f"{self.module_name}-{self.module_number}-checkbox":
                update_to_apply = UpdateSkjemamottakAktiv(
                    refnr=refnr, value=True if aktiv_status else False
                )
            elif triggered_id == f"{self.module_name}-{self.module_number}-radioitems":
                update_to_apply = UpdateSkjemamottakStatus(
                    refnr=refnr, value=status_code
                )

            if isinstance(_get_connection_object(), EimerDBInstance):
                feedback = update_to_apply.update_eimer()
            elif isinstance(_get_connection_object(), ConnectionPool):
                logger.debug("Attempting to update using ibis logic.")
                feedback = update_to_apply.update_ibis()
            else:
                raise NotImplementedError(f"Connection of type '{type(_get_connection_object())}' is not implemented yet.")

            return no_update, no_update, no_update, [feedback, *alert_store]

        @callback(
            Output(f"{self.module_name}-{self.module_number}-form-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-form-table", "columnDefs"),
            Output(
                f"{self.module_name}-{self.module_number}-form-table-modal", "is_open"
            ),
            Input(f"{self.module_name}-{self.module_number}-button", "n_clicks"),
            self.variableselector.get_all_states(),
        )
        def view_refnrs_by_ident(click, *args):
            if ctx.triggered_id != f"{self.module_name}-{self.module_number}-button":
                raise PreventUpdate
            if isinstance(_get_connection_object(), EimerDBInstance):
                args_before_timeunits = 1
                N = len(get_time_units())
                args = list(args)
                args[args_before_timeunits : N + args_before_timeunits] = list(
                    map(int, args[args_before_timeunits : N + args_before_timeunits])
                )

            filterdict = create_filter_dict([get_ident(), *get_time_units()], [*args])
            with get_connection() as conn:
                t = conn.table("skjemamottak")
                data = t.filter(ibis_filter_with_dict(filterdict)).to_pandas()
            return data.to_dict("records"), [{"field": x} for x in data.columns], True
