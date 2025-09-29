"""
editing_table.py

An EditingTable component for Dash using Dash AgGrid that requires a reason
for every cell edit. Implements Option 1 with strict behavior:

- After editing a cell, a modal is shown asking for a required reason.
- The edit is not persisted until the user confirms with a reason.
- If the user cancels, the edit is undone (the grid is reverted to the last
  persisted rowData).
- The reason is inserted into the edit dictionary (key "reason") which is
  passed to update_table_func(edit_with_reason, *dynamic_states).

Additional features:
- User can specify log directory.
- Changes modal textarea auto-focuses.
- Pressing Enter in the textarea triggers Confirm.

This file preserves the original design and hooks:
- Loads data via `get_data_func`.
- Calls `update_table_func(edit_with_reason, *dynamic_states)` on confirm.
- Uses VariableSelector to construct dynamic inputs/states for callbacks.
"""

import logging
from collections.abc import Callable
from typing import Any
import os
import json
import time

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
    """A component for editing data using a Dash AgGrid table that enforces reasons."""

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
        log_filepath: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the EditingTable component.

        Args:
            log_filepath: Filepath of changelog. Must be .jsonl
        """
        self.kwargs = kwargs
        self.module_number = EditingTable._id_number
        self.module_name = self.__class__.__name__
        EditingTable._id_number += 1
        self.icon = "📒"
        self.label = label
        self.output = output
        self.output_varselector_name = output_varselector_name or output
        self.log_filepath = log_filepath

        if number_format is None:
            self.number_format = "d3.format(',.1f')(params.value).replace(/,/g, ' ')"
        else:
            self.number_format = number_format

        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.get_data = get_data_func
        self.get_data_args = [x for x in self.variableselector.selected_variables]
        self.update_table_func = update_table_func
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()

        self.timestamp = int(time.time() * 1000)

        module_validator(self)

    def _is_valid(self) -> None:
        """Validate provided arguments and configuration."""
        if not isinstance(self.label, str):
            raise TypeError(f"label {self.label} is not a string")
        if self.output is not None and self.output_varselector_name is not None:
            if isinstance(self.output, str) and not isinstance(self.output_varselector_name, str):
                raise TypeError("output_varselector_name type mismatch")
            elif isinstance(self.output, list) and isinstance(self.output_varselector_name, list):
                if len(self.output) != len(self.output_varselector_name):
                    raise ValueError("output and output_varselector_name length mismatch")

    def _create_layout(self, **kwargs: Any) -> html.Div:
        """Create layout (AgGrid + modal + stores)."""
        layout = html.Div(
            className="editingtable",
            children=[
                dag.AgGrid(
                    defaultColDef=self.kwargs.get("defaultColDef", {"editable": True}),
                    id=f"{self.module_number}-tabelleditering-table1",
                    className="ag-theme-alpine header-style-on-filter editingtable-aggrid-style",
                    **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
                ),
                dcc.Store(id=f"{self.module_number}-pending-edit"),
                dcc.Store(id=f"{self.module_number}-table-data"),
                dbc.Modal(
                    [
                        dbc.ModalHeader("Reason for change"),
                        dbc.ModalBody(
                            [
                                html.Div(id=f"{self.module_number}-edit-details"),
                                dbc.Textarea(
                                    id=f"{self.module_number}-edit-reason",
                                    placeholder="Enter reason for the change...",
                                    style={"width": "100%"},
                                    autoFocus=True,
                                    n_submit=0,  # <-- allow Enter to trigger callback
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Cancel",
                                    id=f"{self.module_number}-cancel-edit",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Confirm",
                                    id=f"{self.module_number}-confirm-edit",
                                    color="primary",
                                ),
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
        return layout

    def layout(self) -> html.Div:
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Register callbacks for loading data, capturing edits, confirming and cancelling."""
        dynamic_states = [self.variableselector.get_inputs(), self.variableselector.get_states()]

        @callback(
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            Output(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
        )
        def load_to_table(*dynamic_states):
            try:
                df = self.get_data(*dynamic_states)
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": col == "row_id",
                        "editable": col != "uuid",
                        "valueFormatter": {"function": self.number_format} if pd.api.types.is_numeric_dtype(df[col]) else None,
                    }
                    for col in df.columns
                ]
                if columns:
                    columns[0]["checkboxSelection"] = True
                    columns[0]["headerCheckboxSelection"] = True
                row_data = df.to_dict("records")
                return row_data, columns, row_data
            except Exception as e:
                logger.error("Error loading data", exc_info=True)
                raise e

        @callback(
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Output(f"{self.module_number}-edit-reason", "value"),
            Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def capture_edit(edited):
            if not edited:
                raise PreventUpdate
            edit = edited[0]
            details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
            return edit, True, details, ""

        @callback(
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Output(f"{self.module_number}-table-data", "data", allow_duplicate=True),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            Input(f"{self.module_number}-edit-reason", "n_submit"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State("alert_store", "data"),
            State(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def confirm_edit(n_clicks, n_submit, pending_edit, reason, error_log, table_data, *dynamic_states):
            if not (n_clicks or n_submit):
                raise PreventUpdate
            if error_log is None:
                error_log = []
            if not pending_edit:
                error_log.append(create_alert("Ingen pending edit funnet", "error", ephemeral=True))
                return False, error_log, table_data
            if not reason or str(reason).strip() == "":
                error_log.append(create_alert("Årsak for endring er påkrevd", "warning", ephemeral=True))
                return True, error_log, table_data

            edit_with_reason = dict(pending_edit)
            edit_with_reason["reason"] = reason
            edit_with_reason["timestamp"] = int(time.time() * 1000)

            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(edit_with_reason, ensure_ascii=False) + "\n")

            if self.update_table_func:
                self.update_table_func(edit_with_reason, *dynamic_states)

            new_table_data = list(table_data) if table_data else []
            row_obj = pending_edit.get("data") or {}
            updated = False
            uid = row_obj.get("uuid") if isinstance(row_obj, dict) else None
            rid = row_obj.get("row_id") if isinstance(row_obj, dict) else None
            if uid is not None:
                for i, r in enumerate(new_table_data):
                    if r.get("uuid") == uid:
                        new_table_data[i] = row_obj
                        updated = True
                        break
            elif rid is not None:
                for i, r in enumerate(new_table_data):
                    if r.get("row_id") == rid:
                        new_table_data[i] = row_obj
                        updated = True
                        break
            else:
                row_index = pending_edit.get("rowIndex")
                if row_index is not None and 0 <= int(row_index) < len(new_table_data):
                    new_table_data[int(row_index)] = row_obj
                    updated = True
            if not updated:
                new_table_data.append(row_obj)

            return False, error_log, new_table_data

        @callback(
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output(f"{self.module_number}-tabelleditering-table1", "rowData", allow_duplicate=True),
            Input(f"{self.module_number}-cancel-edit", "n_clicks"),
            State(f"{self.module_number}-table-data", "data"),
            prevent_initial_call=True,
        )
        def cancel_edit(n_clicks, table_data):
            if not n_clicks:
                raise PreventUpdate
            if table_data is None:
                return False, PreventUpdate
            return False, table_data


class EditingTableTab(TabImplementation, EditingTable):
    """A class to implement an EditingTable module inside a tab."""

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
        number_format: str | None = None,
        log_filepath: str,
        **kwargs: Any,
    ) -> None:
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            update_table_func=update_table_func,
            output=output,
            output_varselector_name=output_varselector_name,
            number_format=number_format,
            log_filepath=log_filepath,
            **kwargs,
        )
        TabImplementation.__init__(self)


class EditingTableWindow(WindowImplementation, EditingTable):
    """A class to implement an EditingTable module inside a modal window."""

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
        number_format: str | None = None,
        log_dir: str = "logs",
        **kwargs: Any,
    ) -> None:
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            update_table_func=update_table_func,
            output=output,
            output_varselector_name=output_varselector_name,
            number_format=number_format,
            log_dir=log_dir,
            **kwargs,
        )
        WindowImplementation.__init__(self)
