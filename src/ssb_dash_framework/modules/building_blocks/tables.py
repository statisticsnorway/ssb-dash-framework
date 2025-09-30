"""
editing_table.py.
An EditingTable component for Dash using Dash AgGrid that requires a reason
for every cell edit (if justify_edit=True).
Implements Option 1 with strict behavior:
- After editing a cell, a modal is shown asking for a required reason.
- The edit is not persisted until the user confirms with a reason.
- If the user cancels, the edit is undone (the grid is reverted to the last
  persisted rowData).
- The reason is inserted into the edit dictionary (key "reason") which is
  passed to update_table_func(edit_with_reason, *dynamic_states).

If justify_edit=False:
- Edits are persisted immediately, no reason is required and no modal is shown.

Additional features:
- User can specify log directory.
- Changes modal textarea auto-focuses.
- Pressing Enter in the textarea triggers Confirm.
This file preserves the original design and hooks:
- Loads data via `get_data_func`.
- Calls `update_table_func(edit, *dynamic_states)` on confirm.
- Uses VariableSelector to construct dynamic inputs/states for callbacks.
"""
import json
import logging
import time
from collections.abc import Callable
from typing import Any
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class EditingTable:
    """A reusable Dash component for editing tabular data with optional reason enforcement.
    This component renders a Dash AgGrid table where each edit can be
    optionally confirmed with a user-provided reason before being persisted.

    Workflow when justify_edit=True:
        1. Data is loaded into AgGrid via `get_data_func`.
        2. When a cell is edited, a modal opens requesting a reason.
        3. If confirmed:
            - The edit is logged (with reason and timestamp).
            - The `update_table_func` is optionally invoked.
            - The in-memory table data is updated.
        4. If cancelled:
            - The modal closes and the table reverts to its last saved state.

    Workflow when justify_edit=False:
        - Edits are accepted immediately, logged without reason, and persisted.

    Attributes:
        label (str): Display label for the component.
        output (str | list[str] | None): Optional identifier(s) for outputs.
        output_varselector_name (str | list[str] | None): Names for variable selector outputs.
        variableselector (VariableSelector): Handles inputs and states for callbacks.
        get_data_func (Callable): Function to fetch data for populating the table.
        log_filepath (str): Optional path to the JSONL file used for logging edits. If none, no logging occurs.
        update_table_func (Callable | None): Function to apply edits to the backend.
        justify_edit (bool): Whether a reason is required for edits (default True).
        module_layout (html.Div): Dash layout containing AgGrid, modal, and stores.
        number_format (str): JavaScript d3-format string for numeric formatting.
    """

    _id_number: int = 0

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        log_filepath: str | None = None,
        update_table_func: Callable[..., Any] | None = None,
        output: str | list[str] | None = None,
        output_varselector_name: str | list[str] | None = None,
        number_format: str | None = None,
        justify_edit: bool = True,
        **kwargs: Any,
    ) -> None:        
        """Initialize the EditingTable component.

        Args:
            label: Display label for the component.
            inputs: List of variable names to be used as callback inputs.
            states: List of variable names to be used as callback states.
            get_data_func: Function that returns a pandas DataFrame for the table.
            log_filepath: Path to JSONL changelog file where edits are logged.
            update_table_func: Optional function to handle edits on confirm.
            output: Optional callback output identifier(s).
            output_varselector_name: Optional variable selector names for outputs.
            number_format: Optional d3-format string for numeric values.
            justify_edit: Defaults True. If False reason for editing-window does not pop up.
            **kwargs: Extra keyword arguments passed to AgGrid configuration.
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
        self.justify_edit = justify_edit

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
        """Validate the component's configuration.

        Checks that:
        - `label` is a string.
        - If both `output` and `output_varselector_name` are provided:
          - Their types are compatible.
          - Their lengths match if they are lists.
        Raises TypeError or ValueError if invalid.
        """
        if not isinstance(self.label, str):
            raise TypeError(f"label {self.label} is not a string")
        if self.output is not None and self.output_varselector_name is not None:
            if isinstance(self.output, str) and not isinstance(
                self.output_varselector_name, str
            ):
                raise TypeError("output_varselector_name type mismatch")
            elif isinstance(self.output, list) and isinstance(
                self.output_varselector_name, list
            ):
                if len(self.output) != len(self.output_varselector_name):
                    raise ValueError(
                        "output and output_varselector_name length mismatch"
                    )

    def _create_layout(self, **kwargs: Any) -> html.Div:
        """Build the component layout.

        Layout includes:
        - Dash AgGrid with editable columns.
        - `dcc.Store` for pending edits.
        - `dcc.Store` for current table data.
        - Modal dialog with:
            - Edit details preview.
            - Textarea for entering reason.
            - Cancel/Confirm buttons.
        Args:
            **kwargs: Additional keyword arguments for AgGrid and layout customization.

        Returns:
            html.Div: The root container for the component.
        """

        children = [
            dag.AgGrid(
                defaultColDef=self.kwargs.get("defaultColDef", {"editable": True}),
                id=f"{self.module_number}-tabelleditering-table1",
                className="ag-theme-alpine header-style-on-filter editingtable-aggrid-style",
                **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
            ),
            dcc.Store(id=f"{self.module_number}-table-data"),
        ]

        if self.justify_edit:
            children += [
                dcc.Store(id=f"{self.module_number}-pending-edit"),
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
                                    n_submit=0,
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
            ]

        return html.Div(className="editingtable", children=children)

    def layout(self) -> html.Div:
        """Return the component layout for integration into Dash apps."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Register Dash callbacks for the component.

        Defines callback chains for:
        - Loading data into AgGrid (`load_to_table`).
        - Capturing edits and opening the modal (`capture_edit`).
        - Confirming edits (logging + updating table data) (`confirm_edit`).
        - Cancelling edits (reverting table to saved state) (`cancel_edit`).
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            Output(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
        )
        def load_to_table(*dynamic_states: Any):
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
                row_data = df.to_dict("records")
                return row_data, columns, row_data
            except Exception as e:
                logger.error("Error loading data", exc_info=True)
                raise e
        
        if self.output and self.output_varselector_name:
            logger.debug(
                "Adding callback for returning clicked output to variable selector"
            )
            if isinstance(self.output, str) and isinstance(
                self.output_varselector_name, str
            ):
                output_objects = [
                    self.variableselector.get_output_object(
                        variable=self.output_varselector_name
                    )
                ]
                output_columns = [self.output]
            elif isinstance(self.output, list) and isinstance(
                self.output_varselector_name, list
            ):
                output_objects = [
                    self.variableselector.get_output_object(variable=var)
                    for var in self.output_varselector_name
                ]
                output_columns = self.output
            else:
                logger.error(
                    f"output {self.output} is not a string or list, is type {type(self.output)}"
                )
                raise TypeError(
                    f"output {self.output} is not a string or list, is type {type(self.output)}"
                )
            logger.debug(f"Output object: {output_objects}")

            def make_table_to_main_table_callback(
                output: Output, column: str, output_varselector_name: str
            ) -> None:
                @callback(  # type: ignore[misc]
                    output,
                    Input(
                        f"{self.module_number}-tabelleditering-table1", "cellClicked"
                    ),
                    prevent_initial_call=True,
                )
                def table_to_main_table(clickdata: dict[str, Any]) -> str:
                    logger.debug(
                        f"Args:\n"
                        f"clickdata: {clickdata}\n"
                        f"column: {column}\n"
                        f"output_varselector_name: {output_varselector_name}"
                    )
                    if not clickdata:
                        logger.debug("Raised PreventUpdate")
                        raise PreventUpdate
                    if clickdata["colId"] != column:
                        logger.debug("Raised PreventUpdate")
                        raise PreventUpdate
                    output = clickdata["value"]
                    if not isinstance(output, str):
                        logger.debug(
                            f"{output} is not a string, is type {type(output)}"
                        )
                        logger.debug("Raised PreventUpdate")
                        raise PreventUpdate
                    logger.debug(f"Transfering {output} to {output_varselector_name}")
                    return output

            for i in range(len(output_objects)):
                make_table_to_main_table_callback(
                    output_objects[i],
                    output_columns[i],
                    (
                        self.output_varselector_name[i]
                        if isinstance(self.output_varselector_name, list)
                        else self.output_varselector_name
                    ),
                )

        if self.justify_edit:
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
                logger.info(edited)
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
            def confirm_edit(
                n_clicks: int,
                n_submit: int,
                pending_edit: dict,
                reason: str,
                error_log: list,
                table_data: list,
                *dynamic_states: Any
            ):
                if not (n_clicks or n_submit):
                    raise PreventUpdate
                if error_log is None:
                    error_log = []
                if not pending_edit:
                    error_log.append(
                        create_alert("Ingen pending edit funnet", "error", ephemeral=True)
                    )
                    return False, error_log, table_data
                if not reason or str(reason).strip() == "":
                    error_log.append(
                        create_alert(
                            "Årsak for endring er påkrevd", "warning", ephemeral=True
                        )
                    )
                    return True, error_log, table_data

                edit_with_reason = dict(pending_edit)
                edit_with_reason["reason"] = reason
                edit_with_reason["timestamp"] = int(time.time() * 1000)
                logger.debug(edit_with_reason)
                if self.log_filepath:
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(json.dumps(edit_with_reason, ensure_ascii=False) + "\n")

                if self.update_table_func:
                    variable = edit_with_reason["colId"]
                    old_value = edit_with_reason["oldValue"]
                    new_value = edit_with_reason["value"]
                    logger.info("Running update_table_func")
                    try:
                        self.update_table_func(edit_with_reason, *dynamic_states)
                        error_log.append(
                            create_alert(
                                f"{variable} oppdatert fra {old_value} til {new_value}",
                                "info",
                                ephemeral=True,
                            )
                        )
                    except Exception:
                        logger.error("Error updating table", exc_info=True)
                        error_log.append(
                            create_alert(
                                f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                                "error",
                                ephemeral=True,
                            )
                        )

                new_table_data = self._update_row(table_data, pending_edit)
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

        else:
            @callback(
                Output("alert_store", "data", allow_duplicate=True),
                Output(f"{self.module_number}-table-data", "data", allow_duplicate=True), # Somewhat sure this is not needed
                Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
                State("alert_store", "data"),
                State(f"{self.module_number}-table-data", "data"),
                *dynamic_states,
                prevent_initial_call=True,
            )
            def immediate_edit(edited, error_log, table_data, *dynamic_states):
                if not edited:
                    raise PreventUpdate
                edit = edited[0]
                edit["timestamp"] = int(time.time() * 1000)
                if self.log_filepath:
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(json.dumps(edit, ensure_ascii=False) + "\n")

                if self.update_table_func:
                    variable = edit["colId"]
                    old_value = edit["oldValue"]
                    new_value = edit["value"]
                    logger.info("Running update_table_func")
                    try:
                        self.update_table_func(edit, *dynamic_states)
                        error_log.append(
                            create_alert(
                                f"{variable} oppdatert fra {old_value} til {new_value}",
                                "info",
                                ephemeral=True,
                            )
                        )
                    except Exception:
                        logger.error("Error updating table", exc_info=True)
                        error_log.append(
                            create_alert(
                                f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                                "error",
                                ephemeral=True,
                            )
                        )
                new_table_data = self._update_row(table_data, edit)
                logger.debug("Finished update")
                return error_log, new_table_data

    def _update_row(self, table_data: list, edit: dict) -> list:
        """Helper to update table row by uuid, row_id, or rowIndex."""
        new_data = list(table_data) if table_data else []
        row_obj = edit.get("data") or {}
        updated = False
        uid = row_obj.get("uuid") if isinstance(row_obj, dict) else None
        rid = row_obj.get("row_id") if isinstance(row_obj, dict) else None
        if uid is not None:
            for i, r in enumerate(new_data):
                if r.get("uuid") == uid:
                    new_data[i] = row_obj
                    updated = True
                    break
        elif rid is not None:
            for i, r in enumerate(new_data):
                if r.get("row_id") == rid:
                    new_data[i] = row_obj
                    updated = True
                    break
        else:
            row_index = edit.get("rowIndex")
            if row_index is not None and 0 <= int(row_index) < len(new_data):
                new_data[int(row_index)] = row_obj
                updated = True
        if not updated:
            new_data.append(row_obj)
        return new_data


class EditingTableTab(TabImplementation, EditingTable):
    """EditingTable embedded in a tab container.

    Inherits from both `EditingTable` and `TabImplementation` so that
    the component can be displayed as a tab in a multi-tab layout.
    """

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        log_filepath: str | None = None,
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
        number_format: str | None = None,
        justify_edit: bool = True,
        **kwargs: Any,
    ) -> None:
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            log_filepath=log_filepath,
            update_table_func=update_table_func,
            output=output,
            output_varselector_name=output_varselector_name,
            number_format=number_format,
            justify_edit=justify_edit,
            **kwargs,
        )
        TabImplementation.__init__(self)


class EditingTableWindow(WindowImplementation, EditingTable):
    """EditingTable embedded in a modal window.

    Inherits from both `EditingTable` and `WindowImplementation` so that
    the component can be displayed inside a popup/modal context.

    Args:
        log_filepath (str): Filepath for logs. Must be .jsonl.
    """

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        log_filepath: str | None = None,
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
        number_format: str | None = None,
        justify_edit: bool = True,
        **kwargs: Any,
    ) -> None:
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            log_filepath=log_filepath,
            update_table_func=update_table_func,
            output=output,
            output_varselector_name=output_varselector_name,
            number_format=number_format,
            justify_edit=justify_edit,
            **kwargs,
        )
        WindowImplementation.__init__(self)
