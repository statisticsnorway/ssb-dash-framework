"""
editing_table.py

An EditingTable component for Dash using Dash AgGrid that requires a reason
for every cell edit. Implements Option 1 with stricter behavior:

- After editing a cell, a modal is shown asking for a required reason.
- The edit is not applied until the user confirms with a reason.
- If the user cancels, the edit is undone (cell is reverted to oldValue).

This ensures that **all edits must include a reason**.
"""

import logging
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
import pandas as pd
from dash import callback, html, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class EditingTable:
    """A component for editing data using a Dash AgGrid table.

    This version requires a reason for every edit.
    Workflow:
      1. User edits a cell → `cellValueChanged` fires.
      2. `capture_edit` stores the pending edit in a dcc.Store and opens a modal.
      3. User confirms with a reason:
           - The reason is added into the edit dictionary as key "reason".
           - `update_table_func(edit_with_reason, *dynamic_states)` is called.
      4. If the user cancels:
           - The cell is reverted to its oldValue.
           - No update function is called.

    Attributes:
        label (str): Label for the module.
        variableselector (VariableSelector): Helper to build dynamic inputs/states.
        get_data (Callable[..., Any]): Function returning a pandas.DataFrame used to populate the grid.
        update_table_func (Callable[..., Any] | None): Function to apply updates.
            Must accept (edit_with_reason, *dynamic_states).
        module_layout (html.Div): Layout containing the grid, modal, and hidden stores.
        number_format (str): d3 formatter for numeric cells.
    """

    _id_number: int = 0

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any] | None = None,
        output: str | list[str] | None = None,
        output_varselector_name: str | list[str] | None = None,
        number_format: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the EditingTable.

        Args:
            label: Display label for module.
            inputs: List of input variable names (used by VariableSelector).
            states: List of state variable names (used by VariableSelector).
            get_data_func: Callable returning a pandas.DataFrame. It will be called with selected inputs then states.
            update_table_func: Callable to perform the actual update. IMPORTANT: this function will be called as
                update_table_func(edit_with_reason, *dynamic_states).
            output / output_varselector_name: Optional integration with VariableSelector outputs.
            number_format: Optional d3 number format string for numeric columns.
            **kwargs: Passed to dag.AgGrid (except defaultColDef which is handled).
        """
        self.kwargs = kwargs
        self.module_number = EditingTable._id_number
        self.module_name = self.__class__.__name__
        EditingTable._id_number += 1
        self.icon = "📒"
        self.label = label
        self.output = output
        self.output_varselector_name = output_varselector_name or output

        self.number_format = number_format or "d3.format(',.1f')(params.value).replace(/,/g, ' ')"

        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.get_data = get_data_func
        self.get_data_args = [x for x in self.variableselector.selected_variables]
        self.update_table_func = update_table_func
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self) -> None:
        """Validate provided arguments and configuration."""
        if not isinstance(self.label, str):
            raise TypeError(f"label {self.label} is not a string, is type {type(self.label)}")
        if self.output is not None and self.output_varselector_name is not None:
            if isinstance(self.output, str) and not isinstance(self.output_varselector_name, str):
                raise TypeError(
                    f"output is a string while output_varselector_name {self.output_varselector_name} is not a string"
                )
            elif isinstance(self.output, list) and isinstance(self.output_varselector_name, list):
                if len(self.output) != len(self.output_varselector_name):
                    raise ValueError("output and output_varselector_name must have the same length")

    def _create_layout(self, **kwargs: Any) -> html.Div:
        """Create the module layout."""
        return html.Div(
            className="editingtable",
            children=[
                dag.AgGrid(
                    defaultColDef=self.kwargs.get("defaultColDef", {"editable": True}),
                    id=f"{self.module_number}-tabelleditering-table1",
                    className="ag-theme-alpine header-style-on-filter editingtable-aggrid-style",
                    **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
                ),
                dcc.Store(id=f"{self.module_number}-pending-edit"),  # holds the latest edit
                dcc.Store(id=f"{self.module_number}-table-data"),    # holds the latest rowData
                dbc.Modal(
                    [
                        dbc.ModalHeader("Reason for Change"),
                        dbc.ModalBody(
                            [
                                html.Div(id=f"{self.module_number}-edit-details"),
                                dbc.Textarea(
                                    id=f"{self.module_number}-edit-reason",
                                    placeholder="Enter reason for change...",
                                    style={"width": "100%"},
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button("Cancel", id=f"{self.module_number}-cancel-edit", color="secondary"),
                                dbc.Button("Confirm", id=f"{self.module_number}-confirm-edit", color="primary"),
                            ]
                        ),
                    ],
                    id=f"{self.module_number}-reason-modal",
                    is_open=False,
                    backdrop="static",
                    centered=True,
                ),
            ],
        )

    def layout(self) -> html.Div:
        """Return the layout (for external use)."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Register the callbacks for data loading and editing behavior."""
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        # --- Load data into the table ---
        @callback(
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            Output(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
        )
        def load_to_table(*dynamic_states: list[str]):
            """Load dataframe into AgGrid and store rowData for later reversion."""
            try:
                df = self.get_data(*dynamic_states)
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": col == "row_id",
                        "editable": col != "uuid",
                        "valueFormatter": (
                            {"function": self.number_format}
                            if pd.api.types.is_numeric_dtype(df[col])
                            else None
                        ),
                    }
                    for col in df.columns
                ]
                if columns:
                    columns[0]["checkboxSelection"] = True
                    columns[0]["headerCheckboxSelection"] = True
                return df.to_dict("records"), columns, df.to_dict("records")
            except Exception:
                logger.error("Error loading data", exc_info=True)
                raise

        # --- Capture edit and show modal ---
        @callback(
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def capture_edit(edited):
            """Capture edit from grid and open modal requiring reason."""
            if not edited:
                raise PreventUpdate
            edit = edited[0]
            details = f"Column: {edit['colId']} | Old: {edit['oldValue']} | New: {edit['value']}"
            return edit, True, details

        # --- Confirm edit ---
        @callback(
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State("alert_store", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def confirm_edit(n_clicks, edit, reason, error_log, *dynamic_states):
            """Confirm edit with reason, call update function, and log alert."""
            if not n_clicks:
                raise PreventUpdate
            if error_log is None:
                error_log = []
            if not edit:
                error_log.append(create_alert("Ingen pending edit funnet", "error", ephemeral=True))
                return False, error_log
            if not reason or str(reason).strip() == "":
                error_log.append(create_alert("Årsak for endring er påkrevd", "warning", ephemeral=True))
                return True, error_log

            # Add reason into edit dict
            edit_with_reason = dict(edit)
            edit_with_reason["reason"] = reason

            try:
                if self.update_table_func:
                    self.update_table_func(edit_with_reason, *dynamic_states)
                msg = f"{edit['colId']} oppdatert fra {edit['oldValue']} til {edit['value']}. Årsak: {reason}"
                logger.info(msg)
                error_log.append(create_alert(msg, "info", ephemeral=True))
                return False, error_log
            except Exception:
                logger.error("Error updating table", exc_info=True)
                error_log.append(
                    create_alert(
                        f"Oppdatering av {edit['colId']} fra {edit['oldValue']} til {edit['value']} feilet!",
                        "error",
                        ephemeral=True,
                    )
                )
                return False, error_log

        # --- Cancel edit (revert change) ---
        @callback(
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output(f"{self.module_number}-tabelleditering-table1", "rowData", allow_duplicate=True),
            Input(f"{self.module_number}-cancel-edit", "n_clicks"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-table-data", "data"),
            prevent_initial_call=True,
        )
        def cancel_edit(n_clicks, edit, current_data):
            """Cancel edit: close modal and revert the edited cell to its oldValue."""
            if not n_clicks or not edit or not current_data:
                raise PreventUpdate

            col = edit["colId"]
            row_id = edit.get("rowId") or edit.get("rowIndex")  # ag-grid may provide rowId or rowIndex
            old_val = edit["oldValue"]

            new_data = []
            for i, row in enumerate(current_data):
                row_copy = dict(row)
                if str(i) == str(row_id) or row_copy.get("row_id") == row_id:
                    row_copy[col] = old_val
                new_data.append(row_copy)

            return False, new_data


class EditingTableTab(TabImplementation, EditingTable):
    """EditingTable inside a Tab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TabImplementation.__init__(self)


class EditingTableWindow(WindowImplementation, EditingTable):
    """EditingTable inside a modal window."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WindowImplementation.__init__(self)
