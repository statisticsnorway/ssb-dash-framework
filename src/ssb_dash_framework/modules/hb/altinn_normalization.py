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
) -> HBDataResult:
    """Convert selected exact-path Altinn answers to common HB data.

    The input is expected to contain records already scoped to the configured
    form, comparison periods, and active submissions.
    """
    if not isinstance(selected_active_candidate_records, pd.DataFrame):
        raise TypeError("selected_active_candidate_records must be a pandas DataFrame.")
    if not isinstance(selected_feltsti, str) or not selected_feltsti.strip():
        raise ValueError("selected_feltsti must be a non-empty string.")
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

        normalized_records.append(
            {
                "unit_id": unit_id,
                "period": period,
                "value": value,
            }
        )

    hb_dataframe = pd.DataFrame.from_records(
        normalized_records,
        columns=["unit_id", "period", "value"],
    )
    hb_dataframe["value"] = pd.to_numeric(hb_dataframe["value"], errors="raise")
    validate_hb_dataframe(hb_dataframe)

    return HBDataResult(
        hb_dataframe=hb_dataframe,
        hb_warnings=tuple(hb_warnings),
    )


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
