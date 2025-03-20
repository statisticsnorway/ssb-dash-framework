import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template

logger = logging.getLogger(__name__)
theme_map = {
    "sketchy": dbc.themes.SKETCHY,
    "slate": dbc.themes.SLATE,
    "cyborg": dbc.themes.CYBORG,
    "superhero": dbc.themes.SUPERHERO,
    "darkly": dbc.themes.DARKLY,
    "solar": dbc.themes.SOLAR,
    "flatly": dbc.themes.FLATLY,
}


def app_setup(port: int, service_prefix: str, domain: str, stylesheet: str) -> Dash:
    """Set up and configure a Dash application with the specified parameters.

    Args:
        port (int): The port number for the Dash application.
        service_prefix (str): The service prefix used for constructing the app's pathname.
        domain (str): The domain name where the app is hosted.
        stylesheet (str): The name of the Bootstrap theme to apply to the app.
                          Must be a key in `theme_map`.

    Returns:
        Dash: Configured Dash application instance.

    Notes:
        - The function maps the `stylesheet` parameter to a Bootstrap theme using `theme_map`.
        - A callback is registered within the app to toggle the visibility of an element
          with the ID `main-varvelger` based on the number of clicks on `sidebar-varvelger-button`.

    Examples:
        >>> app = app_setup(port=8050, service_prefix="/", domain="localhost", stylesheet="slate")
        >>> app.run_server() # doctest: +SKIP
    """
    template = theme_map[stylesheet]
    load_figure_template([template])

    dbc_css = (
        "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
    )

    app = Dash(
        __name__,
        requests_pathname_prefix=f"{service_prefix}proxy/{port}/",
        external_stylesheets=[theme_map[stylesheet], dbc_css],
    )

    @callback(  # type: ignore[misc]
        Output("main-varvelger", "style"),
        Input("sidebar-varvelger-button", "n_clicks"),
        State("main-varvelger", "style"),
    )
    def toggle_varselector(n_clicks: int, style: dict[str, Any]) -> dict[str, Any]:
        """Toggle the visibility of the `main-varselector` component.

        Args:
            n_clicks (int): The number of times the `sidebar-varvelger-button` is clicked.
            style (dict): Current style dictionary for the `main-varvelger` component.

        Returns:
            dict: Updated style dictionary for `main-varvelger`.

        Raises:
            PreventUpdate: If click is None.
        """
        if not n_clicks:
            raise PreventUpdate
        if style == {"display": "none"}:
            style = {}
        else:
            style = {"display": "none"}
        return style

    return app
