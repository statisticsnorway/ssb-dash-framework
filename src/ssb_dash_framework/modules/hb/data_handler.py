"""Data contracts for the HB methodology module."""

from abc import ABC
from abc import abstractmethod
from typing import Final

import pandas as pd
from pandas.api.types import is_bool_dtype
from pandas.api.types import is_numeric_dtype

HB_REQUIRED_COLUMNS: Final[tuple[str, ...]] = ("unit_id", "period", "value")


class HBDataHandlerMeta(ABC):
    """Interface for handlers that provide validated HB input data."""

    @abstractmethod
    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> pd.DataFrame:
        """Return one validated HB row per unit and comparison period.

        Args:
            selected_hb_variable: Source variable selected for the HB run.
            hb_comparison_periods: Ordered previous and selected periods.
            configured_hb_strata_variable: Optional source grouping variable.

        Returns:
            A DataFrame with the required HB columns and optional context.

        Raises:
            NotImplementedError: If a concrete handler has no implementation.
        """
        raise NotImplementedError


def validate_hb_dataframe(hb_input_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate the common DataFrame contract used by the HB calculation.

    Missing values in the numeric ``value`` column are allowed so that later
    stages can preserve not-comparable observations explicitly. The column
    must still have a numeric pandas dtype.

    Args:
        hb_input_dataframe: DataFrame to validate.

    Returns:
        The same DataFrame instance after validation.

    Raises:
        TypeError: If the input or a required column has an invalid type.
        ValueError: If required columns, valid values, or uniqueness are
            missing.
    """
    if not isinstance(hb_input_dataframe, pd.DataFrame):
        raise TypeError("HB input must be a pandas DataFrame.")

    if hb_input_dataframe.columns.duplicated().any():
        raise ValueError("HB input must not contain duplicate column names.")

    missing_columns = [
        column_name
        for column_name in HB_REQUIRED_COLUMNS
        if column_name not in hb_input_dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            f"HB input is missing required columns: {', '.join(missing_columns)}."
        )

    _validate_string_column(
        hb_input_dataframe,
        column_name="unit_id",
        allow_empty=False,
    )
    _validate_period_column(hb_input_dataframe)
    _validate_numeric_value_column(hb_input_dataframe)

    if hb_input_dataframe.duplicated(subset=["unit_id", "period"]).any():
        raise ValueError(
            "HB input must contain at most one row per unit_id and period."
        )

    return hb_input_dataframe


def _validate_string_column(
    hb_input_dataframe: pd.DataFrame,
    *,
    column_name: str,
    allow_empty: bool,
) -> None:
    column_values = hb_input_dataframe[column_name]
    invalid_values = column_values.isna() | ~column_values.map(
        lambda value: isinstance(value, str)
    )
    if not allow_empty:
        invalid_values |= column_values.map(
            lambda value: isinstance(value, str) and not value.strip()
        )

    if invalid_values.any():
        raise TypeError(f"HB column '{column_name}' must contain non-empty strings.")


def _validate_period_column(hb_input_dataframe: pd.DataFrame) -> None:
    period_values = hb_input_dataframe["period"]
    _validate_string_column(
        hb_input_dataframe,
        column_name="period",
        allow_empty=False,
    )

    invalid_periods = ~period_values.map(_is_canonical_period)
    if invalid_periods.any():
        raise ValueError(
            "HB column 'period' must use canonical values such as "
            "YYYY, YYYY-Q1, or YYYY-MM."
        )


def _is_canonical_period(period_value: object) -> bool:
    if not isinstance(period_value, str):
        return False
    if len(period_value) == 4:
        return period_value.isdigit()
    if len(period_value) == 7 and period_value[4] == "-":
        if period_value[5] == "Q":
            return period_value[:4].isdigit() and period_value[6] in "1234"
        if period_value[4] == "-":
            month = period_value[5:]
            return (
                period_value[:4].isdigit() and month.isdigit() and 1 <= int(month) <= 12
            )
    return False


def _validate_numeric_value_column(hb_input_dataframe: pd.DataFrame) -> None:
    value_column = hb_input_dataframe["value"]
    if is_bool_dtype(value_column) or not is_numeric_dtype(value_column):
        raise TypeError("HB column 'value' must have a numeric dtype.")
