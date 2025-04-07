import logging

from dash import html

from ..modules.freesearch import FreeSearch

logger = logging.getLogger(__name__)


class FreeSearchTab(FreeSearch):
    def __init__(self, database):
        super().__init__(database)

    def layout(self) -> html.Div:
        """Generate the layout for the FrisokTab.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
