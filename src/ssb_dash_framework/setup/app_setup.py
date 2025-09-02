import logging

import dash_bootstrap_components as dbc
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template

from ..utils.app_logger import enable_app_logging

logger = logging.getLogger(__name__)

theme_map = {
    "cerulean": dbc.themes.CERULEAN,
    "cosmo": dbc.themes.COSMO,
    "cyborg": dbc.themes.CYBORG,
    "darkly": dbc.themes.DARKLY,
    "flatly": dbc.themes.FLATLY,
    "journal": dbc.themes.JOURNAL,
    "litera": dbc.themes.LITERA,
    "lumen": dbc.themes.LUMEN,
    "lux": dbc.themes.LUX,
    "materia": dbc.themes.MATERIA,
    "minty": dbc.themes.MINTY,
    "morph": dbc.themes.MORPH,
    "pulse": dbc.themes.PULSE,
    "quartz": dbc.themes.QUARTZ,
    "sandstone": dbc.themes.SANDSTONE,
    "simplex": dbc.themes.SIMPLEX,
    "sketchy": dbc.themes.SKETCHY,
    "slate": dbc.themes.SLATE,
    "solar": dbc.themes.SOLAR,
    "spacelab": dbc.themes.SPACELAB,
    "superhero": dbc.themes.SUPERHERO,
    "united": dbc.themes.UNITED,
    "vapor": dbc.themes.VAPOR,
    "yeti": dbc.themes.YETI,
    "zephyr": dbc.themes.ZEPHYR,
}


def app_setup(
    port: int,
    service_prefix: str | None = None,
    stylesheet: str = "darkly",
    enable_logging: bool = True,
    logging_level: str = "info",
    log_to_file: bool = False,
) -> Dash:
    """Set up and configure a Dash application with the specified parameters.

    Args:
        port (int): The port number for the Dash application.
        service_prefix (str): The service prefix used for constructing the app's pathname.
        stylesheet (str): The name of the Bootstrap theme to apply to the app.
                          Must be a key in `theme_map`.
        enable_logging (bool): Decides if ssb_dash_framework logging should be used. Defaults to True.
        logging_level (str): The logging level set for the application logging. Valid values are "debug", "info", "warning", "error", or "critical".
        log_to_file (bool): Decides if log should be written to file 'work/app.log' in addition to the console.

    Returns:
        Dash: Configured Dash application instance.

    Notes:
        - The function maps the `stylesheet` parameter to a Bootstrap theme using `theme_map`.
        - A callback is registered within the app to toggle the visibility of an element
          with the ID `main-varvelger` based on the number of clicks on `sidebar-varvelger-button`.

    Examples:
        >>> import os
        >>> app = app_setup(port=8050, service_prefix=os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/"))
        >>> app.run_server() # doctest: +SKIP
    """
    if enable_logging:
        enable_app_logging(level=logging_level, log_to_file=log_to_file)
        if log_to_file:
            logger.info(
                "Writing log file to work/app.log. DO NOT ADD 'app.log' FILE TO GIT REPO!"
            )
    template = theme_map[stylesheet]
    load_figure_template([template])

    dbc_css = (
        "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
    )

    app = Dash(
        __name__,
        requests_pathname_prefix=(
            f"{service_prefix}proxy/{port}/" if service_prefix else None
        ),
        external_stylesheets=[theme_map[stylesheet], dbc_css],
        assets_folder="../assets",
    )

    @callback(  # type: ignore[misc]
        Output("variable-selector-offcanvas", "is_open"),
        Input("sidebar-varvelger-button", "n_clicks"),
        State("variable-selector-offcanvas", "is_open"),
    )
    def toggle_variabelvelger(n_clicks: int | None, is_open: bool) -> bool:
        """Toggle the visibility of the variable selector offcanvas.

        This callback is triggered by clicking the "sidebar-varvelger-button".
        If the button has been clicked at least once, it toggles the state of
        the offcanvas panel (open/closed).

        Args:
            n_clicks (Optional[int]): The number of times the button has been clicked.
            is_open (bool): The current open/closed state of the offcanvas.

        Returns:
            bool: The new open/closed state of the offcanvas.

        Raises:
            PreventUpdate: If the button has not been clicked, no update is made.
        """
        if n_clicks:
            if not is_open:
                return True
            else:
                return False
        else:
            raise PreventUpdate

    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                html, body, #_dash-app-content, #_dash-app-layout {
                    height: 100vh;
                    margin: 0;
                    overflow: hidden;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """

    return app
