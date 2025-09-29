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

This file preserves the original design and hooks:
- Loads data via `get_data_func`.
- Calls `update_table_func(edit_with_reason, *dynamic_states)` on confirm.
- Uses VariableSelector to construct dynamic inputs/states for callbacks.
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
    """A component for editing data using a Dash AgGrid table that enforces reasons.

    Workflow:
      1. User edits a cell -> `cellValueChanged` fires.
      2. `capture_edit` stores the pending edit in a dcc.Store and opens a modal.
         The modal textarea value is reset each time.
      3. User confirms with a reason:
           - The reason is injected into the edit dict as key "reason".
           - `update_table_func(edit_with_reason, *dynamic_states)` is called.
           - On success, the internal stored rowData (table_data store) is updated
             to reflect the accepted change.
      4. If the user cancels:
           - The grid is reverted to the last persisted rowData (from the store).
           - No update function is called.

    Important:
      - `update_table_func` must accept the edit dict that includes "reason" (e.g. def f(edit_with_reason, *dynamic_states): ...).
      - Grid rows should include a stable id field (e.g., "uuid" or "row_id") to make updates robust;
        when present those are used to find the row to update in the stored table_data.
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
        """Initialize the EditingTable component.
    
        Args:
            label: Display label for module.
            inputs: List of input IDs (used by VariableSelector).
            states: List of state IDs (used by VariableSelector).
            get_data_func: Callable returning a pandas.DataFrame. Called with selected inputs then states.
            update_table_func: Callable to perform the actual update. Must accept (edit_with_reason, *dynamic_states).
            output / output_varselector_name: Optional variableselector integration.
            number_format: Optional d3 number format string for numeric columns.
            **kwargs: Extra keyword args passed to dag.AgGrid (except defaultColDef which is handled).
        """
        self.kwargs = kwargs
    
        self.module_number = EditingTable._id_number
        self.module_name = self.__class__.__name__
        EditingTable._id_number += 1
        self.icon = "📒"
        self.label = label
        self.output = output
        self.output_varselector_name = output_varselector_name or output
    
        if number_format is None:
            self.number_format = "d3.format(',.1f')(params.value).replace(/,/g, ' ')"
        else:
            self.number_format = number_format
    
        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.get_data = get_data_func
        # keep for compatibility - unused directly here but preserved
        self.get_data_args = [x for x in self.variableselector.selected_variables]
        self.update_table_func = update_table_func
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
    
        # --- Logging setup ---
        os.makedirs("logs", exist_ok=True)
        self.log_filename = os.path.join(
            "logs",
            f"log_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl"
        )
    
        module_validator(self)


    def _is_valid(self) -> None:
        """Validate provided arguments and configuration."""
        if not isinstance(self.label, str):
            raise TypeError(
                f"label {self.label} is not a string, is type {type(self.label)}"
            )
        if self.output is not None and self.output_varselector_name is not None:
            if isinstance(self.output, str) and not isinstance(
                self.output_varselector_name, str
            ):
                raise TypeError(
                    f"output is a string while output_varselector_name {self.output_varselector_name} is not a string, is type {type(self.output_varselector_name)}"
                )
            elif isinstance(self.output, list) and isinstance(
                self.output_varselector_name, list
            ):
                if len(self.output) != len(self.output_varselector_name):
                    raise ValueError(
                        f"output {self.output} and output_varselector_name {self.output_varselector_name} are not the same length"
                    )

    def _create_layout(self, **kwargs: Any) -> html.Div:
        """Create the module layout (AgGrid + modal + stores)."""
        layout = html.Div(
            className="editingtable",
            children=[
                dag.AgGrid(
                    defaultColDef=self.kwargs.get("defaultColDef", {"editable": True}),
                    id=f"{self.module_number}-tabelleditering-table1",
                    className="ag-theme-alpine header-style-on-filter editingtable-aggrid-style",
                    **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
                ),
                # Store holding the pending edit dict (single edit)
                dcc.Store(id=f"{self.module_number}-pending-edit"),
                # Store holding the last persisted rowData (used to revert on cancel)
                dcc.Store(id=f"{self.module_number}-table-data"),
                # Reason modal
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
        logger.debug("Generated layout with modal and stores")
        return layout

    def layout(self) -> html.Div:
        """Return layout for external use (preserves original API)."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Register Dash callbacks for loading data, capturing edits, confirming and cancelling."""
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        # -------------------------
        # Load data into the table
        # -------------------------
        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            Output(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
        )
        def load_to_table(*dynamic_states: list[str]):
            """Load data via get_data_func and populate columnDefs.

            Also stores the loaded rowData into the table_data store for undo capability.
            """
            logger.debug(
                "Args:\n"
                + "\n".join(
                    [
                        f"dynamic_state_{i}: {state}"
                        for i, state in enumerate(dynamic_states)
                    ]
                )
            )
            try:
                df = self.get_data(*dynamic_states)
                logger.debug(f"{self.label} - {self.module_number}: Data from get_data: {df}")
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
                logger.debug(f"{self.label} - {self.module_number}: Returning data")
                return row_data, columns, row_data
            except Exception as e:
                logger.error(
                    f"{self.label} - {self.module_number}: Error loading data into table",
                    exc_info=True,
                )
                raise e

        # -----------------------------------
        # Step 1: Capture edit and open modal
        # -----------------------------------
        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Output(f"{self.module_number}-edit-reason", "value"),
            Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def capture_edit(edited):
            """Capture the edit blob from AgGrid and open the modal asking for reason.

            We also reset the textarea value to empty so previous reasons are not reused.
            """
            if not edited:
                logger.debug("capture_edit: no edited payload, raising PreventUpdate")
                raise PreventUpdate
            logger.debug(f"{self.label} - {self.module_number}: Edited payload: {edited}")
            edit = edited[0]
            details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
            # store full edited dict; textarea reset to ""
            return edit, True, details, ""

        # -----------------------------------
        # Step 2: Confirm edit with reason
        # -----------------------------------
        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Output(f"{self.module_number}-table-data", "data", allow_duplicate=True),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State("alert_store", "data"),
            State(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def confirm_edit(n_clicks, pending_edit, reason, error_log, table_data, *dynamic_states):
            """When Confirm is clicked:
              - Require a non-empty reason.
              - Inject 'reason' into the edit dict and call update_table_func(edit_with_reason, *dynamic_states).
              - Update the stored table_data to reflect the accepted change so future cancels revert correctly.
            Returns:
              (is_open, alert_store_data, new_table_data)
            """
            if not n_clicks:
                logger.debug("confirm_edit: n_clicks falsy, raising PreventUpdate")
                raise PreventUpdate

            if error_log is None:
                error_log = []

            if not pending_edit:
                logger.error("confirm_edit called without a pending edit")
                error_log.append(create_alert("Ingen pending edit funnet", "error", ephemeral=True))
                return False, error_log, table_data

            if not reason or str(reason).strip() == "":
                logger.debug("confirm_edit: no reason provided")
                error_log.append(create_alert("Årsak for endring er påkrevd", "warning", ephemeral=True))
                # keep modal open
                return True, error_log, table_data

            # Inject reason into a copy of the edit dict
            edit_with_reason = dict(pending_edit)
            edit_with_reason["reason"] = reason

            edit_with_reason["timestamp"] = datetime.utcnow().isoformat()

            # Write to log file (append mode)
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_filename = os.path.join(
                log_dir,
                f"log_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl"
            )
            
            with open(log_filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(edit_with_reason, ensure_ascii=False) + "\n")

            variable = pending_edit.get("colId")
            old_value = pending_edit.get("oldValue")
            new_value = pending_edit.get("value")

            try:
                if self.update_table_func:
                    # IMPORTANT: update_table_func should accept the edit dict with 'reason'
                    self.update_table_func(edit_with_reason, *dynamic_states)
                msg = f"{variable} oppdatert fra {old_value} til {new_value}. Årsak: {reason}"
                logger.info(msg)
                error_log.append(create_alert(msg, "info", ephemeral=True))

                # Update table_data store so that future cancel will revert to this accepted state
                new_table_data = list(table_data) if table_data else []

                # Determine row identity: prefer stable id in pending_edit['data'] (uuid, row_id), else rowIndex
                row_obj = pending_edit.get("data") or {}
                updated = False
                if new_table_data:
                    # try 'uuid'
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
                        # fallback to rowIndex if provided
                        row_index = pending_edit.get("rowIndex")
                        if row_index is not None and 0 <= int(row_index) < len(new_table_data):
                            new_table_data[int(row_index)] = row_obj
                            updated = True

                if not updated:
                    # If we couldn't match/update, append/replace conservatively: try to keep table_data length
                    # (This is defensive; ideally rows contain a stable id.)
                    logger.debug("confirm_edit: could not match row to table_data by uuid/row_id/rowIndex; trying to best-effort replace")
                    if pending_edit.get("rowIndex") is not None and table_data:
                        idx = int(pending_edit.get("rowIndex"))
                        if 0 <= idx < len(new_table_data):
                            new_table_data[idx] = row_obj
                        else:
                            new_table_data.append(row_obj)
                    else:
                        # append as last resort
                        new_table_data.append(row_obj)

                return False, error_log, new_table_data

            except Exception:
                logger.error("Error updating table", exc_info=True)
                error_log.append(
                    create_alert(
                        f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                        "error",
                        ephemeral=True,
                    )
                )
                # Close modal but leave table_data unchanged
                return False, error_log, table_data

        # -----------------------------------
        # Step 3: Cancel edit -> revert grid
        # -----------------------------------
        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output(f"{self.module_number}-tabelleditering-table1", "rowData", allow_duplicate=True),
            Input(f"{self.module_number}-cancel-edit", "n_clicks"),
            State(f"{self.module_number}-table-data", "data"),
            prevent_initial_call=True,
        )
        def cancel_edit(n_clicks, table_data):
            """Cancel the pending edit and revert grid rowData to the last persisted table_data.

            Because we keep the last persisted rowData in the table_data store, reverting is simply
            returning that data as the grid's rowData.
            """
            if not n_clicks:
                raise PreventUpdate
            if table_data is None:
                # Nothing to revert to; just close modal
                logger.debug("cancel_edit: no table_data available to revert to")
                return False, PreventUpdate
            # close modal and send persisted rowData back to grid (undoing the in-memory edit)
            return False, table_data

        # -------------------------
        # Output-to-variable-selector
        # -------------------------
        if self.output and self.output_varselector_name:
            logger.debug("Adding callback for returning clicked output to variable selector")
            if isinstance(self.output, str) and isinstance(self.output_varselector_name, str):
                output_objects = [
                    self.variableselector.get_output_object(variable=self.output_varselector_name)
                ]
                output_columns = [self.output]
            elif isinstance(self.output, list) and isinstance(self.output_varselector_name, list):
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

            def make_table_to_main_table_callback(output: Output, column: str, output_varselector_name: str) -> None:
                @callback(  # type: ignore[misc]
                    output,
                    Input(f"{self.module_number}-tabelleditering-table1", "cellClicked"),
                    prevent_initial_call=True,
                )
                def table_to_main_table(clickdata: dict[str, Any]) -> str:
                    """Transfer clicked cell value to a VariableSelector output if the right column was clicked."""
                    logger.debug(
                        f"Args:\nclickdata: {clickdata}\ncolumn: {column}\noutput_varselector_name: {output_varselector_name}"
                    )
                    if not clickdata:
                        raise PreventUpdate
                    if clickdata["colId"] != column:
                        raise PreventUpdate
                    output_value = clickdata["value"]
                    if not isinstance(output_value, str):
                        raise PreventUpdate
                    return output_value

            for i in range(len(output_objects)):
                make_table_to_main_table_callback(
                    output_objects[i],
                    output_columns[i],
                    (self.output_varselector_name[i] if isinstance(self.output_varselector_name, list) else self.output_varselector_name),
                )

        logger.debug("Generated callbacks")


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
        **kwargs: Any,
    ) -> None:
        """Initialize the EditingTableTab.

        We explicitly initialize EditingTable first (with its expected params)
        and then call TabImplementation.__init__(self) with no extra args to avoid
        passing unexpected kwargs into TabImplementation.
        """
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
            **kwargs,
        )
        # Call TabImplementation init without forwarding the EditingTable args
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
        **kwargs: Any,
    ) -> None:
        """Initialize the EditingTableWindow.

        As above, explicitly call EditingTable.__init__ and then WindowImplementation.__init__(self).
        """
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
            **kwargs,
        )
        WindowImplementation.__init__(self)
