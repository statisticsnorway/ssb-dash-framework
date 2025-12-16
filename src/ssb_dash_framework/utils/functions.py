import logging

import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)

def get_config_path(module_name: str, ssb_template: bool=True):
    return f"/home/onyxia/work/stat-naringer-dash/config/ssb-dash-framework/{module_name}"

def sidebar_button(
    icon: str,
    text: str,
    component_id: str,
    additional_styling: dict[str, str] | None = None,
) -> html.Div:
    """Generate a sidebar button with an icon and label.

    Args:
        icon (str): The icon displayed at the top of the button.
        text (str): The label text displayed below the icon.
        component_id (str): The ID assigned to the button component.
        additional_styling (dict, optional): Additional styling applied to the button. Defaults to an empty dictionary.

    Returns:
        html.Div: A Div containing the styled button.
    """
    if additional_styling is None:
        additional_styling = {}
    return html.Div(
        dbc.Button(
            [
                html.Span(icon, className="sidebar-button-icon-spot"),
                html.Span(text, className="sidebar-button-label-spot"),
            ],
            id=component_id,
            className="sidebar-button-button",
            style={
                **additional_styling,
            },
        )
    )
