"""Normalize selected Altinn HB answers to the common HB data contract."""

from numbers import Real

import pandas as pd
from pandas.api.types import is_bool_dtype
from pandas.api.types import is_scalar

from .data_handler import HBDataResult
from .data_handler import HBDataWarning
from .data_handler import validate_hb_dataframe

_REQUIRED_ALTINN_HB_COLUMNS = {
    "iso_periode",
    "skjema",
    "ident",
    "feltsti",
    "verdi",
}


def normalize_altinn_hb_candidate_records(
    selected_active_candidate_records: pd.DataFrame,
    *,
    selected_feltsti: str,
    selected_strata_feltsti: str | None = None,
) -> HBDataResult:
    """Convert selected exact-path Altinn answers to common HB data.

    The input is expected to contain records already scoped to the configured
    form, comparison periods, and active submissions. When a strata field path
    is provided, exactly one non-null, non-blank scalar answer is required for
    every unit-period.
    """
    if not isinstance(selected_active_candidate_records, pd.DataFrame):
        raise TypeError("selected_active_candidate_records must be a pandas DataFrame.")
    if not isinstance(selected_feltsti, str) or not selected_feltsti.strip():
        raise ValueError("selected_feltsti must be a non-empty string.")
    if selected_strata_feltsti is not None and (
        not isinstance(selected_strata_feltsti, str)
        or not selected_strata_feltsti.strip()
    ):
        raise ValueError("selected_strata_feltsti must be a non-empty string.")
    if selected_active_candidate_records.columns.duplicated().any():
        raise ValueError(
            "selected_active_candidate_records must not have duplicate columns."
        )

    missing_columns = _REQUIRED_ALTINN_HB_COLUMNS - set(
        selected_active_candidate_records.columns
    )
    if missing_columns:
        missing_column_names = ", ".join(sorted(missing_columns))
        raise ValueError(
            "selected_active_candidate_records is missing required columns: "
            f"{missing_column_names}."
        )
    if selected_active_candidate_records.empty:
        raise ValueError(
            "No selected Altinn HB candidate records are available to normalize."
        )

    normalized_records: list[dict[str, object]] = []
    hb_warnings: list[HBDataWarning] = []
    hb_dataframe_columns = ["unit_id", "period", "value"]
    if selected_strata_feltsti is not None:
        hb_dataframe_columns.append("strata")
    unit_period_columns = ["iso_periode", "skjema", "ident"]
    for (
        period,
        _form,
        unit_id,
    ), unit_period_records in selected_active_candidate_records.groupby(
        unit_period_columns,
        sort=False,
        dropna=False,
    ):
        exact_field_answers = unit_period_records.loc[
            unit_period_records["feltsti"].eq(selected_feltsti).fillna(False)
        ]
        if selected_strata_feltsti is not None:
            exact_strata_answers = unit_period_records.loc[
                unit_period_records["feltsti"].eq(selected_strata_feltsti).fillna(False)
            ]
            strata_value = _get_altinn_hb_strata_value(
                exact_strata_answers,
                unit_id=unit_id,
                period=period,
            )
        if len(exact_field_answers) > 1:
            # Missing-value treatment and eligibility belong to the downstream method.
            value = float("nan")
            hb_warnings.append(
                HBDataWarning(
                    message=(
                        "Multiple answers matched the configured field for unit "
                        f"{unit_id} in period {period}. No value was selected. "
                        "The analysis method determines how this missing value "
                        "affects the results. Excluding units can change the "
                        "population used to calculate results and may affect "
                        "outlier thresholds or classifications for other units."
                    ),
                    unit_id=unit_id,
                    period=period,
                )
            )
        elif exact_field_answers.empty:
            value = float("nan")
        else:
            value = _convert_altinn_hb_value(
                exact_field_answers.iloc[0]["verdi"],
                unit_id=unit_id,
                period=period,
            )

        normalized_record = {
            "unit_id": unit_id,
            "period": period,
            "value": value,
        }
        if selected_strata_feltsti is not None:
            normalized_record["strata"] = strata_value
        normalized_records.append(normalized_record)

    hb_dataframe = pd.DataFrame.from_records(
        normalized_records,
        columns=hb_dataframe_columns,
    )
    hb_dataframe["value"] = pd.to_numeric(hb_dataframe["value"], errors="raise")
    validate_hb_dataframe(hb_dataframe)

    return HBDataResult(
        hb_dataframe=hb_dataframe,
        hb_warnings=tuple(hb_warnings),
    )


def _get_altinn_hb_strata_value(
    exact_strata_answers: pd.DataFrame,
    *,
    unit_id: str,
    period: str,
) -> object:
    if exact_strata_answers.empty:
        raise ValueError(
            f"Missing Altinn strata answer for unit {unit_id!r} in period "
            f"{period!r}."
        )
    if len(exact_strata_answers) > 1:
        raise ValueError(
            f"Multiple Altinn strata answers for unit {unit_id!r} in period "
            f"{period!r}."
        )

    strata_value = exact_strata_answers.iloc[0]["verdi"]
    if not is_scalar(strata_value) or pd.isna(strata_value):
        raise ValueError(
            f"Altinn strata answer for unit {unit_id!r} in period {period!r} "
            "must be a non-null scalar value."
        )
    if isinstance(strata_value, str) and not strata_value.strip():
        raise ValueError(
            f"Altinn strata answer for unit {unit_id!r} in period {period!r} "
            "must not be blank."
        )
    return strata_value


def _convert_altinn_hb_value(
    raw_value: object,
    *,
    unit_id: str,
    period: str,
) -> Real:
    if is_scalar(raw_value) and pd.isna(raw_value):
        return float("nan")

    try:
        numeric_value = pd.to_numeric(raw_value, errors="raise")
    except (TypeError, ValueError) as error:
        raise _altinn_value_error(raw_value, unit_id, period) from error

    if is_bool_dtype(type(numeric_value)) or not isinstance(numeric_value, Real):
        raise _altinn_value_error(raw_value, unit_id, period)
    return numeric_value


def _altinn_value_error(raw_value: object, unit_id: str, period: str) -> ValueError:
    return ValueError(
        f"Altinn value {raw_value!r} for unit {unit_id!r} in period {period!r} "
        "is not a real number."
    )
