import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ..utils.alert_handler import AlertHandler
from ..utils.functions import sidebar_button
from ..utils.implementations import TabModule
from ..utils.implementations import WindowModule
from .variableselector import VariableSelector

logger = logging.getLogger(__name__)


def main_layout(
    window_list: list[WindowModule],
    tab_list: list[dbc.Tab | TabModule],
    variable_list: list[str] | None = None,
    default_values: dict[str, Any] | None = None,
) -> dbc.Container:
    """Generates the main layout for the Dash application.

    Args:
        window_list (list[html.Div]):
            A list of modal components to be included in the sidebar.
        tab_list (list[html.Div | dbc.Tab]):
            A list of tab objects, each containing a `layout` method and a `label` attribute.
        variable_list (list[str] | None):
            A list of variable selection components to be included in the main layout. Defaults to all existing VariableSelectorOptions.
        default_values (dict[str, Any] | None, optional):
            Default values for the variable selector. Defaults to None.

    Returns:
        dbc.Container:
            A Dash Container component representing the app's main layout.

    Notes:
        - The function includes an alert handler modal and a toggle button for the variable selector.
        - Each tab in `tab_list` must implement a `layout()` method and have a `label` attribute.
    """
    if variable_list is None:
        logger.debug(
            "No variable list provided. Using all available VariableSelectorOptions."
        )
        variable_list = [
            option.title for option in VariableSelector._variableselectoroptions
        ]
        logger.debug(f"Variable list derived from VariableSelector: {variable_list}")
    if not default_values:
        logger.warning(  # TODO should this be a suggestion provided through logging or is that potentially annoying?
            "No default values provided. Variable selection will be empty on load, which might be un-intuitive. It is recommended to provide default values for the variable selector for better usability."
        )
    variable_selector = VariableSelector(
        selected_states=variable_list, selected_inputs=[], default_values=default_values
    )  # Because inputs and states don't matter in main_layout, everything is put into the VariableSelector as states. Every module defines its own VariableSelector that sets up interactions. This is to simplify it for the user while maintaining flexibility.

    window_modules = [module.layout() for module in window_list]
    alerthandler = AlertHandler()
    window_modules_list = [alerthandler.layout(), *window_modules]

    varvelger_toggle = [
        html.Div(
            [
                sidebar_button(
                    "🛆", "Vis variabler", "sidebar-varvelger-button"
                )
            ]
        )
    ]
    window_modules_list = varvelger_toggle + window_modules_list
    selected_tab_list = [
        (tab if isinstance(tab, dbc.Tab) else dbc.Tab(tab.layout(), label=tab.label))
        for tab in tab_list
    ]
    layout = dbc.Container(
        [
            html.Div(
                id="notifications-container",
                className="main-layout-notifications-container",
            ),
            html.P(
                id="update-status",
                style={"font-size": "60%", "visibility": "hidden"},  # What is this!?
            ),
            html.Div(
                id="main-layout",
                className="main-layout",
                children=[
                    html.Div(
                        id="main-layout-sidebar",
                        className="main-layout-sidebar bg-secondary",
                        children=window_modules_list,
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                id="main-layout-offcanvas",
                                children=[
                                    dbc.Offcanvas(
                                        html.Div(
                                            children=variable_selector.layout(),
                                        ),
                                        id="variable-selector-offcanvas",
                                        className="main-layout-offcanvas-variable-selector",
                                        title="Variabler",
                                        is_open=False,
                                        placement="end",
                                        backdrop=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                id="main-layout-tab-div",
                                className="main-layout-tab-container",
                                children=dbc.Tabs(selected_tab_list),
                            ),
                        ],
                    ),
                ],
            ),
        ],
        fluid=True,
        className="dbc dbc-ag-grid",
    )
    logger.debug("Generated layout.")
    return layout
