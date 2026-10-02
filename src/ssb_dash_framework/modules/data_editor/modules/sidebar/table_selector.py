import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from .editing_sidebar_helper import DataEditorHelperSidebar


class DataEditorTableSelector(DataEditorHelperSidebar):
    """Default module to select datasource table to show data for."""

    _id_number = 0

    def __init__(self, form_data_tables: list[str], starting_table: str) -> None:
        """Initializes the table selector component.

        Args:
            form_data_tables: A list of tables in the database to select from.
            starting_table: Sets the default table value to display first.

        Raises:
            ValueError: If starting_table is not found in form_data_tables.
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
        """Creates the dropdown table selector component.

        Returns:
            A Dash Div containing the label and dropdown component.
        """
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
        """Returns the layout containing the component.

        Returns:
            A Dash Div element.
        """
        return self._create_layout()

    def module_callbacks(
        self,
    ) -> None:  # TODO Add a way to connect selected table to variable selector?
        """Registers callbacks. Currently no callbacks are required."""
        pass
