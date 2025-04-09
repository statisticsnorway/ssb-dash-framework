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
    """Base class for creating a free-text SQL query interface with results displayed in an AgGrid table.

    This class provides a template for modules that allow users to:
    - Enter SQL queries in a text area.
    - Optionally specify partition filters as a dictionary string.
    - Display query results in an editable Dash AgGrid table.

    Attributes:
        database (object): Database connection or interface for executing SQL queries.
        label (str): Label for the module, displayed in the application.
        module_layout (html.Div): The generated layout for the module.

    Methods:
        layout(): Abstract method to define the module's layout.
        module_callbacks(): Registers the Dash callbacks for interactivity.
    """

    def __init__(self, database: object) -> None:
        """Initialize the FreeSearch module with a database connection.

        Args:
            database (object): Database connection or interface used for executing SQL queries.

        Attributes:
            database (object): The provided database connection or interface.
            module_layout (html.Div): The generated layout for the module.
            label (str): Label for the module, set to "🔍 Frisøk".

        Raises:
            TypeError: If the provided database object does not have a `query` method.
        """
        if not hasattr(database, "query"):
            raise TypeError("The provided object does not have a 'query' method.")
        self.database = database
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self.label = "🔍 Frisøk"

    def _create_layout(self) -> html.Div:
        """Generate the default layout for the FreeSearch module.

        Returns:
            html.Div: A Div element containing:
                - A text area for SQL queries.
                - An input field for partition filters.
                - A button to execute the query.
                - A Dash AgGrid table for displaying query results.
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
        """Register the Dash callbacks for the FreeSearch module.

        This method defines the callback for executing SQL queries and updating the AgGrid table with results.
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
                PreventUpdate: If the button has not been clicked.

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
