"""Vaskify execution boundary for the HB module."""

import pandas as pd
from vaskify import Detect


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
    detector = Detect(hb_input_dataframe, id_nr="unit_id")
    return detector.hb(
        y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="strata" if configured_hb_strata_variable else "",
    )
