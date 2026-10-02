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
from dash.dependencies import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate

from ssb_dash_framework.setup import VariableSelector

from .editor_helper_button import DataEditorHelperButton

logger = logging.getLogger(__name__)


class DataEditorSupportTable:
    """Class for adding a supporting context or reference table to the DataEditor.

    Attributes:
        label: The title/label displayed on the modal tab.
        get_data_func: Callback function to fetch and populate data in the AgGrid.
        pin_leftmost_column: Pins the first column to the left in the AgGrid table.
        suffix_to_colour_grey: Suffix of column names to shade light grey in grid.
        suptable_id: Generated auto-incremented ID of the supporting table.
    """

    suptable_id = 0

    def __init__(
        self,
        label: str,
        get_data_func: Callable[..., pd.DataFrame],
        inputs: list[str],
        states: list[str] | None = None,
        pin_leftmost_column: bool = True,
        suffix_to_colour_grey: list[str] | None = None,
    ) -> None:
        """Initializes the support table.

        Args:
            label: Label to put on the tab in the modal.
            get_data_func: Function that returns data to show in the supporting table.
            inputs: List of input fields to trigger data fetching.
            states: Optional list of state items.
            pin_leftmost_column: Optional. Boolean to pin the leftmost column. Defaults to True.
            suffix_to_colour_grey: Optional. List of column-name suffixes to shade grey. Defaults to ["_x"].
        """
        self.label = label
        self.get_data_func = get_data_func
        self.pin_leftmost_column = pin_leftmost_column
        self.suffix_to_colour_grey = suffix_to_colour_grey or ["_x"]

        self.suptable_id = DataEditorSupportTable.suptable_id
        DataEditorSupportTable.suptable_id += 1
        DataEditorSupportTables.support_components.append(self.support_table_layout())
        self.support_table_callbacks()

    def support_table_content(self) -> html.Div:
        """Returns the layout content containing the AgGrid table.

        Returns:
            A Dash Div element.
        """
        return html.Div(
            dag.AgGrid(
                className="ag-theme-alpine ag-theme-ssb mb-2",
                defaultColDef={"editable": False, "filter": True},
                dashGridOptions={"enableCellTextSelection": True},
                id=f"support-table-{self.suptable_id}",
                style={"height": "700px"},
            )
        )

    def support_table_callbacks(self) -> None:
        """Registers callbacks to load data from get_data_func when the modal opens."""

        @callback(  # TODO: Prevent update if table is not needed for current table and form
            Output(f"support-table-{self.suptable_id}", "rowData"),
            Output(f"support-table-{self.suptable_id}", "columnDefs"),
            Input(f"{DataEditorSupportTables.__name__}-0-modal", "is_open"),
            *VariableSelector.get_all_states(),
            prevent_initial_call=True,
        )
        def load_support_table_data(is_open: bool, *args: Any):
            if not is_open:
                raise PreventUpdate
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

    def support_table_layout(self) -> dbc.Tab:  # pyright: ignore
        """Creates the Tab layout containing the reference table.

        Returns:
            A Dash Bootstrap Tab element.
        """
        return dbc.Tab(
            self.support_table_content(),
            label=self.label,
            tab_id=f"support-table-{self.label}-{self.suptable_id}",
        )


class DataEditorSupportTables(DataEditorHelperButton):
    """Module providing a collection of supporting reference tables inside a modal.

    It adds a trigger button that launches a modal with tabs containing supplementary grids.
    """

    _id_number = 0
    support_components: ClassVar[list[DataEditorSupportTable]] = []

    def __init__(
        self,
        applies_to_tables: list[str] | None = None,
        applies_to_forms: list[str] | None = None,
    ) -> None:
        """Initializes the DataEditorSupportTables module.

        Args:
            applies_to_tables: Optional override listing applicable database tables.
            applies_to_forms: Optional override listing applicable questionnaire forms.
        """
        self.module_number = DataEditorSupportTables._id_number
        self.module_name = self.__class__.__name__
        DataEditorSupportTables._id_number += 1
        self.modal_body = self._create_modal_body()
        super().__init__(label="Hjelpetabeller")

    def _create_modal_body(self) -> html.Div:
        """Creates the internal layout structure holding all nested supporting table tabs.

        Returns:
            A Dash Div containing the Bootstrap Tabs.
        """
        return html.Div(
            [
                dbc.Tabs(
                    [*DataEditorSupportTables.support_components],
                    className="dataeditor-supporting-tables-tabs",
                ),
            ],
        )

    # TODO: Add callback for hiding irrelevant tables based on selected table and form
