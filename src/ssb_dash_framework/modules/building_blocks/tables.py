import json
import logging
import os
import zoneinfo
from collections.abc import Callable
from datetime import datetime
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
    """A reusable and flexible Dash component for editing tabular data.

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
        - Edits are accepted immediately, logged without reason supplied, and persisted.
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
            label (str): The label for the tab or component, used for display purposes.
            inputs (list[str]): A list of input variable names that will trigger callbacks.
            states (list[str]): A list of state variable names used that will not trigger callbacks, but can be provided as args.
            get_data_func (Callable[..., Any]): A function that returns a pandas dataframe.
            update_table_func (Callable[..., Any]): A function for updating data based on edits in the AgGrid.
                Note, the update_table_func is provided with the dict from cellValueChanged[0] from the Dash AgGrid in addition the inputs and states values.
            output (str | list[str] | None, optional): Identifier for the table, used for callbacks. Defaults to None.
            output_varselector_name (str | list[str] | None, optional): Identifier for the variable selector. If list, make sure it is in the same order as output. Defaults to None.
                If `output` is provided but `output_varselector_name` is not, it will default to the value of `output`.
            number_format (str | None, optional): A d3 format string for formatting numeric values in the table. Defaults to None.
                If None, it will default to "d3.format(',.1f')(params.value).replace(/,/g, ' ')".
            log_filepath (str): Path to JSONL changelog file where edits are logged.
            justify_edit (bool): If True a 'reason for editing-window' does pops up before updating data. Defaults to True.
            **kwargs: Additional keyword arguments for the Dash AgGrid component.
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
        self.user = os.getenv("DAPLA_USER")

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
        self.tz = zoneinfo.ZoneInfo("Europe/Oslo")
        module_validator(self)

    def _is_valid(self) -> None:
        """Validate the component's configuration."""
        if self.log_filepath and not self.log_filepath.endswith(".jsonl"):
            raise ValueError(
                f"log_path needs to end with '.jsonl' in order to function. Received: {self.log_filepath}"
            )
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

    def _create_layout(self) -> html.Div:
        """Build the component layout.

        Layout includes:
        - Dash AgGrid with editable columns.
        - `dcc.Store` for pending edits.
        - `dcc.Store` for current table data.
        - optionally a modal dialog with:
            - Edit details preview.
            - Textarea for entering reason.
            - Cancel/Confirm buttons.

        Returns:
            html.Div: The container for the component.
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
        """Returns the layout for the EditingTable module.

        Because this module can be used as a a component in other modules, it needs to have a layout method that is not abstract.
        For implementations as tab or window, this method should still be overridden.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module to be displayed directly.
        """
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
            self.variableselector.get_all_inputs(),
            self.variableselector.get_all_states(),
        ]

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            Output(f"{self.module_number}-table-data", "data"),
            *dynamic_states,
        )
        def load_to_table(
            *dynamic_states: Any,
        ) -> tuple[
            list[dict[str, Any]], list[dict[str, str | bool]], list[dict[str, Any]]
        ]:
            """Loads data to the AgGrid table using supplied get_data_func function.

            Raises exception when it fails.
            """
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

            def make_table_to_varselector_connection(
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
                make_table_to_varselector_connection(
                    output_objects[i],
                    output_columns[i],
                    (
                        self.output_varselector_name[i]
                        if isinstance(self.output_varselector_name, list)
                        else self.output_varselector_name
                    ),
                )

        if self.justify_edit:
            logger.debug("Adding functionality for requiring reason for edits.")

            @callback(  # type: ignore[misc]
                Output(f"{self.module_number}-pending-edit", "data"),
                Output(f"{self.module_number}-reason-modal", "is_open"),
                Output(f"{self.module_number}-edit-details", "children"),
                Output(f"{self.module_number}-edit-reason", "value"),
                Input(
                    f"{self.module_number}-tabelleditering-table1", "cellValueChanged"
                ),
                prevent_initial_call=True,
            )
            def capture_edit(
                edited: list[dict[str, Any]],
            ) -> tuple[dict[str, Any], bool, str, str]:
                if not edited:
                    raise PreventUpdate
                logger.info(edited)
                edit = edited[0]
                details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
                return edit, True, details, ""

            @callback(  # type: ignore[misc]
                Output(
                    f"{self.module_number}-reason-modal",
                    "is_open",
                    allow_duplicate=True,
                ),
                Output("alert_store", "data", allow_duplicate=True),
                Output(
                    f"{self.module_number}-table-data", "data", allow_duplicate=True
                ),
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
                pending_edit: dict[str, Any],
                reason: str,
                error_log: list[dict[str, Any]],
                table_data: list[dict[str, Any]],
                *dynamic_states: Any,
            ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
                if not (n_clicks or n_submit):
                    raise PreventUpdate
                if not pending_edit:
                    error_log = [
                        create_alert(
                            "Ingen pending edit funnet", "error", ephemeral=True
                        ),
                        *error_log,
                    ]
                    return False, error_log, table_data
                if not reason or str(reason).strip() == "":
                    error_log = [
                        create_alert(
                            "Årsak for endring er påkrevd", "warning", ephemeral=True
                        ),
                        *error_log,
                    ]
                    return True, error_log, table_data

                edit_with_reason = dict(pending_edit)
                edit_with_reason["reason"] = reason.replace("\n", "")
                edit_with_reason["user"] = self.user
                edit_with_reason["change_event"] = "manual"

                aware_timestamp = datetime.now(self.tz)  # timezone-aware
                naive_timestamp = aware_timestamp.replace(tzinfo=None)  # drop tzinfo
                edit_with_reason["timestamp"] = naive_timestamp

                logger.debug(edit_with_reason)
                if self.log_filepath:
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(
                            json.dumps(
                                edit_with_reason, ensure_ascii=False, default=str
                            )
                            + "\n"
                        )

                if self.update_table_func:
                    variable = edit_with_reason["colId"]
                    old_value = edit_with_reason["oldValue"]
                    new_value = edit_with_reason["value"]
                    logger.info("Running update_table_func")
                    try:
                        self.update_table_func(edit_with_reason, *dynamic_states)
                        error_log = [
                            create_alert(
                                f"{variable} oppdatert fra {old_value} til {new_value}",
                                "info",
                                ephemeral=True,
                            ),
                            *error_log,
                        ]
                    except Exception:
                        logger.error("Error updating table", exc_info=True)
                        error_log = [
                            create_alert(
                                f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                                "error",
                                ephemeral=True,
                            ),
                            *error_log,
                        ]

                new_table_data = self._update_row(table_data, pending_edit)
                return False, error_log, new_table_data

            @callback(  # type: ignore[misc]
                Output(
                    f"{self.module_number}-reason-modal",
                    "is_open",
                    allow_duplicate=True,
                ),
                Output(
                    f"{self.module_number}-tabelleditering-table1",
                    "rowData",
                    allow_duplicate=True,
                ),
                Input(f"{self.module_number}-cancel-edit", "n_clicks"),
                State(f"{self.module_number}-table-data", "data"),
                prevent_initial_call=True,
            )
            def cancel_edit(
                n_clicks: int | None, table_data: list[dict[str, Any]]
            ) -> tuple[bool, list[dict[str, Any]]]:
                if not n_clicks:
                    raise PreventUpdate
                return False, table_data

        else:
            logger.debug("Adding functionality for immediate edits.")

            @callback(  # type: ignore[misc]
                Output("alert_store", "data", allow_duplicate=True),
                Output(
                    f"{self.module_number}-table-data", "data", allow_duplicate=True
                ),  # Somewhat sure this is not needed
                Input(
                    f"{self.module_number}-tabelleditering-table1", "cellValueChanged"
                ),
                State("alert_store", "data"),
                State(f"{self.module_number}-table-data", "data"),
                *dynamic_states,
                prevent_initial_call=True,
            )
            def immediate_edit(
                edited: list[dict[str, Any]],
                error_log: list[dict[str, Any]],
                table_data: list[dict[str, Any]],
                *dynamic_states: Any,
            ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
                if not edited:
                    raise PreventUpdate
                edit = edited[0]

                aware_timestamp = datetime.now(self.tz)  # timezone-aware
                naive_timestamp = aware_timestamp.replace(tzinfo=None)  # drop tzinfo
                edit["timestamp"] = naive_timestamp
                if self.log_filepath:
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(
                            json.dumps(edit, ensure_ascii=False, default=str) + "\n"
                        )

                if self.update_table_func:
                    variable = edit["colId"]
                    old_value = edit["oldValue"]
                    new_value = edit["value"]
                    logger.info("Running update_table_func")
                    try:
                        self.update_table_func(edit, *dynamic_states)
                        error_log = [
                            create_alert(
                                f"{variable} oppdatert fra {old_value} til {new_value}",
                                "info",
                                ephemeral=True,
                            ),
                            *error_log,
                        ]

                    except Exception:
                        logger.error("Error updating table", exc_info=True)
                        error_log = [
                            create_alert(
                                f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                                "error",
                                ephemeral=True,
                            ),
                            *error_log,
                        ]
                new_table_data = self._update_row(table_data, edit)
                logger.debug("Finished update")
                return error_log, new_table_data

    def _update_row(
        self, table_data: list[dict[str, Any]], edit: dict[str, Any]
    ) -> list[dict[str, Any]]:
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
    """EditingTable embedded in a tab container."""

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
        """Initialize the EditingTableTab.

        Args:
            label (str): The label for the tab or component, used for display purposes.
            inputs (list[str]): A list of input variable names that will trigger callbacks.
            states (list[str]): A list of state variable names used that will not trigger callbacks, but can be provided as args.
            get_data_func (Callable[..., Any]): A function that returns a pandas dataframe.
            update_table_func (Callable[..., Any]): A function for updating data based on edits in the AgGrid.
                Note, the update_table_func is provided with the dict from cellValueChanged[0] from the Dash AgGrid in addition the inputs and states values.
            output (str | list[str] | None, optional): Identifier for the table, used for callbacks. Defaults to None.
            output_varselector_name (str | list[str] | None, optional): Identifier for the variable selector. If list, make sure it is in the same order as output. Defaults to None.
                If `output` is provided but `output_varselector_name` is not, it will default to the value of `output`.
            number_format (str | None, optional): A d3 format string for formatting numeric values in the table. Defaults to None.
                If None, it will default to "d3.format(',.1f')(params.value).replace(/,/g, ' ')".
            log_filepath (str): Path to JSONL changelog file where edits are logged.
            justify_edit (bool): If True a 'reason for editing-window' does pops up before updating data. Defaults to True.
            **kwargs: Additional keyword arguments for the Dash AgGrid component.
        """
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
    """A class to implement an EditingTable module inside a modal."""

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
        """Initialize the EditingTableWindow.

        Args:
            label (str): The label for the tab or component, used for display purposes.
            inputs (list[str]): A list of input variable names that will trigger callbacks.
            states (list[str]): A list of state variable names used that will not trigger callbacks, but can be provided as args.
            get_data_func (Callable[..., Any]): A function that returns a pandas dataframe.
            update_table_func (Callable[..., Any]): A function for updating data based on edits in the AgGrid.
                Note, the update_table_func is provided with the dict from cellValueChanged[0] from the Dash AgGrid in addition the inputs and states values.
            output (str | list[str] | None, optional): Identifier for the table, used for callbacks. Defaults to None.
            output_varselector_name (str | list[str] | None, optional): Identifier for the variable selector. If list, make sure it is in the same order as output. Defaults to None.
                If `output` is provided but `output_varselector_name` is not, it will default to the value of `output`.
            number_format (str | None, optional): A d3 format string for formatting numeric values in the table. Defaults to None.
                If None, it will default to "d3.format(',.1f')(params.value).replace(/,/g, ' ')".
            log_filepath (str): Path to JSONL changelog file where edits are logged.
            justify_edit (bool): If True a 'reason for editing-window' does pops up before updating data. Defaults to True.
            **kwargs: Additional keyword arguments for the Dash AgGrid component.
        """
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
