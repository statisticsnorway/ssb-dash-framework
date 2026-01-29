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
import numpy as np
from pandas.api import types as pdt
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from pandas.io import parquet
from ssb_poc_statlog_model.change_data_log import ChangeDataLog

from ..setup.variableselector import VariableSelector
from ..utils.alert_handler import create_alert
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)

def check_for_bucket_path(path: str) -> None:
    """Temporary check to make sure users keep to using '/buckets/' paths.
    
    Need to test more with UPath to make sure nothing unexpected happens.
    """
    if not path.startswith("/buckets/"):
        raise NotImplementedError("Due to differences in how files in '/buckets/...' behave compared to files in the cloud buckets this functionality is currently limited to only work with paths that starts with '/buckets'.")

class ParquetEditor:  # TODO add validation of dataframe, workshop argument names
    """Simple module with the sole purpose of editing a parquet file.

    Accomplishes this functionality by writing a processlog in a json lines file and recording any edits in this jsonl file.

    Args:
        statistics_name: The name of the statistic being edited.
        id_vars: A list of columns that together form a unique identifier for a single row in your data.
        data_source: The path to the parquet file you want to edit.
        output: Columns in your dataframe that should be clickable to output to the variable selector panel.
        output_varselector_name: If your dataframe column names do not match the names in the variable selector, this can be used to map columns names to variable selector names. See examples.
        require_reason: If True (default), a reason and comment are required for each edit.
                        If False, edits are logged immediately without opening the modal,
                        using change_event_reason="OTHER" (valid enum) and empty comment.

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
        require_reason: bool = True,
    ) -> None:
        """Initializes the module and makes a few validation checks before moving on."""
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1
        self.icon = "✏️"  # TODO: Make visible
        check_for_bucket_path(data_source)
        if "/inndata/" not in data_source:
            logger.warning(
                "Editing is supposed to happen between inndata and klargjort, you might not be following 'Datatilstander'."
            )

        self.statistics_name = statistics_name
        self.output = output
        self.output_varselector_name = output_varselector_name or output
        self.require_reason = require_reason
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
        logger.info("Getting data for the module.")
        if self.log_filepath.exists():
            logger.debug("Reading file and applying edits.")
            df = apply_edits(self.file_path)
        else:
            logger.debug("Reading file, no edits to apply.")
            df = pd.read_parquet(self.file_path)
        _raise_if_duplicates(df, self.id_vars)
        return df

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
        # Add-row button beneath the table
        add_row_controls = html.Div(
            [
                dbc.Button(
                    "Legg til rad",
                    id=f"{self.module_number}-add-row",
                    color="primary",
                    className="mt-2",
                ),
            ]
        )

        return html.Div(
            [
                *reason_modal,
                dag.AgGrid(id=f"{self.module_number}-parqueteditor-table"),
                add_row_controls,
            ]
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
            # Make all columns editable to allow entering id_vars for new rows
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "editable": True,
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
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-parqueteditor-table", "cellValueChanged"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def capture_edit(
            edited: list[dict[str, Any]],
            error_log: list[dict[str, Any]],
        ) -> tuple[dict[str, Any], bool, str, str, list[dict[str, Any]]]:
            if not edited:
                logger.debug("Raising PreventUpdate")
                raise PreventUpdate
            logger.info(f"Edited: {edited}")
            edit = edited[0]
            details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"

            if not self.require_reason:
                # Auto-log immediately with a valid enum reason
                edit["reason"] = "OTHER"
                edit["comment"] = ""
                try:
                    change_to_log = self._build_process_log_entry(edit)
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(json.dumps(change_to_log, ensure_ascii=False, default=str) + "\n")
                    error_log = [
                        create_alert("Endring logget (uten begrunnelse).", "info", ephemeral=True),
                        *error_log,
                    ]
                except Exception as e:
                    logger.exception("Failed to auto-log edit when require_reason=False.")
                    error_log = [
                        create_alert(f"Kunne ikke logge endringen: {e}", "error", ephemeral=True),
                        *error_log,
                    ]
                # Keep modal closed
                return edit, False, details, "", error_log

            # Default (require_reason=True): open modal and wait for confirm
            return edit, True, details, "", error_log

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
            # Only used when require_reason=True
            if not self.require_reason:
                raise PreventUpdate

            trigger_id = ctx.triggered_id
            if trigger_id not in {
                f"{self.module_number}-confirm-edit",
                f"{self.module_number}-edit-comment",
            }:
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

            try:
                change_to_log = self._build_process_log_entry(pending_edit)
                with open(self.log_filepath, "a", encoding="utf-8") as f:
                    f.write(json.dumps(change_to_log, ensure_ascii=False, default=str) + "\n")
                error_log = [
                    create_alert("Prosesslogg oppdatert!", "info", ephemeral=True),
                    *error_log,
                ]
            except Exception as e:
                logger.exception("Failed to log confirmed edit.")
                error_log = [
                    create_alert(f"Kunne ikke logge endringen: {e}", "error", ephemeral=True),
                    *error_log,
                ]
                # Keep modal open to allow fix
                return True, error_log, table_data

            # Close modal on success
            return False, error_log, table_data

        # Add-row callback
        @callback(
            Output(f"{self.module_number}-parqueteditor-table", "rowData", allow_duplicate=True),
            Output(f"{self.module_number}-parqueteditor-table-data-store", "data", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-add-row", "n_clicks"),
            State(f"{self.module_number}-parqueteditor-table-data-store", "data"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, table_data: list[dict[str, Any]] | None, error_log: list[dict[str, Any]]) \
            -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            if not n_clicks:
                raise PreventUpdate
            if not table_data or len(table_data) == 0:
                # If the table has not been loaded yet, pull schema from parquet
                df = self.get_data()
                cols = list(df.columns)
            else:
                cols = list(table_data[0].keys())

            new_row = {col: None for col in cols}
            updated_data = (table_data or []) + [new_row]

            error_log = [
                create_alert("Ny rad lagt til. Fyll inn verdier og bekreft endringer som vanlig.", "info", ephemeral=True),
                *error_log,
            ]
            return updated_data, updated_data, error_log

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
                    output_val = clickdata["value"]
                    if not isinstance(output_val, str):
                        logger.debug(
                            f"{output_val} is not a string, is type {type(output_val)}. Trying to convert to string."
                        )
                        try:
                            output_val = str(output_val)
                        except Exception as e:
                            logger.debug(f"Failed to convert to string: {e}")
                            logger.debug("Raised PreventUpdate")
                            raise PreventUpdate from e
                    logger.debug(f"Transfering {output_val} to {output_varselector_name}")
                    return output_val

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
            ),
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


def _typed_missing_for_col(series: pd.Series):
    """Return a dtype-appropriate missing value for the given series."""
    dtype = series.dtype
    if pdt.is_integer_dtype(dtype):
        return pd.NA
    if pdt.is_float_dtype(dtype):
        return np.nan
    if pdt.is_bool_dtype(dtype):
        return pd.NA
    if pdt.is_datetime64_any_dtype(dtype):
        return pd.NaT
    return None


def _match_dtype(
    data_to_change: pd.DataFrame, column: str, value_to_change: Any
) -> Any | None:
    """Cast or coerce the provided value to match the column dtype.

    - Strings like "40" will become int/float/bool/datetime where appropriate.
    - "None", empty string, "nan"/"NA", or None become dtype-appropriate missing values.
    """
    # Handle missing representations
    if isinstance(value_to_change, str):
        if value_to_change.strip().lower() in {"", "none", "nan", "na"}:
            return _typed_missing_for_col(data_to_change[column])
    if value_to_change in (None,):
        return _typed_missing_for_col(data_to_change[column])

    col_dtype = data_to_change[column].dtype
    text = str(value_to_change)

    try:
        if pdt.is_integer_dtype(col_dtype):
            # Convert to Python int; assignment will work with nullable Int64 later
            return int(text)
        if pdt.is_float_dtype(col_dtype):
            return float(text)
        if pdt.is_bool_dtype(col_dtype):
            low = text.lower()
            if low in ("true", "1", "yes"):
                return True
            if low in ("false", "0", "no"):
                return False
            return _typed_missing_for_col(data_to_change[column])
        if pdt.is_datetime64_any_dtype(col_dtype):
            return pd.to_datetime(text, errors="coerce")
        # Fallback for object/string columns
        return value_to_change
    except Exception:
        # On any conversion failure, return a missing value appropriate for the dtype
        return _typed_missing_for_col(data_to_change[column])


def _apply_change_detail(
    data_to_change: pd.DataFrame, change: dict[str, Any]
) -> pd.DataFrame:
    """Apply a single jsonl row change to the dataframe.

    Supports updates and implicit inserts:
    - Try match with new snapshot of unit_id.
    - If no match, try with old value for the edited column.
    - If still no match and old_value is missing, insert a new row with unit_id typed.
    """
    unit_ids = change["unit_id"]

    # Edited variable + typed values
    old_var = change["old_value"][0]["variable_name"]
    old_val = _match_dtype(data_to_change, old_var, change["old_value"][0]["value"])
    new_val = _match_dtype(data_to_change, old_var, change["new_value"][0]["value"])

    def build_mask(use_old_for_oldvar: bool) -> pd.Series:
        mask = pd.Series([True] * len(data_to_change))
        for cond in unit_ids:
            col = cond["unit_id_variable"]
            val = cond["unit_id_value"]
            match_val = _match_dtype(
                data_to_change,
                col,
                (old_val if use_old_for_oldvar and col == old_var else val),
            )
            # Treat any NA-like value (np.nan, pd.NA, None, pd.NaT) as missing
            if pd.isna(match_val):
                mask &= data_to_change[col].isna()
            else:
                mask &= data_to_change[col] == match_val
        return mask

    # Match with new-snapshot
    mask_new = build_mask(use_old_for_oldvar=False)
    num_new = int(mask_new.sum())
    target_mask: pd.Series | None = None

    if num_new == 0:
        # Try matching with old value for edited column
        mask_old = build_mask(use_old_for_oldvar=True)
        num_old = int(mask_old.sum())
        if num_old == 1:
            target_mask = mask_old
        elif num_old > 1:
            raise ValueError(
                f"Unit_id is not unique when matching with old value for '{old_var}'. Found {num_old} rows."
            )
        else:
            # No match with either snapshot -> possible insert if old_val is missing
            if pd.isna(old_val):
                # Build a new row with dtype-appropriate missing values
                new_row = {
                    col: _typed_missing_for_col(data_to_change[col])
                    for col in data_to_change.columns
                }
                # Fill unit_id values (typed)
                for cond in unit_ids:
                    uid_col = cond["unit_id_variable"]
                    uid_val = _match_dtype(data_to_change, uid_col, cond["unit_id_value"])
                    new_row[uid_col] = uid_val
                # Set the edited column's new value
                new_row[old_var] = new_val
                # Append
                data_to_change = pd.concat(
                    [data_to_change, pd.DataFrame([new_row])], ignore_index=True
                )
                return data_to_change
            else:
                raise ValueError("No rows match the specified unit_id. Cannot apply change.")
    elif num_new > 1:
        raise ValueError(
            f"Unit_id is not unique using new-snapshot values. Found {num_new} rows."
        )
    else:
        target_mask = mask_new

    # UPDATE CASE on matched row
    # Only enforce old-value match when old_val is not missing
    if not pd.isna(old_val):
        if not (data_to_change.loc[target_mask, old_var] == old_val).all():
            found_val = data_to_change.loc[target_mask, old_var].iloc[0]
            raise ValueError(
                f"Old value mismatch: expected {old_val}, but found {found_val}."
            )

    # Assign new value
    if pd.isna(old_val):
        check_mask = target_mask & data_to_change[old_var].isna()
    else:
        check_mask = target_mask & (data_to_change[old_var] == old_val)

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


def _raise_if_duplicates(df: pd.DataFrame, subset: set[str] | list[str]) -> None:
    """Raises a ValueError if duplicates exist on the given subset of columns."""
    dupes = df.duplicated(subset=subset, keep=False)
    if dupes.any():
        duplicate_rows = df[dupes]
        raise ValueError(
            f"Duplicate rows found based on subset {subset}:\n{duplicate_rows}"
        )


def _harmonize_dtypes(edited_df: pd.DataFrame, reference_df: pd.DataFrame) -> pd.DataFrame:
    """Coerce edited_df column dtypes to match reference_df schema.

    - Integer columns -> numeric then pandas nullable Int64 (supports NA).
    - Float columns -> numeric float dtype.
    - Boolean columns -> pandas 'boolean' dtype.
    - Datetime columns -> to_datetime (coerce).
    - Others left as-is.
    """
    df = edited_df.copy()
    for col in df.columns:
        ref_dtype = reference_df[col].dtype if col in reference_df.columns else df[col].dtype
        try:
            if pdt.is_integer_dtype(ref_dtype):
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].astype("Int64")
            elif pdt.is_float_dtype(ref_dtype):
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].astype(ref_dtype)
            elif pdt.is_bool_dtype(ref_dtype):
                # Cast to pandas nullable boolean
                df[col] = df[col].astype("boolean")
            elif pdt.is_datetime64_any_dtype(ref_dtype):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                # Leave object/string columns as-is
                pass
        except Exception as e:
            logger.warning(f"Failed to harmonize dtype for column '{col}': {e}")
            # leave column unchanged if coercion fails
            continue
    return df


def apply_edits(parquet_path: str | Path) -> pd.DataFrame:
    """Applies edits from the jsonl log to a parquet file.

    Args:
        parquet_path (str): The file path for the parquet file.

    Returns:
        A pd.DataFrame with updated data.
    """
    check_for_bucket_path(parquet_path)
    log_path = get_log_path(parquet_path)
    logger.debug(f"log_path: {log_path}")
    processlog = read_jsonl_log(log_path)

    # Load original and keep a copy of the reference schema
    original = pd.read_parquet(processlog[0]["data_source"][0])
    data = original.copy()

    id_vars = set()
    for line in processlog:
        for id_var in [
            unit_id_var["unit_id_variable"]
            for unit_id_var in line["change_details"]["unit_id"]
        ]:
            id_vars.add(id_var)
        data = _apply_change_detail(data, line["change_details"])

    # Harmonize dtypes to original schema to avoid ArrowInvalid on export
    data = _harmonize_dtypes(data, original)

    logger.debug(f"id_vars deduced from processlog: {id_vars}")
    _raise_if_duplicates(data, id_vars)
    return data


def export_from_parqueteditor(
    data_source: str, data_target: str, force_overwrite: bool = False
) -> None:
    """Export edited data from parquet editor.

    Reads the jsonl log, updates data_target from placeholder to the supplied value,
    and saves the updated log next to the exported parquet file.
    Also applies edits and exports the data.

    Args:
        data_source: Path to the source parquet file
        data_target: Path where the exported file will be written
        force_overwrite: If True, overwrites existing parquet and jsonl files when exporting. Defaults to False.

    Raises:
        FileNotFoundError: if no log file is found.
        FileExistsError: If any of the files to export already exists and force_overwrite is False.
    """
    check_for_bucket_path(data_source)
    log_path = get_log_path(data_source)

    # Read and update the jsonl log with actual data_target value
    if log_path.exists():
        processlog = read_jsonl_log(log_path)
        for entry in processlog:
            if entry.get("data_target") == "data_target_placeholder":
                entry["data_target"] = data_target
        data_path = Path(data_target)
        bucket_root = data_path.parents[1]
        relative = data_path.relative_to(bucket_root).with_suffix(".jsonl")
        export_log_path = bucket_root / "logg" / "prosessdata" / relative
        export_log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"export_log_path:\n{export_log_path}")
        Path(data_target).parent.mkdir(parents=True, exist_ok=True)
        export_log_path.parent.mkdir(parents=True, exist_ok=True)
        if export_log_path.exists() and not force_overwrite:
            raise FileExistsError(
                f"Process log '{export_log_path}' already exists. "
                f"Use force_overwrite=True to overwrite."
            )
        with open(export_log_path, "w", encoding="utf-8") as f:
            for entry in processlog:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    else:
        raise FileNotFoundError(
            f"Process log not found at '{log_path}'. No edits have been recorded for '{data_source}'."
        )

    data_target_path = Path(data_target)
    if data_target_path.exists() and not force_overwrite:
        raise FileExistsError(
            f"Target parquet file '{data_target}' already exists. "
            "Use force_overwrite=True to overwrite."
        )

    updated_data = apply_edits(data_source)
    updated_data.to_parquet(data_target)
    print(
        f"Export completed! File now exists at '{data_target}' with processlog at '{export_log_path}'"
    )