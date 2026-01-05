import logging
from abc import ABC
from abc import abstractmethod

from dash import html

from ...utils import TabImplementation
from ...utils import WindowImplementation

logger = logging.getLogger(__name__)


class Canvas(ABC):
    """The Canvas module is a base class that simplifies adding your own unique view to the framework.

    It is intended to be used when you want to combine building blocks into a single view.

    Its limitation is that it does not support any interactivity on its own, and no callbacks are defined.
    It is meant to be used as a container for other components, such as tables, graphs and similar.

    It can to a degree replace the need for a completely custom module, but if you need interactivity
    between the contained modules instead of routing it through the variable selector,
    you should consider creating a custom module instead.
    """

    _id_number = 0

    def __init__(self, label: str, content: html.Div) -> None:
        """Initializes the Canvas module.

        Args:
            label: The label for the canvas, used in the UI.
            content: A Dash layout that will be displayed in the canvas. Can contain other building block modules.
        """
        self.module_number = Canvas._id_number
        self.module_name = self.__class__.__name__
        Canvas._id_number += 1
        self.icon = "⬜"

        self.label = label
        self.content = content

        self.module_layout = self._create_layout()

    def _create_layout(self) -> html.Div:
        """Creates the layout for the canvas module."""
        layout = html.Div(self.content, className="canvas")
        logger.debug("Generated layout.")
        return layout

    @abstractmethod
    def layout(self) -> None:
        """Returns the layout of the canvas module.

        This method is abstract and should be implemented by subclasses to define the specific layout of the canvas.
        """
        pass


class CanvasTab(TabImplementation, Canvas):
    """Implements the Canvas module as a tab."""

    def __init__(self, label: str, content: html.Div) -> None:
        """Initializes the CanvasTab module.

        Args:
            label: The label for the canvas tab, used in the UI.
            content: A Dash layout that will be displayed in the canvas tab. Can contain other building block modules.
        """
        Canvas.__init__(self, label=label, content=content)
        TabImplementation.__init__(
            self,
        )


class CanvasWindow(WindowImplementation, Canvas):
    """Implements the Canvas module as a tab."""

    def __init__(self, label: str, content: html.Div) -> None:
        """Initializes the CanvasWindow module.

        Args:
            label: The label for the canvas tab, used in the UI.
            content: A Dash layout that will be displayed in the canvas tab. Can contain other building block modules.
        """
        Canvas.__init__(self, label=label, content=content)
        WindowImplementation.__init__(self)
