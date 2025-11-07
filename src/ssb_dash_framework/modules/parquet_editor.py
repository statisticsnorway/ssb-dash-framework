import os
from pathlib import Path
from typing import Any
import logging
from datetime import datetime
import zoneinfo
import json

import pandas as pd
from dash import html, dcc
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import Output
from dash.exceptions import PreventUpdate
from dash import callback
import dash_bootstrap_components as dbc


import dash_ag_grid as dag
from ..setup.variableselector import VariableSelector
from ..utils.module_validation import module_validator
from ..utils.alert_handler import create_alert

logger = logging.getLogger(__name__)


class ParquetEditor:
    _id_number: int = 0

    def __init__(self, id_vars, file_path) -> None:
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
        module_validator(self)
        self.module_callbacks()

    def get_data(self):
        return pd.read_parquet(self.file_path)

    def _create_layout(self):
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

    def layout(self):
        return html.Div(self.module_layout)

    def module_callbacks(self):
        @callback(
            Output(f"{self.module_number}-simple-table", "rowData"),
            Output(f"{self.module_number}-simple-table", "columnDefs"),
            Output(f"{self.module_number}-simple-table-data-store", "data"),
            *self.variable_selector.get_all_inputs(),
        )
        def load_data_to_table(*args):
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

            edit_with_reason = dict(pending_edit)
            edit_with_reason["reason"] = reason.replace("\n", "")
            edit_with_reason["user"] = self.user
            edit_with_reason["change_event"] = "manual"

            aware_timestamp = datetime.now(self.tz)  # timezone-aware
            naive_timestamp = aware_timestamp.replace(tzinfo=None)  # drop tzinfo
            edit_with_reason["timestamp"] = naive_timestamp

            logger.debug(edit_with_reason)
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(edit_with_reason, ensure_ascii=False, default=str) + "\n"
                )
            new_table_data = self._update_row(
                table_data, pending_edit
            )  # Might be possible to replace with something simpler.
            error_log = [
                create_alert(
                    "Prosesslogg oppdatert!",
                    "info",
                    ephemeral=True,
                ),
                *error_log,
            ]
            return False, error_log, new_table_data

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
