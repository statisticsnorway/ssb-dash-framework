import ast
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


class FreeSearch(ABC):
    """Tab for free-text SQL queries and displaying results in an AgGrid table.

    This class provides a layout for a tab that allows users to:
    - Enter SQL queries in a text area.
    - Optionally specify partition filters as a dictionary string.
    - Display the query results in an editable Dash AgGrid table.

    Attributes:
        database (object): Database connection or interface for executing SQL queries.
        label (str): Label for the tab, displayed in the application.

    Methods:
        layout(): Generates the layout for the tab.
        callbacks(): Registers the Dash callbacks for interactivity.
    """

    def __init__(self, database: object) -> None:
        """Initialize the FrisokTab with a database connection.

        Args:
            database (object): Database connection or interface used for executing SQL queries.

        Attributes:
            database (object): The provided database connection or interface.
            label (str): Label for the tab, set to "🔍 Frisøk".

        Raises:
            TypeError: If database does not have a query method an error is raised, as this module assumes database.query(sql_query) is possible.
        """
        if not hasattr(database, "query"):
            raise TypeError("The provided object does not have a 'query' method.")
        self.database = database
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self.label = "🔍 Frisøk"

    def _create_layout(self) -> html.Div:
        """Generate the layout for the FrisokTab.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        return html.Div(
            [
                html.Div(
                    dbc.Textarea(
                        id="tab-frisøk-textarea1",
                        size="xxl",
                        placeholder="SELECT * FROM databasetabell",
                    ),
                ),
                html.Div(
                    style={"display": "grid", "grid-template-columns": "80% 20%"},
                    children=[
                        dbc.Input(
                            id="tab-frisøk-input1",
                            placeholder="Velg partition. f.eks. {'aar': [2023], 'termin':[1, 2]}",
                        ),
                        dbc.Button(
                            "kjør",
                            id="tab-frisøk-button1",
                        ),
                    ],
                ),
                dag.AgGrid(
                    defaultColDef={"editable": True},
                    id="tab-frisøk-table1",
                    className="ag-theme-alpine-dark header-style-on-filter",
                ),
            ]
        )

    @abstractmethod
    def layout(self) -> html.Div:
        """Generate the layout for the FrisokTab.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        pass

    def module_callbacks(self) -> None:
        """Register the Dash callbacks for the FrisokTab.

        Notes:
            - This method registers a callback for executing the SQL query when the "kjør" button is clicked.
            - The results are displayed in the AgGrid table, with appropriate column definitions.
        """

        @callback(  # type: ignore[misc]
            Output("tab-frisøk-table1", "rowData"),
            Output("tab-frisøk-table1", "columnDefs"),
            Input("tab-frisøk-button1", "n_clicks"),
            State("tab-frisøk-textarea1", "value"),
            State("tab-frisøk-input1", "value"),
        )
        def table_free_search(
            n_clicks: int, query: str, partition: str
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            """Execute an SQL query and update the table with results.

            Args:
                n_clicks (int): Number of clicks on the "kjør" button.
                query (str): SQL query entered by the user in the text area.
                partition (str): Partition filters entered as a dictionary string
                                   (e.g., "{'aar': [2023]}"). Can be None if no filters are provided.

            Returns:
                tuple: Contains:
                    - rowData (list[dict]): Records to display in the table.
                    - columnDefs (list[dict]): Column definitions for the table.

            Raises:
                PreventUpdate: If click is None.

            Notes:
                - Column definitions hide the "row_id" column by default, if present.
            """
            if not n_clicks:
                raise PreventUpdate
            if partition is not None:
                partition = ast.literal_eval(partition)
            df = self.database.query(query, partition_select=partition)
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": True if col == "row_id" else False,
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columns

        logger.debug("Generated callbacks")
