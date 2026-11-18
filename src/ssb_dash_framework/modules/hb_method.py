"""HB methodology application module."""

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
        """Return the initial empty layout; controls are added in the next task."""
        return html.Div()

    def module_callbacks(self) -> None:
        """Register no callbacks until the module interaction tasks are implemented."""
