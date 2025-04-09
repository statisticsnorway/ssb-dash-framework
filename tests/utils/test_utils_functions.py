import dash_bootstrap_components as dbc
from dash import html

from ssb_dash_framework.utils.functions import sidebar_button


def test_sidebar_button():
    button = sidebar_button("icon", "text", "id")
    assert isinstance(button, html.Div)
    assert isinstance(button.children, dbc.Button)
