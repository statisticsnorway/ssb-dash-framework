"""Vaskify execution boundary for the HB module."""

import pandas as pd
from vaskify import Detect

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

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
    _validate_hb_comparison_periods(hb_input_dataframe, hb_comparison_periods)
    detector = Detect(hb_input_dataframe, id_nr="unit_id")
    return detector.hb(
    y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="strata" if configured_hb_strata_variable else "",
    )


def _validate_hb_comparison_periods(
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
) -> None:
    if not isinstance(hb_comparison_periods, tuple):
        raise TypeError("hb_comparison_periods must be a tuple.")
    if len(hb_comparison_periods) != 2:
        raise ValueError("HB comparison requires exactly two periods.")
    if not all(
        any(
            is_canonical_hb_period(period, frequency)
            for frequency in TimeUnitType
        )
        for period in hb_comparison_periods
    ):
        raise ValueError("HB comparison periods must be canonical TimeUnit periods.")
    if hb_comparison_periods[0] == hb_comparison_periods[1]:
        raise ValueError("HB comparison periods must be distinct.")

    input_periods = hb_input_dataframe["period"].drop_duplicates().tolist()
    if len(input_periods) != 2 or not all(
        isinstance(period, str) and period in hb_comparison_periods
        for period in input_periods
    ):
        raise ValueError(
            "HB input must contain exactly the requested comparison periods."
        )
