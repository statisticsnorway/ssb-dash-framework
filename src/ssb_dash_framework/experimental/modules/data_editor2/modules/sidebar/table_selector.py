# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
from dash import html, dcc
import dash_bootstrap_components as dbc

from .editing_sidebar_helper import DataEditorHelperSidebar


class DataEditorTableSelector(DataEditorHelperSidebar):
    """Default module to select datasource table to show data for."""

    _id_number = 0

    def __init__(self, form_data_tables: list[str], starting_table: str) -> None:
        """Initializes the table selector component.

        Args:
            starting_table: Sets the default value of the DataEditorTableSelector dropdown.
            table_list: Optional override to default list of tables. Defaults to getting all tables starting with the prefix 'skjemadata_'.

        Raises:
            NotImplementedError: if another instance of DataEditorTableSelector is already running. Current implementation does not support multiple of the DataEditorTableSelector module.
            ValueError: If starting table does not exist in table_list.
        """

        self.module_name = self.__class__.__name__
        DataEditorTableSelector._id_number += 1

        self.table_options = [
            {"label": item, "value": item} for item in form_data_tables
        ]

        if starting_table not in form_data_tables:
            raise ValueError(
                f"Selected starting table not found in data source.\nExpected one of: '{form_data_tables}'.\nReceived: '{starting_table}'"
            )
        self.starting_table = starting_table

    def _create_layout(self) -> html.Div:
        """Creates the component."""
        return html.Div(
            [
                dbc.Label("Tabellvelger"),
                dcc.Dropdown(
                    id="dataeditortableselector",
                    searchable=False,
                    options=self.table_options,
                    value=self.starting_table,
                    className="ssb-dropdown",
                    placeholder="-- Velg tabell --",
                ),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout containing the component."""
        return self._create_layout()

    def module_callbacks(
        self,
    ) -> None:  # TODO Add a way to connect selected table to variable selector?
        """Registers callbacks. Currently no callbacks required from the module itself."""
        pass
