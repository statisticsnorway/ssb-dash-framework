import logging

from dash import html
from dash import callback
from dash import Input
from dash import Output
from dash import State
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

from ..modules.ratemodel import RateModel
from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)

class RateModelWindow(RateModel):
    def __init__(self, id_var, cache_location, get_sample_func, get_population_func):
        super().__init__(id_var, cache_location, get_sample_func, get_population_func)
        self.callbacks()

    def layout(self) -> html.Div:
        """Generate the layout for the freesearch window.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Ratemodell")),
                        dbc.ModalBody(
                            self.module_layout
                        )
                    ],
                    id = "ratemodel-modal",
                    size="xl",
                    fullscreen = "xxl-down",
                ),
                sidebar_button("🔍", "ratemodel", "sidebar-ratemodel-button")
            ]
        )
        logger.debug("Generated layout")
        return layout

    def callbacks(self):
        @callback(  # type: ignore[misc]
            Output("ratemodel-modal", "is_open"),
            Input("sidebar-ratemodel-button", "n_clicks"),
            State("ratemodel-modal", "is_open"),
        )
        def ratemodel_toggle(n: int, is_open: bool) -> bool:
            """Toggles the state of the modal window.

            Args:
                n (int): Number of clicks on the toggle button.
                is_open (bool): Current state of the modal (open/closed).

            Returns:
                bool: New state of the modal (open/closed).
            """
            logger.info("Toggle modal")
            if n:
                return not is_open
            return is_open