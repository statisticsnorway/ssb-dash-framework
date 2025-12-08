import json
import logging
import os
import zoneinfo
from datetime import UTC
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from ssb_poc_statlog_model.change_data_log import ChangeDataLog

from ..setup.variableselector import VariableSelector
from ..utils.alert_handler import create_alert
from ..utils.module_validation import module_validator

UTC = UTC

logger = logging.getLogger(__name__)


class ParquetEditor:  # TODO add validation of dataframe, workshop argument names
    """Simple module with the sole purpose of editing a parquet file.

    Accomplishes this functionality by writing a processlog in a json lines file and recording any edits in this jsonl file.

    Args:
        statistics_name: The name of the statistic being edited.
        id_vars: A list of columns that together form a unique identifier for a single row in your data.
        data_source: The path to the parquet file you want to edit.
        output: Columns in your dataframe that should be clickable to output to the variable selector panel.
        output_varselector_name: If your dataframe column names do not match the names in the variable selector, this can be used to map columns names to variable selector names. See examples.

    Example:
        >>> id_variabler = ["orgnr", "aar", "kvartal"]
        >>> my_parquet_editor = ParquetEditor(
            statistics_name="Demo",
            id_vars=id_variabler,
            data_source="/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet",
        )

    Notes:
        The process log is automatically created in the correct folder structure and is named after your parquet file.
    """

    _id_number: int = 0

    def __init__(
        self,
        statistics_name: str,
        id_vars: list[str],
        data_source: str,
        output: str | list[str] | None = None,
        output_varselector_name: str | list[str] | None = None,
    ) -> None:
        """Initializes the module and makes a few validation checks before moving on."""
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1

        if "/inndata/" not in data_source:
            logger.warning(
                "Editing is supposed to happen between inndata and klargjort, you might not be following 'Datatilstander'."
            )

        self.statistics_name = statistics_name
        self.output = output
        self.output_varselector_name = output_varselector_name or output
        self.user = os.getenv("DAPLA_USER")
        self.tz = zoneinfo.ZoneInfo("Europe/Oslo")
        self.id_vars = id_vars
        self.variableselector = VariableSelector(
            selected_inputs=id_vars, selected_states=[]
        )
        self.file_path = data_source
        path = Path(data_source)
        self.log_filepath = get_log_path(data_source)
        self.label = path.stem

        # Create parent directories for log file if they don't exist
        self.log_filepath.parent.mkdir(parents=True, exist_ok=True)

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

    def get_data(self) -> pd.DataFrame:
        """Reads the parquet file at the supplied file path."""
        if self.log_filepath.exists():
            logger.debug("Reading file and applying edits.")
            return apply_edits(self.file_path)
        logger.debug("Reading file, no edits to apply.")
        return pd.read_parquet(self.file_path)

    def _create_layout(self) -> html.Div:
        reason_modal = [
            dcc.Store(id=f"{self.module_number}-pending-edit"),
            dbc.Modal(
                [
                    dbc.ModalHeader("Reason for change"),
                    dbc.ModalBody(
                        [
                            dbc.Row(html.Div(id=f"{self.module_number}-edit-details")),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{self.module_number}-edit-reason",
                                            # This format for options is recommended by the official Dash documentation, mypy is ignored for this reason.
                                            options=[  # type: ignore[arg-type]
                                                {
                                                    "label": "Statistisk gjennomgang",
                                                    "value": "REVIEW",
                                                },
                                                {
                                                    "label": "Kontakt med dataleverandør",
                                                    "value": "OWNER",
                                                },
                                                {
                                                    "label": "Kontroll mot annen kilde",
                                                    "value": "OTHER_SOURCE",
                                                },
                                                {
                                                    "label": "Marginal enhet",
                                                    "value": "MARGINAL_UNIT",
                                                },  # Hva er egentlig dette?
                                                {
                                                    "label": "Dublett",
                                                    "value": "DUPLICATE",
                                                },  # Dette burde løses maskinelt, ikke være en kategori her?
                                                {
                                                    "label": "Annen grunn",
                                                    "value": "OTHER",
                                                },
                                            ],
                                            value="REVIEW",
                                        )
                                    ),
                                    dbc.Col(
                                        dbc.Textarea(
                                            id=f"{self.module_number}-edit-comment",
                                            placeholder="Enter a comment for the change...",
                                            autoFocus=True,
                                            n_submit=0,
                                        )
                                    ),
                                ]
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
            dcc.Store(id=f"{self.module_number}-parqueteditor-table-data-store"),
        ]
        return html.Div(
            [*reason_modal, dag.AgGrid(id=f"{self.module_number}-parqueteditor-table")]
        )

    def layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(self.module_layout)

    def module_callbacks(self) -> None:
        """Sets up the callbacks for the module."""

        @callback(
            Output(f"{self.module_number}-parqueteditor-table", "rowData"),
            Output(f"{self.module_number}-parqueteditor-table", "columnDefs"),
            Output(f"{self.module_number}-parqueteditor-table-data-store", "data"),
            *self.variableselector.get_all_inputs(),
        )
        def load_data_to_table(
            *args: Any,
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            logger.debug("Getting data for module.")
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

        @callback(
            Output(f"{self.module_number}-pending-edit", "data"),
            Output(f"{self.module_number}-reason-modal", "is_open"),
            Output(f"{self.module_number}-edit-details", "children"),
            Output(f"{self.module_number}-edit-comment", "value"),
            Input(f"{self.module_number}-parqueteditor-table", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def capture_edit(
            edited: list[dict[str, Any]],
        ) -> tuple[dict[str, Any], bool, str, str]:
            if not edited:
                logger.debug("Raising PreventUpdate")
                raise PreventUpdate
            logger.info(f"Edited: {edited}")
            edit = edited[0]
            details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
            return edit, True, details, ""

        @callback(
            Output(
                f"{self.module_number}-reason-modal",
                "is_open",
                allow_duplicate=True,
            ),
            Output("alert_store", "data", allow_duplicate=True),
            Output(
                f"{self.module_number}-parqueteditor-table-data-store",
                "data",
                allow_duplicate=True,
            ),
            Input(f"{self.module_number}-confirm-edit", "n_clicks"),
            Input(f"{self.module_number}-edit-comment", "n_submit"),
            State(f"{self.module_number}-pending-edit", "data"),
            State(f"{self.module_number}-edit-reason", "value"),
            State(f"{self.module_number}-edit-comment", "value"),
            State("alert_store", "data"),
            State(f"{self.module_number}-parqueteditor-table-data-store", "data"),
            *self.variableselector.get_all_inputs(),
            prevent_initial_call=True,
        )
        def confirm_edit(
            n_clicks: int,
            n_submit: int,
            pending_edit: dict[str, Any],
            reason: str,
            comment: str,
            error_log: list[dict[str, Any]],
            table_data: list[dict[str, Any]],
            *dynamic_states: Any,
        ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
            if not (n_clicks or n_submit):
                logger.debug("Raising PreventUpdate")
                raise PreventUpdate

            trigger_id = ctx.triggered_id
            if (
                trigger_id
                not in {  # This check is necessary to make sure it doesn't randomly log the same change a second time.
                    f"{self.module_number}-confirm-edit",
                    f"{self.module_number}-edit-comment",
                }
            ):
                logger.debug(f"Ignoring callback from {trigger_id}")
                raise PreventUpdate

            if not pending_edit:
                error_log = [
                    create_alert("Ingen pending edit funnet", "error", ephemeral=True),
                    *error_log,
                ]
                return False, error_log, table_data
            if not comment or str(comment).strip() == "":
                error_log = [
                    create_alert(
                        "Årsak for endring er påkrevd", "warning", ephemeral=True
                    ),
                    *error_log,
                ]
                return True, error_log, table_data

            pending_edit["reason"] = reason
            pending_edit["comment"] = comment
            logger.debug(f"Trying to log change.\nChangedict received: {pending_edit}")

            change_to_log = self._build_process_log_entry(pending_edit)

            logger.debug(f"Record for changelog: {change_to_log}")
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                logger.debug("Writing change")
                f.write(
                    json.dumps(change_to_log, ensure_ascii=False, default=str) + "\n"
                )
                logger.debug("Change written.")
            error_log = [
                create_alert(
                    "Prosesslogg oppdatert!",
                    "info",
                    ephemeral=True,
                ),
                *error_log,
            ]
            return False, error_log, table_data

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
                @callback(
                    output,
                    Input(f"{self.module_number}-parqueteditor-table", "cellClicked"),
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
                            f"{output} is not a string, is type {type(output)}. Trying to convert to string."
                        )
                        try:
                            output = str(output)
                        except Exception as e:
                            logger.debug(f"Failed to convert to string: {e}")
                            logger.debug("Raised PreventUpdate")
                            raise PreventUpdate from e
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

    def _build_process_log_entry(self, edit_dict: dict[str, Any]) -> dict[str, Any]:
        reason_category = edit_dict["reason"]
        comment = edit_dict["comment"]
        change_datetime = datetime.fromtimestamp(edit_dict["timestamp"] / 1000, tz=UTC)

        unit_id = [
            {"unit_id_variable": var, "unit_id_value": str(edit_dict["data"][var])}
            for var in self.id_vars
        ]
        changed_variable = edit_dict["colId"]
        old_value = edit_dict["oldValue"]
        new_value = edit_dict["value"]
        changelog_entry = {
            "statistics_name": self.statistics_name,
            "data_source": [self.file_path],
            "data_target": "data_target_placeholder",
            "data_period": "",
            "variable_name": changed_variable,
            "change_event": "M",
            "change_event_reason": reason_category,
            "change_datetime": change_datetime,
            "changed_by": self.user,
            "data_change_type": "UPD",
            "change_comment": comment.replace(
                "\n", ""
            ),  # Not sure what replace does but it was there before.
            "change_details": {
                "detail_type": "unit",
                "unit_id": unit_id,
                "old_value": [
                    {"variable_name": changed_variable, "value": str(old_value)}
                ],
                "new_value": [
                    {"variable_name": changed_variable, "value": str(new_value)}
                ],
            },
        }
        logger.debug(f"Changelog to validate:\n{changelog_entry}")
        ChangeDataLog.model_validate(changelog_entry)
        return changelog_entry


class ParquetEditorChangelog:
    """Simple module with the sole purpose of showing the changes made using ParquetEditor.

    Args:
        id_vars: A list of columns that together form a unique identifier for a single row in your data.
        file_path: The path to the parquet file you want to find the changelog for.

    Notes:
        The process log is automatically created in the correct folder structure and is named after your parquet file.
    """

    _id_number: int = 0

    def __init__(self, id_vars: list[str], file_path: str) -> None:
        """Initializes the module and makes a few validation checks before moving on."""
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1

        self.variable_selector = VariableSelector(
            selected_inputs=id_vars, selected_states=[]
        )
        self.user = os.getenv("DAPLA_USER")
        self.tz = zoneinfo.ZoneInfo("Europe/Oslo")
        path = Path(file_path)
        self.log_filepath = get_log_path(file_path)
        self.label = "Changes - " + path.stem

        self.module_layout = self._create_layout()
        module_validator(self)
        self.module_callbacks()

    def _create_layout(self) -> dcc.Textarea:
        return dcc.Textarea(
            id=f"{self.module_number}-parqueteditor-changelog",
            style={"width": "100%", "height": "80vh"},
            readOnly=True,
        )

    def module_callbacks(self) -> None:
        """Sets up the callbacks for the module."""

        @callback(
            Output(f"{self.module_number}-parqueteditor-changelog", "value"),
            *self.variable_selector.get_all_inputs(),
        )
        def load_data_to_table(
            *args: Any,
        ) -> str:
            data = log_as_text(self.log_filepath)

            return str(data)

    def layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(self.module_layout)


def get_log_path(parquet_path: str | Path) -> Path:
    """Return the expected log file path (.jsonl) for a given parquet file.

    The function searches for known data-state subfolders in the parquet path
    (/inndata/, /klargjorte-data/, /statistikk/, /utdata/) and rewrites the path
    to the corresponding temp folder under /<state>/temp/parqueteditor/.
    If none match, the log file is assumed to be in the same directory as the parquet file.
    """
    data_states = ["inndata", "klargjorte-data", "statistikk", "utdata"]
    log_subpath = "temp/parqueteditor"

    p = Path(parquet_path)
    posix = p.as_posix()

    for state in data_states:
        token = f"/{state}/"
        if token in posix:
            replaced = posix.replace(token, f"/{state}/{log_subpath}/")
            return Path(replaced).with_suffix(".jsonl")

    print(f"Expecting subfolder {data_states}. Log file path set to parquet path.")
    return p.with_suffix(".jsonl")


def read_jsonl_log(path: str | Path) -> list[Any]:
    """Reads the jsonl log.

    Args:
        path (str | Path): The path that leads to the jsonl log.

    Returns:
        A list where each instance is a line in the jsonl file.
    """
    all_data = []
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                all_data.append(data)
            elif isinstance(data, list):
                all_data.extend(data)
    except json.JSONDecodeError:
        with open(path, encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    all_data.append(json.loads(line))
    return all_data


def _match_dtype(
    data_to_change: pd.DataFrame, column: str, value_to_change: Any
) -> Any | None:
    # Change the dtype to match the column dtype
    if value_to_change == "None":
        return None
    col_dtype = data_to_change[column].dtype
    return col_dtype.type(value_to_change)


def _apply_change_detail(
    data_to_change: pd.DataFrame, change: dict[str, Any]
) -> pd.DataFrame:
    """Apply a single jsonl row change to the dataframe."""
    mask = pd.Series([True] * len(data_to_change))
    for cond in change["unit_id"]:
        col = cond["unit_id_variable"]
        val = cond["unit_id_value"]
        mask &= data_to_change[col].astype(str) == str(val)

    num_matches = mask.sum()
    if num_matches == 0:
        raise ValueError("No rows match the specified unit_id. Cannot apply change.")

    if num_matches > 1:
        raise ValueError(
            f"Unit_id is not unique: expected 1 row, found {num_matches} rows."
        )

    # The below might need to be a loop to account for bulk edits.
    old_var = change["old_value"][0]["variable_name"]
    old_val = _match_dtype(data_to_change, old_var, change["old_value"][0]["value"])
    new_val = _match_dtype(data_to_change, old_var, change["new_value"][0]["value"])

    if not (data_to_change.loc[mask, old_var] == old_val).all():
        found_val = data_to_change.loc[mask, old_var].iloc[0]
        if old_val is not None:
            raise ValueError(
                f"Old value mismatch: expected {old_val}, but found {found_val}."
            )

    if old_val is None:
        check_mask = mask & (data_to_change[old_var].isna())
    else:
        check_mask = mask & (data_to_change[old_var] == old_val)

    data_to_change.loc[check_mask, old_var] = new_val
    return data_to_change


def read_jsonl_file_to_string(file_path: str | Path) -> str:
    """Reads a JSONL file and returns its contents as a single string."""
    file_path = Path(file_path)
    with file_path.open("r", encoding="utf-8") as f:
        return f.read()


def log_as_text(file_path: str | Path) -> str:
    """Convert a JSONL string of change logs into a human-readable text format.

    Returns a single string.
    """
    jsonl_string = read_jsonl_file_to_string(file_path)
    records = [json.loads(line) for line in StringIO(jsonl_string)]
    lines = []

    for rec in records:
        detail = rec["change_details"]
        unit_id_text = ", ".join(
            f"{u['unit_id_variable']}={u['unit_id_value']}" for u in detail["unit_id"]
        )
        old_val = detail["old_value"][0]["value"] if detail["old_value"] else None
        new_val = detail["new_value"][0]["value"] if detail["new_value"] else None

        lines.append(f"Variable: {rec['variable_name']}")
        lines.append(f"  Data source: {rec['data_source'][0]}")
        lines.append(f"  Data target: {rec['data_target']}")
        lines.append(f"  Changed by: {rec['changed_by']} at {rec['change_datetime']}")
        lines.append(f"  Unit IDs: {unit_id_text}")
        lines.append(f"  Old value: {old_val} -> New value: {new_val}")
        lines.append(f"  Comment: {rec['change_comment']}")
        lines.append("-" * 60)

    return "\n".join(lines)


def apply_edits(parquet_path: str | Path) -> pd.DataFrame:
    """Applies edits from the jsonl log to a parquet file.

    Args:
        parquet_path (str): The file path for the parquet file.

    Returns:
        A pd.DataFrame with updated data.
    """
    log_path = get_log_path(parquet_path)
    logger.debug(f"log_path: {log_path}")
    processlog = read_jsonl_log(log_path)
    data = pd.read_parquet(processlog[0]["data_source"][0])

    for line in processlog:
        data = _apply_change_detail(data, line["change_details"])

    return data


def export_from_parqueteditor(data_source: str, data_target: str) -> None:
    """Export edited data from parquet editor.

    Reads the jsonl log, updates data_target from placeholder to the supplied value,
    and saves the updated log next to the exported parquet file.
    Also applies edits and exports the data.

    Args:
        data_source: Path to the source parquet file
        data_target: Path where the exported file will be written

    Raises:
        FileNotFoundError: if no log file is found.
    """
    log_path = get_log_path(data_source)

    # Read and update the jsonl log with actual data_target value
    if log_path.exists():
        processlog = read_jsonl_log(log_path)
        for entry in processlog:
            if entry.get("data_target") == "data_target_placeholder":
                entry["data_target"] = data_target
        # Alternative 1
        stem = Path(data_target).stem
        export_log_path = (
            Path(data_target).parent.parent
            / "logg"
            / "produksjonslogg"
            / f"{stem}.jsonl"
        )
        # Alternative 2
        # export_log_path = Path(data_target).with_suffix(".jsonl") # Save updated log next to the exported parquet file
        Path(data_target).parent.mkdir(parents=True, exist_ok=True)
        export_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_log_path, "w", encoding="utf-8") as f:
            for entry in processlog:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    else:
        raise FileNotFoundError(
            f"Process log not found at '{log_path}'. No edits have been recorded for '{data_source}'."
        )

    updated_data = apply_edits(data_source)
    updated_data.to_parquet(data_target)
    print(
        f"Export completed! File now exists at '{data_target}' with processlog at '{export_log_path}'"
    )
