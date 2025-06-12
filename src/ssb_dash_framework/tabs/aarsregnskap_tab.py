import logging

from dash import html

from ..modules.aarsregnskap import Aarsregnskap
from ..utils import TabImplementation

logger = logging.getLogger(__name__)


class AarsregnskapTab(TabImplementation, Aarsregnskap):
    """AarsregnskapTab is an implementation of the Aarsregnskap module as a tab in a Dash application."""

    def __init__(self) -> None:
        """Initializes the AarsregnskapTab class."""
        Aarsregnskap.__init__()
        TabImplementation.__init__(self)
