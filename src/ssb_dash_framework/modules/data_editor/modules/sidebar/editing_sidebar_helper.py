from abc import abstractmethod

from dash import html

from ...meta import ContextABC


class DataEditorHelperSidebar(ContextABC):
    """Base class for defining a helper sidebar component.

    Subclasses must implement `_create_layout` and `module_callbacks`.
    """

    @abstractmethod
    def _create_layout(self) -> html.Div:
        """Creates the internal visual layout of the sidebar widget.

        Returns:
            A Dash Div element.
        """
        pass

    def layout(self) -> html.Div:
        """Returns the layout of the module.

        Returns:
            A Dash Div element.
        """
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Registers interactive callbacks for the sidebar module."""
        pass
