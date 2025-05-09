import logging

from dash import html

from ..modules.aarsregnskap import Aarsregnskap

logger = logging.getLogger(__name__)


class AarsregnskapTab(Aarsregnskap):
    """AarsregnskapTab is an implementation of the Aarsregnskap module as a tab in a Dash application."""

    def __init__(self) -> None:
        """Initializes the AarsregnskapTab class."""
        super().__init__()

    def layout(self) -> html.Div:
        """Generates the layout for the Årsregnskap module as a tab.

        Returns:
            html.Div: The layout of the Årsregnskap tab.
        """
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
