# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
import logging
from typing import Any

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
from psycopg_pool import ConnectionPool

from .....setup.variableselector import VariableSelector
from .....utils.config_tools.connection import _get_connection_object
from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_refnr
from .....utils.config_tools.set_variables import get_time_units
from .....utils.core_models import UpdateSkjemamottakKommentar
from .editing_sidebar_helper import DataEditorHelperSidebar

logger = logging.getLogger(__name__)


class DataEditorSidebarComment(DataEditorHelperSidebar):
    """Sidebar component for showing a field comment."""

    _id_number = 0

    def __init__(self) -> None:
        """Initializes and registers the sidebar comment component."""
        self.module_number = DataEditorSidebarComment._id_number
        self.module_name = self.__class__.__name__
        DataEditorSidebarComment._id_number += 1

        self.variableselector = VariableSelector(
            selected_inputs=[get_ident(), get_time_units().name], selected_states=[]
        )
        self.module_callbacks()

        super().__init__()

    def _create_layout(self) -> html.Div:
        return html.Div(
            [
                dbc.Row("Intern kommentar"),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id=f"{self.module_name}-{self.module_number}-dropdown-refnr",
                                className="ssb-dropdown",
                                searchable=False,
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Lagre",
                                id=f"{self.module_name}-{self.module_number}-save-button",
                                className="ssb-btn primary-btn",
                            )
                        ),
                    ]
                ),
                dbc.Row(
                    dcc.Textarea(
                        id=f"{self.module_name}-{self.module_number}-comment-text",
                        placeholder="Skriv kommentar her...",
                        className="comment-textarea",
                        style={"height": "150px"},
                    )
                ),
            ]
        )

    def module_callbacks(self) -> None:
        """Registers the callbacks for the module."""

        @callback(
            Output(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
            Output(
                f"{self.module_name}-{self.module_number}-dropdown-refnr", "options"
            ),
            self.variableselector.get_input(get_refnr()),
            self.variableselector.get_input(get_ident()),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input(get_time_units().name),
        )
        def find_refnrs(
            refnr: str, ident, skjema: str, period
        ) -> tuple[str, list[dict[str, str]]]:
            """Collect relevant refnrs."""
            if not refnr or not skjema or not ident:
                raise PreventUpdate
            data = self.fetcher.get_refnrs_by_period_ident(self.settings, ident, period)

            if data is None:
                raise PreventUpdate

            refnrs = data[self.settings.refnr_col].unique().tolist()
            logger.debug(f"default_refnr: {refnr}\nrefnrs: {refnrs}")

            return refnr, [{"label": x, "value": x} for x in refnrs]

        @callback(
            Output(f"{self.module_name}-{self.module_number}-comment-text", "value"),
            Input(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
        )
        def get_comment(refnr: str) -> str:
            """Gets the comment for the selected 'refnr'."""
            comment = self.fetcher.get_comment(refnr)

            if comment is None:
                return ""

            return comment

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_name}-{self.module_number}-save-button", "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-comment-text", "value"),
            State(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_output(save_click: int | None, value: Any, refnr: str, alert_store):
            """Update the comment when button is clicked."""
            if (
                callback_context.triggered_id
                != f"{self.module_name}-{self.module_number}-save-button"
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
                raise NotImplementedError(
                    f"Connection of type '{type(_get_connection_object())}' is not implemented yet."
                )

            return [feedback, *alert_store]
