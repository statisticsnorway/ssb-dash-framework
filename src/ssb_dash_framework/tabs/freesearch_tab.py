import logging

from dash import html

from ..modules.freesearch import FreeSearch

logger = logging.getLogger(__name__)


class FreeSearchTab(FreeSearch):
    """Implementation of the FreeSearch module as a tab in the application.

    This class extends the FreeSearch base class and provides a layout
    specific to the tab interface.
    """

    def __init__(self, database):
        """Initialize the FreeSearchTab with a database connection.

        Args:
            database (object): Database connection or interface used for executing SQL queries.
        """
        super().__init__(database)

    def layout(self) -> html.Div:
        """Generate the layout for the FreeSearchTab.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
