import logging

import dash_bootstrap_components as dbc
from dash import html

from ..utils.alert_handler import AlertHandler
from ..utils.functions import sidebar_button
from .variableselector import VariableSelector

logger = logging.getLogger(__name__)


def main_layout(
    modal_list: list[html.Div],
    tab_list: list[html.Div],
    variable_list: list[str],
    default_values: dict[str, any] | None = None,
) -> dbc.Container:
    """Generate the main layout for the Dash application.

    Args:
        modal_list (list[html.Div]):
            List of modal components to be included in the sidebar.
        tab_list (list[html.Div]):
            List of tab objects, each containing a `layout` method and a `label` attribute.
        variable_list (list[html.Div]):
            List of variable selection components to be included in the main layout.

    Returns:
        dbc.Container:
            A Dash Container component representing the app's main layout.

    Notes:
        - The function includes an alert handler modal and a toggle button for the variable selector.
        - Each tab in `tab_list` must implement a `layout()` method and have a `label` attribute.
    """
    variable_selector = VariableSelector(
        selected_states=variable_list, selected_inputs=[], default_values=default_values
    )  # Because inputs and states don't matter in main_layout, everything is put into the VariableSelector as states. Every module defines its own VariableSelector that sets up interactions. This is to simplify it for the user while maintaining flexibility.

    alerthandler = AlertHandler()
    alerthandler_layout = alerthandler.layout()
    modal_list = [alerthandler_layout, *modal_list]

    varvelger_toggle = [
        html.Div(
            [
                sidebar_button(
                    "🛆", "vis/skjul variabelvelger", "sidebar-varvelger-button"
                )
            ]
        )
    ]
    modal_list = varvelger_toggle + modal_list
    selected_tab_list = [dbc.Tab(tab.layout(), label=tab.label) for tab in tab_list]
    layout = dbc.Container(
        [
            html.Div(
                id="notifications-container",
                style={"position": "fixed", "z-index": 9999},
            ),
            html.P(
                id="update-status", style={"font-size": "60%", "visibility": "hidden"}
            ),
            html.Div(
                id="main-layout",
                style={
                    "height": "100vh",
                    "overflow": "auto",
                    "display": "grid",
                    "grid-template-columns": "5% 95%",
                },
                children=[
                    html.Div(
                        className="bg-secondary",
                        style={
                            "display": "flex",
                            "flex-direction": "column",
                            "height": "100%",
                        },
                        children=modal_list,
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                dbc.Row(children=variable_selector.layout()),
                                style={"display": "none"},
                                id="main-varvelger",
                            ),
                            html.Div(
                                dbc.Tabs(
                                    selected_tab_list,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ],
        fluid=True,
        className="dbc dbc-ag-grid",
    )
    return layout
