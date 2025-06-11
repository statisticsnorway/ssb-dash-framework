import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from ..modules.freesearch import FreeSearch
from ..utils import WindowImplementation

logger = logging.getLogger(__name__)


class FreeSearchWindow(WindowImplementation, FreeSearch):
    """FreeSearchWindow is a class that creates a modal based on the FreeSearch module."""

    def __init__(self, database: Any) -> None:
        """Initialize the FreeSearchWindow class.

        Args:
            database: The database connection or object used for querying.
        """
        FreeSearch.__init__(database)
        WindowImplementation.__init__(
            self,
        )
