import datetime
import json
import logging
import os
import zoneinfo
from collections.abc import Sequence
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

logger = logging.getLogger(__name__)


class ParquetEditor:  # TODO add validation of dataframe, workshop argument names
    """Simple module with the sole purpose of editing a parquet file.

    Accomplishes this functionality by writing a processlog in a json lines file and recording any edits in this jsonl file.

    Args:
        statistics_name: The name of the statistic being edited.
        id_vars: A list of columns that together form a unique identifier for a single row in your data.
        data_source: The path to the parquet file you want to edit.
        data_target: The path your completed file will be created at.
        output: Columns in your dataframe that should be clickable to output to the variable selector panel.
        output_varselector_name: If your dataframe column names do not match the names in the variable selector, this can be used to map columns names to variable selector names. See examples.

    Notes:
        The process log is automatically created in the correct folder structure and is named after your parquet file.
    """

    _id_number: int = 0

    def __init__(
        self,
        statistics_name: str,
        id_vars: list[str],
        data_source: str,
        data_target: str,  # Optional?
        output: str | list[str] | None = None,
        output_varselector_name: str | list[str] | None = None,
    ) -> None:
        """Initializes the module and makes a few validation checks before moving on."""
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1

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
        self.data_target = data_target
        path = Path(data_source)
        self.log_filepath = get_log_path(data_source)
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

    def get_data(self) -> pd.DataFrame:
        """Reads the parquet file at the supplied file path."""
        if self.log_filepath.exists():
            logger.debug("Reading file and applying edits.")
            return apply_edits(self.file_path, self.id_vars)
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
                                            options=[
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

        @callback(  # type: ignore[misc]
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

        @callback(  # type: ignore[misc]
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

        @callback(  # type: ignore[misc]
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
                @callback(  # type: ignore[misc]
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

    def _build_process_log_entry(self, edit_dict: dict[str, Any]) -> dict[str, Any]:
        reason_category = edit_dict["reason"]
        comment = edit_dict["comment"]
        change_datetime = datetime.datetime.fromtimestamp(
            edit_dict["timestamp"] / 1000, tz=datetime.UTC
        )

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
            "data_target": self.data_target,
            "data_period": "",
            "variable_name": changed_variable,
            "change_event": "M",
            "change_event_reason": reason_category,
            "change_datetime": change_datetime,
            "change_by": self.user,
            "data_change_type": "UPD",
            "change_comment": comment.replace(
                "\n", ""
            ),  # Not sure what replace does but it was there before.
            "change_details": {
                "kind": "unit",
                "unit_id": unit_id,
                "old_value": {"variable_name": changed_variable, "value": old_value},
                "new_value": {"variable_name": changed_variable, "value": new_value},
            },
        }
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
        self.id_vars = id_vars
        path = Path(file_path)
        self.log_filepath = get_log_path(file_path)
        self.label = "Changes - " + path.stem

        self.module_layout = self._create_layout()
        module_validator(self)
        self.module_callbacks()

    def get_log(self) -> pd.DataFrame:
        """Reads the log file at the supplied file path."""
        log = pd.read_json(self.log_filepath, lines=True)
        return log.join(pd.json_normalize(log["row_identifier"])).copy()

    def _create_layout(self) -> dag.AgGrid:
        return dag.AgGrid(id=f"{self.module_number}-parqueteditor-changes-table")

    def module_callbacks(self) -> None:
        """Sets up the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-parqueteditor-changes-table", "rowData"),
            Output(f"{self.module_number}-parqueteditor-changes-table", "columnDefs"),
            *self.variable_selector.get_all_inputs(),
        )
        def load_data_to_table(
            *args: Any,
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
            data = self.get_log()

            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "editable": True if col not in self.id_vars else False,
                }
                for col in data.columns
            ]
            return (data.to_dict(orient="records"), columns)

    def layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(self.module_layout)


def get_log_path(parquet_path: str | Path) -> Path:
    """Return the expected log file path (.jsonl) for a given parquet file.

    The function searches for known data-state subfolders in the parquet path
    (/inndata/, /klargjorte-data/, /statistikk/, /utdata/) and rewrites the path
    to the corresponding log folder under /logg/prosessdata/<state>/.
    If none match, the log file is assumed to be in the same directory as the parquet file.
    """
    data_states = ["inndata", "klargjorte-data", "statistikk", "utdata"]
    log_subpath = "logg/prosessdata"

    p = Path(parquet_path)
    posix = p.as_posix()

    for state in data_states:
        token = f"/{state}/"
        if token in posix:
            replaced = posix.replace(token, f"/{log_subpath}/{state}/")
            return Path(replaced).with_suffix(".jsonl")

    print(f"Expecting subfolder {data_states}. Log file path set to parquet path.")
    return p.with_suffix(".jsonl")


def _get_key_columns_from_log(log: pd.DataFrame) -> list[str]:
    """Extract and validate the key columns from the 'row_identifier' field in the log.

    The log must contain a 'row_identifier' column where each row is a dict of key-value pairs.
    All rows must use the same set of key columns; otherwise, a ValueError is raised.
    """
    if "row_identifier" not in log.columns:
        raise KeyError("Log file must contain a 'row_identifier' column.")

    key_sets = log["row_identifier"].apply(lambda d: tuple(sorted(d.keys())))

    if key_sets.nunique() != 1:
        raise ValueError(
            "Log file contains multiple incompatible key definitions.",
            list(key_sets.unique()),
        )

    return list(key_sets.iloc[0])


def _validate_keys_in_df(df: pd.DataFrame, key_cols: Sequence[str]) -> None:
    """Verify that all key columns found in the log are present in the parquet dataframe.

    Raises KeyError if any expected key column is missing.
    """
    missing = [c for c in key_cols if c not in df.columns]
    if missing:
        raise KeyError(
            "The specified row identifiers in log file do not exist in parquet columns: "
            f"{missing}"
        )


def apply_edits(
    parquet_path: str | Path,
    expected_keys: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Apply edits from a log file to a parquet dataset using a wide pivot-strategy.

    Steps performed:
        1. Read parquet file and locate its associated log file.
        2. Extract and validate key columns from the log.
        3. Optionally validate that the key columns in the log match expected_keys.
        4. Expand the row_identifier field into explicit key columns.
        5. Sort edits chronologically and remove duplicate edits
           (same key combination + column, keep latest).
        6. Pivot edits into wide format:
               one row per key combination
               one column per edited variable (colId)
        7. Align pivoted edits with the dataframe via index merge.
        8. Overwrite values in the dataframe where the log specifies non-null edits.
        9. Return the updated dataframe.

    Args:
        parquet_path:
            Path to the parquet file to be edited.
        expected_keys:
            Optional sequence of key column names that are expected to identify rows
            (e.g. ["aar", "orgnr"]). If provided, the key columns inferred from the log
            must match this set, otherwise a ValueError is raised.

    Returns:
        A new pandas DataFrame where the edits have been applied.

    Raises:
        ValueError: if key columns from log does not match expected_keys.
    """
    parquet_path = Path(parquet_path)
    log_path = get_log_path(parquet_path)

    df = pd.read_parquet(parquet_path)

    if not log_path.exists():
        logger.warning(
            f"No log file for edits found at: {log_path}. Returning original dataframe."
        )
        return df

    log = pd.read_json(log_path, lines=True)
    logger.debug(f"Log:\n{log}")
    if log.empty:
        logger.info("Log file is empty. No edits applied.")
        return df

    key_cols = _get_key_columns_from_log(log)
    _validate_keys_in_df(df, key_cols)

    if expected_keys is not None and set(expected_keys) != set(key_cols):
        raise ValueError(
            "Key columns from log do not match expected_keys.",
            {"from_log": key_cols, "expected": list(expected_keys)},
        )

    log_expanded = log.join(pd.json_normalize(log["row_identifier"])).copy()
    if "timestamp" in log_expanded.columns:
        log_expanded = log_expanded.sort_values("timestamp")

    subset = [*key_cols, "colId"]
    num_duplicated_edits = log_expanded.duplicated(subset=subset, keep="last").sum()
    if num_duplicated_edits > 0:
        logger.info(
            f"{num_duplicated_edits} duplicated edits found. "
            "Keeping the latest edit for each key+colId pair."
        )

    log_unique = log_expanded.drop_duplicates(subset=subset, keep="last").copy()

    if log_unique.empty:
        logger.info("No unique edits found. Returning original dataframe.")
        return df

    wide = log_unique.pivot(
        index=key_cols,
        columns="colId",
        values="value",
    )
    wide.columns.name = None

    df_indexed = df.set_index(key_cols)

    missing_keys = wide.index.difference(df_indexed.index)
    if len(missing_keys) > 0:
        logger.info(
            f"{len(missing_keys)} key combinations from the log do not exist in the parquet data. "
            "These edits are ignored."
        )

    wide_aligned = wide.reindex(df_indexed.index)

    df_edited = df_indexed.copy()

    for col in wide_aligned.columns:
        if col not in df_edited.columns:
            logger.info(
                f"Column '{col}' from the log does not exist in df. Creating column."
            )
            df_edited[col] = wide_aligned[col]
        else:
            df_edited[col] = wide_aligned[col].combine_first(df_edited[col])

    edits_applied = int(wide_aligned.count().sum())
    logger.info(f"{edits_applied} edits applied to parquet file (via pivot).")

    return df_edited.reset_index()
