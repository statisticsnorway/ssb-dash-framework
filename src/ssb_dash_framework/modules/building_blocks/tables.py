"""
editing_table.py

An EditingTable component for Dash using Dash AgGrid that requires a reason
for every cell edit. Implements Option 1: when a user edits a cell, a modal
is shown asking for a required reason. The update is only sent to the
provided update_table_func after the user confirms with a reason.

This file preserves the original design and hooks:
- Loads data via `get_data_func`.
- Calls `update_table_func(edited, reason, *dynamic_states)` on confirm.
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
    """A component for editing data using a Dash AgGrid table.

    This subclass requires the user to provide a reason for each change.
    Workflow:
      1. User edits a cell -> `cellValueChanged` fires.
      2. `capture_edit` stores the pending edit in a dcc.Store and opens a modal.
      3. User confirms with a reason -> `confirm_edit` calls `update_table_func(edit, reason, *dynamic_states)`.
      4. If user cancels, modal closes without calling the update function (grid value remains as edited in the UI).

    Attributes:
        label (str): Label for the module.
        variableselector (VariableSelector): Helper to build dynamic inputs/states.
        get_data (Callable[..., Any]): Function returning a pandas.DataFrame used to populate the grid.
        update_table_func (Callable[..., Any] | None): Function to apply updates. Must accept (edited, reason, *dynamic_states).
        module_layout (html.Div): The layout for the module (AgGrid + modal + hidden store).
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
                update_table_func(edited, reason, *dynamic_states). If None, edits are not persisted.
            output / output_varselector_name: Optional integration with VariableSelector outputs (unchanged from original).
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
        """Create the module layout.

        The layout contains:
          - dag.AgGrid for editable data.
          - dcc.Store to keep a pending edit while the modal is open.
          - dbc.Modal that asks the user to provide a reason for the edit.
        """
        layout = html.Div(
            className="editingtable",
            children=[
                dag.AgGrid(
                    defaultColDef=self.kwargs.get(
                        "defaultColDef", {"editable": True}
                    ),  # allows overriding defaultColDef externally
                    id=f"{self.module_number}-tabelleditering-table1",
                    className="ag-theme-alpine header-style-on-filter editingtable-aggrid-style",
                    **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
                ),
                # Store for the pending edit (single dict representing the edit)
                dcc.Store(id=f"{self.module_number}-pending-edit"),
                # Modal to require reason for each edit
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
        logger.debug("Generated layout")
        return layout

    def layout(self) -> html.Div:
        """Return the layout for use externally (keeps compatibility with original API)."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Register callbacks that:
           - Load data into the grid.
           - Capture a pending edit and open a modal requesting a reason.
           - Confirm the edit with a reason and call update_table_func.
           - Cancel the edit (close modal).
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            *dynamic_states,
        )
        def load_to_table(
            *dynamic_states: list[str],
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            """Load the dataframe into AgGrid's rowData and generate columnDefs.

            The get_data function is expected to accept the dynamic inputs/states in the same
            order as provided by the VariableSelector and return a pandas.DataFrame.
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
                logger.debug(
                    f"{self.label} - {self.module_number}: Data from get_data: {df}"
                )
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
                logger.debug(f"{self.label} - {self.module_number}: Returning data")
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(
                    f"{self.label} - {self.module_number}: Error loading data into table",
                    exc_info=True,
                )
                raise e

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def capture_edit(edited):
            """Capture the first edit from AgGrid and open the reason modal.

            Stores the edit dict (as supplied by dash-ag-grid cellValueChanged) in dcc.Store.
            The modal is opened and populated with a readable summary.
            """
            if not edited:
                logger.debug("capture_edit: no edited payload, raising PreventUpdate")
                raise PreventUpdate
            logger.debug(f"{self.label} - {self.module_number}: Edited payload: {edited}")
            edit = edited[0]
            details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
            # Store the entire edit dict so confirm callback can call update_table_func(edit, reason, ...)
            return edit, True, details

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State("alert_store", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def confirm_edit(n_clicks, pending_edit, reason, error_log, *dynamic_states):
            """When confirm is clicked: require a reason, call update_table_func(edit, reason, *dynamic_states),
            and append an alert describing the result.

            Returns:
                (is_open, alert_store_data) where is_open=False closes the modal.
            """
            if not n_clicks:
                logger.debug("confirm_edit: n_clicks falsy, raising PreventUpdate")
                raise PreventUpdate

            # Safeguard default for error_log in case it is None
            if error_log is None:
                error_log = []

            if not pending_edit:
                logger.error("confirm_edit called without a pending edit")
                error_log.append(create_alert("Ingen pending edit funnet", "error", ephemeral=True))
                return False, error_log

            if not reason or str(reason).strip() == "":
                logger.debug("confirm_edit: no reason provided")
                error_log.append(
                    create_alert("Årsak for endring er påkrevd", "warning", ephemeral=True)
                )
                # Keep modal open so user can enter a reason
                return True, error_log

            variable = pending_edit.get("colId")
            old_value = pending_edit.get("oldValue")
            new_value = pending_edit.get("value")

            try:
                if self.update_table_func:
                    # IMPORTANT: update_table_func is expected to accept (edited, reason, *dynamic_states)
                    self.update_table_func(pending_edit, reason, *dynamic_states)
                message = f"{variable} oppdatert fra {old_value} til {new_value}. Årsak: {reason}"
                logger.info(message)
                error_log.append(create_alert(message, "info", ephemeral=True))
                # Close modal
                return False, error_log
            except Exception:
                logger.error("Error updating table", exc_info=True)
                error_log.append(
                    create_alert(
                        f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                        "error",
                        ephemeral=True,
                    )
                )
                # Close modal regardless, but user can see the error alert
                return False, error_log

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-reason-modal", "is_open", allow_duplicate=True),
            Input(f"{self.module_number}-cancel-edit", "n_clicks"),
            prevent_initial_call=True,
        )
        def cancel_edit(n_clicks):
            """Close the modal when the user cancels.

            Note: this implementation closes the modal and DOES NOT attempt to revert the grid cell
            value programmatically. If you want to revert the grid cell to its old value on cancel,
            additional logic (for example using the grid API via dash-ag-grid or reloading the rowData)
            must be added.
            """
            if not n_clicks:
                raise PreventUpdate
            logger.debug(f"{self.label} - {self.module_number}: Edit cancelled by user")
            return False

        # Output-to-variable-selector callbacks (unchanged logic, moved after modal callbacks for readability)
        if self.output and self.output_varselector_name:
            logger.debug("Adding callback for returning clicked output to variable selector")
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
                    """Transfer clicked cell value to a VariableSelector output if the right column was clicked."""
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
                    output_value = clickdata["value"]
                    if not isinstance(output_value, str):
                        logger.debug(
                            f"{output_value} is not a string, is type {type(output_value)}"
                        )
                        logger.debug("Raised PreventUpdate")
                        raise PreventUpdate
                    logger.debug(f"Transfering {output_value} to {output_varselector_name}")
                    return output_value

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

        logger.debug("Generated callbacks")


class EditingTableTab(TabImplementation, EditingTable):
    """A class to implement an EditingTable module inside a Tab.

    Inherits the EditingTable functionality and the TabImplementation mixin.
    """

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
        """Initialize an EditingTable inside a tab.

        See EditingTable.__init__ for param descriptions.
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
        TabImplementation.__init__(self)


class EditingTableWindow(WindowImplementation, EditingTable):
    """A class to implement an EditingTable module inside a modal window.

    Inherits both EditingTable and WindowImplementation (which manages the outer modal/window behavior).
    """

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
        """Initialize an EditingTable wrapped in a window/modal.

        See EditingTable.__init__ for param descriptions.
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
