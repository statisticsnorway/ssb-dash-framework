"""HB methodology application module."""

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash_iconify import DashIconify

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.utils.base_classes import AsType
from ssb_dash_framework.utils.base_classes import ModuleBase


class HBMethod(ModuleBase):
    """Module shell for running and displaying the HB methodology."""

    def __init__(
        self,
        *,
        hb_data_handler: HBDataHandlerMeta,
        as_type: AsType | None = None,
    ) -> None:
        """Initialize the module with its configured HB data handler."""
        self.label = "HB metoden"
        self.icon = DashIconify(icon="keyline-icons:pencil-ruler-sharp-duotone", width=24)
        self.hb_data_handler = hb_data_handler

        super().__init__(as_type=as_type)

    def layout(self) -> html.Div:
        """Create the HB controls and placeholders for a run's state and result."""
        return html.Div(
            children=[
                dcc.Store(id=f"{self.module_id}-hb_result_store", data=None),
                html.Div(
                    dbc.Button(
                        "Kjør HB-metoden",
                        id=f"{self.module_id}-hb_run_button",
                        n_clicks=0,
                        className="ssb-btn primary-btn",
                    ),
                    id=f"{self.module_id}-hb_controls",
                ),
                dbc.Alert(
                    id=f"{self.module_id}-hb_error_message",
                    color="danger",
                    is_open=False,
                ),
                html.Div(
                    "Kjør HB-metoden for å vise resultater.",
                    id=f"{self.module_id}-hb_empty_state",
                    role="status",
                ),
                dcc.Loading(
                    id=f"{self.module_id}-hb_result_loading",
                    type="default",
                    children=dcc.Graph(
                        id=f"{self.module_id}-hb_result_graph",
                        figure={},
                        style={"display": "none"},
                    ),
                ),
            ]
        )

    def module_callbacks(self) -> None:
        """Register no callbacks until the module interaction tasks are implemented."""
