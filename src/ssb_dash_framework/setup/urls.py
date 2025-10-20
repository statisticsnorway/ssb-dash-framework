import logging
import re

from dash import callback
from dash import Output
from dash import Input
from dash.exceptions import PreventUpdate

from .main_layout import get_standard_layout

logger = logging.getLogger(__name__)


def add_urls():
    logger.debug("Adding urls.")
    @callback(
        Output("main-layout", "children"),
        Input("url", "pathname")
    )
    def routing(path):
        logger.info(f"Routing input: {path}")
        if bool(re.fullmatch(r'/proxy/\d{4}/', path)):
            logger.debug("Returning standard layout.")
            return get_standard_layout()
        else:
            logger.debug("Preventing update.")
            raise PreventUpdate