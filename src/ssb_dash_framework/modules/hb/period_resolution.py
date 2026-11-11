"""Resolve canonical HB periods into ordered comparison periods."""

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

from .period_validation import is_canonical_hb_period
from .quarter_period import format_hb_quarter_period
from .week_period import format_hb_week_period
from .week_period import parse_hb_week_period


def resolve_hb_comparison_periods(
    selected_hb_period: str,
    configured_hb_time_unit: TimeUnit,
) -> tuple[str, str]:
    """Return the previous and selected canonical HB periods.

    Args:
        selected_hb_period: Canonical period selected for the current HB run.
        configured_hb_time_unit: Time unit configured for the selected period.

    Returns:
        The previous period and selected period, in that order.

    Raises:
        TypeError: If the selected period or configured time unit has an
            invalid type.
        ValueError: If the selected period is not canonical for the
            configured frequency.
    """
    if not isinstance(selected_hb_period, str):
        raise TypeError("Selected HB period must be a string.")
    if not isinstance(configured_hb_time_unit, TimeUnit):
        raise TypeError("Configured HB time unit must be a TimeUnit.")

    frequency = configured_hb_time_unit.frequency
    if not is_canonical_hb_period(selected_hb_period, frequency):
        raise ValueError(
            "Selected HB period must use a valid canonical value for "
            f"{frequency.name}: {selected_hb_period!r}."
        )

    if frequency is TimeUnitType.WEEK:
        selected_hb_time = parse_hb_week_period(
            selected_hb_period,
            configured_hb_time_unit,
        )
    else:
        selected_hb_time = TimeUnit.parse(
            configured_hb_time_unit,
            selected_hb_period,
        )

    previous_hb_time = selected_hb_time.subtract(1)
    if frequency is TimeUnitType.WEEK:
        previous_hb_period = format_hb_week_period(previous_hb_time)
    elif frequency is TimeUnitType.QUARTER:
        previous_hb_period = format_hb_quarter_period(previous_hb_time)
    else:
        previous_hb_period = previous_hb_time.to_str()

    return previous_hb_period, selected_hb_period
