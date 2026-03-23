# TODO: Add functionality to add more types of helper things into the module.
import logging
from collections.abc import Callable
from typing import Any
from typing import ClassVar

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import callback
from dash import html
from dash.dependencies import Output

from ssb_dash_framework.setup import VariableSelector

from ..core import DataEditorHelperButton

logger = logging.getLogger(__name__)


class DataEditorSupportTable:
    """Class for adding a supporting table to the component in DataEditor."""

    suptable_id = 0

    def __init__(
        self,
        label: str,
        get_data_func: Callable[..., pd.DataFrame],
        inputs,
        states=None,
        pin_leftmost_column: bool = True,
        suffix_to_colour_grey: list[str] | None = None,
    ) -> None:
        """Initializes the support table.

        Args:
            label: Label to put on the tab in the modal.
            get_data_func: Function that returns data to show in the supporting table.
            variableselector: VariableSelector instance for adding arguments from the overall variableselector.
            pin_leftmost_column: Optional. Boolean to pin the leftmost column in the AgGrid (usually the ident-col). Defaults to "True".
            suffix_to_colour_grey: Optional. List of column-name suffixes to colour light grey in the AgGrid. Defaults to "[_x]".

        Note:
            The component is automatically added to the panel inside the modal.
        """
        self.label = label
        self.get_data_func = get_data_func
        self.pin_leftmost_column = pin_leftmost_column
        self.suffix_to_colour_grey = suffix_to_colour_grey or ["_x"]
        self.variableselector = VariableSelector(inputs, states if states else [])
        self.suptable_id = DataEditorSupportTable.suptable_id
        DataEditorSupportTable.suptable_id += 1
        DataEditorSupportTables.support_components.append(self.support_table_layout())
        self.support_table_callbacks()

    def support_table_content(self) -> html.Div:
        """The content to show in the support table."""
        return html.Div(
            dag.AgGrid(
                defaultColDef={"editable": False, "filter": True},
                dashGridOptions={"enableCellTextSelection": True},
                id=f"support-table-{self.suptable_id}",
                style={"height": "700px"},
            )
        )

    def support_table_callbacks(self) -> None:
        """Adds necessary callbacks."""

        @callback( # TODO: Prevent update if table is not needed for current table and form
            Output(f"support-table-{self.suptable_id}", "rowData"),
            Output(f"support-table-{self.suptable_id}", "columnDefs"),
            *self.variableselector.get_all_callback_objects(),
        )
        def load_support_table_data(*args: Any):
            logger.info(
                f"Running get_data_func for table '{self.label}' using args: {args}"
            )
            data = self.get_data_func(*args)
            column_defs = []
            for col in data.columns:
                col_def: dict[str, Any] = {"field": col, "headerName": col.lower()}
                if self.suffix_to_colour_grey and col.endswith(
                    tuple(self.suffix_to_colour_grey)
                ):
                    col_def["cellStyle"] = {"backgroundColor": "#e8e9eb"}
                column_defs.append(col_def)
            if self.pin_leftmost_column and column_defs:
                column_defs[0]["pinned"] = "left"
            return data.to_dict("records"), column_defs

    def support_table_layout(self) -> dbc.Tab:
        """Creates the layout."""
        return dbc.Tab(
            self.support_table_content(),
            label=self.label,
            tab_id=f"support-table-{self.label}-{self.suptable_id}",
        )


class DataEditorSupportTables(DataEditorHelperButton):
    """This module provides supporting tables for the DataEditor.

    It adds a button that opens a modal with tabs containing tables with extra informatiion.

    Note:
        Adding your own supporting tables is not supported at this time.
    """

    support_components: ClassVar[list[DataEditorSupportTable]] = []

    def __init__(self, applies_to_tables=None, applies_to_forms=None) -> None:
        """Initializes the DataEditorEditorSupportTables module."""
        self.modal_body = self._create_modal_body()
        super().__init__(label="Hjelpetabeller")

    def _create_modal_body(self) -> html.Div:
        return html.Div(
            [
                dbc.Tabs(
                    [*DataEditorSupportTables.support_components],
                    className="dataeditor-supporting-tables-tabs",
                ),
            ],
        )
    
    # TODO: Add callback for hiding irrelevant tables based on selected table and form


    # def add_default_tables(self, tables_to_add: list[str], conn: Any) -> None:
    #     """Adds specified default supporting tables to view."""
    #     for table in tables_to_add:
    #         if table == "aar_til_fjoraar":
    #             add_year_diff_support_table(conn)
    #         else:
    #             raise ValueError(
    #                 f"Table named '{table}' not among available default tables."
    #             )
