"""Data contracts for the HB methodology module."""

from abc import ABC
from abc import abstractmethod
from typing import Final

import pandas as pd
from pandas.api.types import is_bool_dtype
from pandas.api.types import is_numeric_dtype

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

from .period_validation import is_canonical_hb_period

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


def validate_hb_dataframe(
    hb_input_dataframe: pd.DataFrame,
    *,
    configured_hb_frequency: TimeUnitType | None = None,
) -> pd.DataFrame:
    """Validate the common DataFrame contract used by the HB calculation.

    Missing values in the numeric ``value`` column are allowed so that later
    stages can preserve not-comparable observations explicitly. The column
    must still have a numeric pandas dtype.
    Period values may use any canonical ``TimeUnitType`` format; passing
    ``configured_hb_frequency`` also enforces that all periods match it.

    Args:
        hb_input_dataframe: DataFrame to validate.
        configured_hb_frequency: Optional configured frequency used to ensure
            every period value matches the selector's TimeUnit.

    Returns:
        The same DataFrame instance after validation.

    Raises:
        TypeError: If the input or a required column has an invalid type.
        ValueError: If required columns, valid values, or uniqueness are
            missing, or period values do not match the configured frequency.
    """
    if not isinstance(hb_input_dataframe, pd.DataFrame):
        raise TypeError("HB input must be a pandas DataFrame.")
    if configured_hb_frequency is not None and not isinstance(
        configured_hb_frequency, TimeUnitType
    ):
        raise TypeError("configured_hb_frequency must be a TimeUnitType.")

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
    _validate_period_column(hb_input_dataframe, configured_hb_frequency)
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


def _validate_period_column(
    hb_input_dataframe: pd.DataFrame,
    configured_hb_frequency: TimeUnitType | None,
) -> None:
    period_values = hb_input_dataframe["period"]
    _validate_string_column(
        hb_input_dataframe,
        column_name="period",
        allow_empty=False,
    )

    invalid_periods = ~period_values.map(
        lambda period_value: _is_canonical_period(
            period_value,
            configured_hb_frequency,
        )
    )
    if invalid_periods.any():
        if configured_hb_frequency is None:
            supported_frequencies = ", ".join(
                frequency.name for frequency in TimeUnitType
            )
            raise ValueError(
                "HB column 'period' must use a canonical value for a supported "
                f"TimeUnit frequency ({supported_frequencies})."
            )
        raise ValueError(
            "HB column 'period' must use canonical values for configured "
            f"frequency {configured_hb_frequency.name}."
        )


def _is_canonical_period(
    period_value: object,
    configured_hb_frequency: TimeUnitType | None = None,
) -> bool:
    if not isinstance(period_value, str):
        return False
    frequencies = (
        (configured_hb_frequency,)
        if configured_hb_frequency is not None
        else tuple(TimeUnitType)
    )
    return any(
        _is_canonical_period_for_frequency(period_value, frequency)
        for frequency in frequencies
    )


def _is_canonical_period_for_frequency(
    period_value: str,
    frequency: TimeUnitType,
) -> bool:
    return is_canonical_hb_period(period_value, frequency)


def _validate_numeric_value_column(hb_input_dataframe: pd.DataFrame) -> None:
    value_column = hb_input_dataframe["value"]
    if is_bool_dtype(value_column) or not is_numeric_dtype(value_column):
        raise TypeError("HB column 'value' must have a numeric dtype.")
