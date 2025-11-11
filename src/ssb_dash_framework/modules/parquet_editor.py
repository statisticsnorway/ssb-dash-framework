import json
import logging
import os
import zoneinfo
from datetime import datetime
from pathlib import Path
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

from ..setup.variableselector import VariableSelector
from ..utils.alert_handler import create_alert
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class ParquetEditor:
    """Simple module with the sole purpose of editing a parquet file.

    Accomplishes this functionality by writing a processlog in a json lines file and recording any edits in this jsonl file.

    Args:
        id_vars: A list of columns that together form a unique identifier for a single row in your data.
        file_path: The path to the parquet file you want to edit.

    Notes:
        The process log is automatically created in the correct folder structure and is named after your parquet file.
    """

    _id_number: int = 0

    def __init__(self, id_vars: list[str], file_path: str) -> None:
        """Initializes the module and makes a few validation checks before moving on."""
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1

        self.user = os.getenv("DAPLA_USER")
        self.tz = zoneinfo.ZoneInfo("Europe/Oslo")
        self.id_vars = id_vars
        self.variable_selector = VariableSelector(
            selected_inputs=id_vars, selected_states=[]
        )
        self.file_path = file_path
        path = Path(file_path)

        self.log_filepath = (
            path.parent.parent
            / "logg"
            / "prosessdata"
            / path.with_suffix(".jsonl").name
        )
        self.label = path.stem

        self.module_layout = self._create_layout()
        self._is_valid()
        module_validator(self)
        self.module_callbacks()

    def _is_valid(self) -> None:
        if not isinstance(self.id_vars, list):
            raise TypeError(
                f"Argument 'id_vars' must be a list. Received: {type(self.id_vars)}"
            )
        for element in self.id_vars:
            if not isinstance(element, str):
                raise TypeError(
                    f"Argument 'id_vars' must be a list containing only strings. Received: {element} which is a {type(element)}"
                )
        if not isinstance(self.file_path, str):
            raise TypeError(
                f"Argument 'file_path' must be a string. Received: {type(self.file_path)}"
            )
        data = self.get_data()
        duplicates = data.duplicated(subset=self.id_vars, keep=False)
        if duplicates.any():
            raise ValueError(
                f"The dataframe seems to have duplicates on the columns '{self.id_vars}'. For the processlog to be useable the combination of id_vars needs to be unique for a each row.\n Duplicated rows:\n{duplicates}"
            )

    def get_data(self) -> pd.DataFrame:
        """Reads the parquet file at the supplied file path."""
        return pd.read_parquet(self.file_path)

    def _create_layout(self) -> html.Div:
        reason_modal = [
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
            dcc.Store(id=f"{self.module_number}-simple-table-data-store"),
        ]
        return html.Div(
            [*reason_modal, dag.AgGrid(id=f"{self.module_number}-simple-table")]
        )

    def layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(self.module_layout)

    def module_callbacks(self) -> None:
        """Sets up the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-simple-table", "rowData"),
            Output(f"{self.module_number}-simple-table", "columnDefs"),
            Output(f"{self.module_number}-simple-table-data-store", "data"),
            *self.variable_selector.get_all_inputs(),
        )
        def load_data_to_table(
            *args: Any,
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            data = self.get_data()
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "editable": True if col not in self.id_vars else False,
                }
                for col in data.columns
            ]
            return (
                data.to_dict(orient="records"),
                columns,
                data.to_dict(orient="records"),
            )

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Output(f"{self.module_number}-edit-reason", "value"),
            Input(f"{self.module_number}-simple-table", "cellValueChanged"),
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
                f"{self.module_number}-simple-table-data-store",
                "data",
                allow_duplicate=True,
            ),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            Input(f"{self.module_number}-edit-reason", "n_submit"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State("alert_store", "data"),
            State(f"{self.module_number}-simple-table-data-store", "data"),
            *self.variable_selector.get_all_inputs(),
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
                    create_alert("Ingen pending edit funnet", "error", ephemeral=True),
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

            change_to_log: dict[str, Any] = {}
            change_to_log["row_identifier"] = {
                str(x): pending_edit["data"][x] for x in self.id_vars
            }
            change_to_log["colId"] = pending_edit["colId"]
            change_to_log["oldValue"] = pending_edit["oldValue"]
            change_to_log["value"] = pending_edit["value"]
            change_to_log["reason"] = reason.replace("\n", "")
            change_to_log["user"] = self.user
            change_to_log["change_event"] = "manual"
            aware_timestamp = datetime.now(self.tz)  # timezone-aware
            naive_timestamp = aware_timestamp.replace(tzinfo=None)  # drop tzinfo
            change_to_log["timestamp"] = naive_timestamp
            logger.debug(f"Changedict received: {pending_edit}")
            logger.debug(f"Record for changelog: {change_to_log}")
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(change_to_log, ensure_ascii=False, default=str) + "\n"
                )

            error_log = [
                create_alert(
                    "Prosesslogg oppdatert!",
                    "info",
                    ephemeral=True,
                ),
                *error_log,
            ]
            return False, error_log, table_data
