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

from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class FreeSearch(ABC):
    """Base class for creating a free-text SQL query interface with results displayed in an AgGrid table.

    This class serves as a template for modules that allow users to:
    - Enter SQL queries in a text area.
    - Optionally specify partition filters as a dictionary string.
    - Display query results in an editable Dash AgGrid table.

    Attributes:
        database (Any): Database connection or interface for executing SQL queries.
        label (str): Label for the module, defaults to "🔍 Frisøk".
        module_layout (html.Div): The generated layout for the module.

    Methods:
        layout(): Abstract method to define the module's layout.
        module_callbacks(): Registers the Dash callbacks for interactivity.
    """

    _id_number = 0

    def __init__(self, database: Any, label: str = "Frisøk") -> None:
        """Initialize the FreeSearch module with a database connection and optional label."""
        assert hasattr(
            database, "query"
        ), "The database object must have a 'query' method."
        self.module_number = FreeSearch._id_number
        self.module_name = self.__class__.__name__
        FreeSearch._id_number += 1
        self.icon = "🔍"
        self.label = label

        self.database = database
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _create_layout(self) -> html.Div:
        """Generate the default layout for the FreeSearch module.

        Returns:
            html.Div: A Dash HTML Div component containing:
                - A text area for entering SQL queries.
                - An input field for specifying partition filters as a dictionary string.
                - A button to execute the query.
                - A Dash AgGrid table for displaying the query results.
        """
        layout = html.Div(
            className="freesearch",
            children=[
                html.Div(
                    dbc.Textarea(
                        id="tab-frisøk-textarea1",
                        size="xxl",
                        placeholder="SELECT * FROM databasetabell",
                    ),
                ),
                html.Div(
                    className="freesearch-partition-button",
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
                    # className="ag-theme-alpine-dark header-style-on-filter",
                ),
            ],
        )
        logger.debug("Generated layout.")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the FreeSearch module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Register the Dash callbacks for the FreeSearch module.

        This method registers a callback to execute the SQL query when the "kjør" button is clicked.
        The query results are displayed in the AgGrid table, with appropriate column definitions.

        Notes:
            - The callback takes user inputs from the SQL query text area and partition filter input field.
            - The results are displayed in an editable table, with the "row_id" column hidden by default if present.
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
            """Execute an SQL query and update the table with the results.

            Args:
                n_clicks (int): Number of clicks on the "kjør" button.
                query (str): SQL query entered by the user in the text area.
                partition (str): Partition filters entered as a dictionary string
                                 (e.g., "{'aar': [2023]}"). Can be None if no filters are provided.

            Returns:
                tuple:
                    - rowData (list[dict]): A list of records (rows) to display in the table.
                    - columnDefs (list[dict]): A list of column definitions for the table.

            Raises:
                PreventUpdate: If the button has not been clicked.

            Notes:
                - The `partition` string is parsed into a dictionary before being used in the query.
                - Column definitions hide the "row_id" column by default, if present.
            """
            logger.debug(
                "Args:\n"
                f"n_clicks: {n_clicks}\n"
                f"query: {query}\n"
                f"partition: {partition}"
            )
            if not n_clicks:
                logger.debug("Raised PreventUpdate")
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
        FreeSearch.__init__(self, database=database)
        TabImplementation.__init__(self)


class FreeSearchWindow(WindowImplementation, FreeSearch):
    """FreeSearchWindow is a class that creates a modal based on the FreeSearch module."""

    def __init__(self, database: Any) -> None:
        """Initialize the FreeSearchWindow class.

        Args:
            database: The database connection or object used for querying.
        """
        FreeSearch.__init__(self, database=database)
        WindowImplementation.__init__(
            self,
        )
