import logging
from typing import Any

from dash import html

from ..modules.freesearch import FreeSearch
from ..utils import TabImplementation

logger = logging.getLogger(__name__)


class FreeSearchTab(TabImplementation, FreeSearch):
    """Implementation of the FreeSearch module as a tab in the application.

    This class extends the FreeSearch base class and provides a layout
    specific to the tab interface.
    """

    def __init__(self, database: Any) -> None:
        """Initialize the FreeSearchTab with a database connection.

        Args:
            database (Any): Database connection or interface used for executing SQL queries.
        """
        FreeSearch.__init__(self, database)
        TabImplementation.__init__(self)
