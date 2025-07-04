import logging
from abc import ABC
from abc import abstractmethod

from dash import html

from ...utils import TabImplementation
from ...utils import WindowImplementation

logger = logging.getLogger(__name__)


class Canvas(ABC):

    _id_number = 0

    def __init__(self, label, content):
        self.module_number = Canvas._id_number
        self.module_name = self.__class__.__name__
        Canvas._id_number += 1

        self.label = label
        self.content = content

        self.module_layout = self._create_layout()

    def _is_valid(self):
        """Needs to recursively check everything in the layout to ensure"""
        pass

    def _create_layout(self):
        layout = html.Div(self.content, className="canvas")
        logger.debug("Generated layout.")
        return layout

    @abstractmethod
    def layout(self):
        pass


class CanvasTab(TabImplementation, Canvas):
    def __init__(self, label, content):
        Canvas.__init__(self, label=label, content=content)
        TabImplementation.__init__(
            self,
        )


class CanvasWindow(WindowImplementation, Canvas):
    def __init__(self, label, content):
        Canvas.__init__(self, label=label, content=content)
        WindowImplementation.__init__(self)
