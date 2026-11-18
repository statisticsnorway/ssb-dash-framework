"""Vaskify execution boundary for the HB module."""

import pandas as pd
from vaskify import Detect

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

from .data_handler import validate_hb_dataframe
from .period_validation import is_canonical_hb_period


def run_hb_vaskify(
    hb_input_dataframe: pd.DataFrame,
    *,
    hb_comparison_periods: tuple[str, str],
    configured_hb_strata_variable: str | None = None,
) -> pd.DataFrame:
    """Run Vaskify HB against the common HB input DataFrame.

    Args:
        hb_input_dataframe: Validated common HB input data.
        hb_comparison_periods: The ordered periods to compare.
        configured_hb_strata_variable: The configured source strata variable,
            if the input includes a normalized ``strata`` column.

    Returns:
        The DataFrame returned by Vaskify's HB method.
    """
    _validate_hb_vaskify_input(
        hb_input_dataframe,
        configured_hb_strata_variable=configured_hb_strata_variable,
    )
    _validate_hb_comparison_periods(hb_input_dataframe, hb_comparison_periods)
    detector = Detect(hb_input_dataframe, id_nr="unit_id")
    hb_result = detector.hb(
        y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="strata" if configured_hb_strata_variable is not None else "",
        pu=0.5,
        pa=0.05,
        pc=20,
        percentiles=(0.25, 0.75),
        flag="flag_hb",
        output_format="wide",
        output_scope="all",
    )
    _validate_hb_vaskify_result(
        hb_result,
        hb_comparison_periods=hb_comparison_periods,
        require_strata=configured_hb_strata_variable is not None,
    )
    return hb_result


def _validate_hb_vaskify_result(
    hb_result: object,
    *,
    hb_comparison_periods: tuple[str, str],
    require_strata: bool,
) -> None:
    if not isinstance(hb_result, pd.DataFrame):
        raise TypeError("Vaskify HB result must be a pandas DataFrame.")

    required_columns = {
        "unit_id",
        f"value_{hb_comparison_periods[0]}",
        f"value_{hb_comparison_periods[1]}",
        "lower_limit",
        "upper_limit",
        "ratio",
        "median_ratio",
        "flag_hb",
    }
    if require_strata:
        required_columns.add("strata")

    missing_columns = required_columns - set(hb_result.columns)
    if missing_columns:
        missing_column_names = ", ".join(sorted(missing_columns))
        raise ValueError(
            "Vaskify HB result is missing required columns: "
            f"{missing_column_names}."
        )


def _validate_hb_vaskify_input(
    hb_input_dataframe: pd.DataFrame,
    *,
    configured_hb_strata_variable: str | None,
) -> None:
    validate_hb_dataframe(hb_input_dataframe)
    if configured_hb_strata_variable is not None and (
        "strata" not in hb_input_dataframe.columns
    ):
        raise ValueError(
            "HB input must contain a 'strata' column when a strata variable is configured."
        )


def _validate_hb_comparison_periods(
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
) -> None:
    if not isinstance(hb_comparison_periods, tuple):
        raise TypeError("hb_comparison_periods must be a tuple.")
    if len(hb_comparison_periods) != 2:
        raise ValueError("HB comparison requires exactly two periods.")
    comparison_period_frequencies = [
        frequency
        for period in hb_comparison_periods
        for frequency in TimeUnitType
        if is_canonical_hb_period(period, frequency)
    ]
    if len(comparison_period_frequencies) != 2:
        raise ValueError("HB comparison periods must be canonical TimeUnit periods.")
    if comparison_period_frequencies[0] is not comparison_period_frequencies[1]:
        raise ValueError(
            "HB comparison periods must use the same canonical TimeUnit frequency."
        )
    if hb_comparison_periods[0] == hb_comparison_periods[1]:
        raise ValueError("HB comparison periods must be distinct.")
    if any(
        is_canonical_hb_period(period, TimeUnitType.HALF_YEAR)
        for period in hb_comparison_periods
    ):
        raise ValueError(
            "HALF_YEAR comparisons are disabled until Vaskify supports "
            "canonical half-year periods."
        )

    input_periods = hb_input_dataframe["period"].drop_duplicates().tolist()
    if len(input_periods) != 2 or not all(
        isinstance(period, str) and period in hb_comparison_periods
        for period in input_periods
    ):
        raise ValueError(
            "HB input must contain exactly the requested comparison periods."
        )
