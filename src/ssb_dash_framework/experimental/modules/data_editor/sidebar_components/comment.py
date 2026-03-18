import logging

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import callback_context
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from eimerdb import EimerDBInstance
from ibis import _

from ssb_dash_framework import VariableSelector
from ssb_dash_framework import _get_connection_object
from ssb_dash_framework import get_connection
from ssb_dash_framework.utils.core_query_functions import create_filter_dict
from ssb_dash_framework.utils.core_query_functions import ibis_filter_with_dict

from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_time_units
from .....utils.core_models import UpdateSkjemamottakKommentar
from ..core import DataEditorHelperSidebar
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


class DataEditorSidebarComment(DataEditorHelperSidebar):
    _id_number = 0

    def __init__(self) -> None:
        self.module_number = DataEditorSidebarComment._id_number
        self.module_name = self.__class__.__name__
        DataEditorSidebarComment._id_number += 1

        self.variableselector = VariableSelector(
            selected_inputs=[get_ident(), *get_time_units().keys()], selected_states=[]
        )
        self.module_callbacks()

        super().__init__()

    def _create_layout(self):
        return html.Div(
            [
                dbc.Row("Intern kommentar"),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id=f"{self.module_name}-{self.module_number}-dropdown-refnr"
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Lagre",
                                id=f"{self.module_name}-{self.module_number}-save-button",
                            )
                        ),
                    ]
                ),
                dbc.Row(
                    dcc.Textarea(
                        id=f"{self.module_name}-{self.module_number}-comment-text",
                        className="dataeditorsidebar-comment-textarea",  # TODO: Style in the css
                    )
                ),
            ]
        )

    def module_callbacks(self):
        @callback(
            Output(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
            Output(
                f"{self.module_name}-{self.module_number}-dropdown-refnr", "options"
            ),
            self.variableselector.get_input("refnr"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_all_callback_objects(),
        )
        def find_refnrs(refnr, skjema, *args):

            if isinstance(_get_connection_object(), EimerDBInstance):
                args_before_timeunits = 1
                N = len(get_time_units())
                args = list(args)
                print(f"Utklipp: {args[args_before_timeunits:N+args_before_timeunits]}")
                args[args_before_timeunits : N + args_before_timeunits] = list(
                    map(int, args[args_before_timeunits : N + args_before_timeunits])
                )
                print(f"test: {args}")

            filterdict = create_filter_dict(
                ["skjema", get_ident(), *get_time_units()], [skjema, *args]
            )
            logger.debug(f"Filterdict: {filterdict}")
            with get_connection() as conn:
                s = conn.table("skjemamottak")
                s = s.filter(ibis_filter_with_dict(filterdict))
                refnrs = s.select("refnr").distinct().execute()["refnr"].tolist()
            logger.debug(f"default_refnr: {refnr}\nrefnrs: {refnrs}")

            return refnr, [{"label": x, "value": x} for x in refnrs]

        @callback(
            Output(f"{self.module_name}-{self.module_number}-comment-text", "value"),
            Input(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
        )
        def get_comment(refnr):
            with get_connection() as conn:
                s = conn.table("skjemamottak")
                comment = (
                    s.filter(_.refnr == refnr)
                    .select("kommentar")
                    .to_pandas()["kommentar"]
                    .item()
                )
            print(f"comment: {comment}")
            return comment

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_name}-{self.module_number}-save-button", "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-comment-text", "value"),
            State(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_output(save_click, value, refnr, alert_store):
            if (
                not callback_context.triggered_id
                == f"{self.module_name}-{self.module_number}-save-button"
            ):
                logger.info("Preventing update")
                raise PreventUpdate

            comment_update = UpdateSkjemamottakKommentar(refnr=refnr, value=value)
            logger.info(comment_update)
            if isinstance(_get_connection_object(), EimerDBInstance):
                feedback = comment_update.update_eimer()
            elif isinstance(_get_connection_object(), ConnectionPool):
                logger.debug("Attempting to update using ibis logic.")
                feedback = comment_update.update_ibis()
            else:
                raise NotImplementedError(f"Connection of type '{type(_get_connection_object())}' is not implemented yet.")

            return [feedback, *alert_store]
