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

from .....utils.alert_handler import AlertHandler, create_alert
from .....config.models import register_module
from .....setup.variableselector import VariableSelector
from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_refnr
from .....utils.config_tools.set_variables import get_time_units
from .editing_sidebar_helper import DataEditorHelperSidebar

logger = logging.getLogger(__name__)


@register_module()
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

            try:
                comment = self.fetcher.get_comment(refnr)
                comment_update = "Comment was updated successfully"
                logger.info(comment_update)
                AlertHandler.info(comment_update)
            except Exception as e:
                error_msg = f"Comment failed to update with error: {e}"
                logger.info(error_msg)
                AlertHandler.info(error_msg) 

            if comment is None:
                error_msg = "Comment returned with None"
                logger.info(error_msg)
                AlertHandler.info(error_msg) 
                return ""

            return comment

        save_button_id = f"{self.module_name}-{self.module_number}-save-button"

        @callback(
            Input(save_button_id, "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-comment-text", "value"),
            State(f"{self.module_name}-{self.module_number}-dropdown-refnr", "value"),
            prevent_initial_call=True,
        )
        def update_output(save_click: int | None, value: Any, refnr: str):
            """Update the comment when button is clicked."""
            if callback_context.triggered_id != save_button_id:
                logger.info("Preventing update")
                raise PreventUpdate

            # comment_update = UpdateSkjemamottakKommentar(refnr=refnr, value=value)
            try:
                self.fetcher.update_form_reception_comment(refnr, value)
                comment_update = "Comment was updated successfully"
                logger.info(comment_update)
                AlertHandler.info(comment_update)
            except Exception as e:
                error_msg = f"Comment failed to update with error: {e}"
                logger.info(error_msg)
                AlertHandler.info(error_msg) 
            
