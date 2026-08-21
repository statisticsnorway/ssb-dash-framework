from abc import abstractmethod
from dash import html

from ...meta import ContextABC

class DataEditorHelperSidebar(ContextABC):
    """Base class for defining a helper sidebar component."""


    @abstractmethod
    def _create_layout(self) -> html.Div:
        """Creates the layout for the module."""
        pass

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        pass