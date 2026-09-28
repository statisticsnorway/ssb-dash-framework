import logging

from dash import html

from ...config import register_module
from ...utils import ModuleBase


logger = logging.getLogger(__name__)

@register_module()
class Canvas(ModuleBase):
    """The Canvas module is a base class that simplifies adding your own unique view to the framework.

    It is intended to be used when you want to combine building blocks into a single view.

    Its limitation is that it does not support any interactivity on its own, and no callbacks are defined.
    It is meant to be used as a container for other components, such as tables, graphs and similar.

    It can to a degree replace the need for a completely custom module, but if you need interactivity
    between the contained modules instead of routing it through the variable selector,
    you should consider creating a custom module instead.
    """

    def __init__(self, label: str, content: html.Div) -> None:
        """Initializes the Canvas module.

        Args:
            label: The label for the canvas, used in the UI.
            content: A Dash layout that will be displayed in the canvas. Can contain other building block modules.
        """
        self.icon = "⬜"

        self.label = label
        self.content = content


    def layout(self) -> html.Div:
        """Creates the layout for the canvas module."""
        layout = html.Div(self.content, className="canvas")
        logger.debug("Generated layout.")
        return layout

    def module_callbacks(self) -> None:
        pass
