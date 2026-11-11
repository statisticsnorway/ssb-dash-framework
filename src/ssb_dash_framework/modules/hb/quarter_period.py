"""HB-local formatting for canonical quarter periods."""

from ssb_dash_framework.setup.variableselector.time_unit import SelectedTimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


def format_hb_quarter_period(selected_hb_quarter: SelectedTimeUnit) -> str:
    """Format an HB quarter using its calendar year and month."""
    if selected_hb_quarter.timeunit.frequency is not TimeUnitType.QUARTER:
        raise ValueError("HB quarter period formatting requires a QUARTER TimeUnit.")

    quarter_number = (selected_hb_quarter.dt.month - 1) // 3 + 1
    return f"{selected_hb_quarter.dt.year:04d}-Q{quarter_number}"
