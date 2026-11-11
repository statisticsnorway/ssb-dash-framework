"""HB-local handling for canonical ISO week periods."""

import re
from datetime import date

import pendulum

from ssb_dash_framework.setup.variableselector.time_unit import SelectedTimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

_CANONICAL_WEEK_PATTERN = re.compile(r"(?P<year>\d{4})-W(?P<week>\d{2})")
_UNSUPPORTED_PENDULUM_WEEK_TOKEN = "Unsupported token: WW"


def parse_hb_week_period(
    selected_hb_week_period: str,
    configured_hb_time_unit: TimeUnit,
) -> SelectedTimeUnit:
    """Parse a canonical HB week period, falling back only for the known parser bug.

    Args:
        selected_hb_week_period: Canonical ISO week such as ``2024-W01``.
        configured_hb_time_unit: The configured WEEK time unit.

    Returns:
        A selected time unit positioned at the Monday of the ISO week.

    Raises:
        TypeError: If the period or configured time unit has an invalid type.
        ValueError: If the period is non-canonical or not a valid ISO week.
    """
    if not isinstance(selected_hb_week_period, str):
        raise TypeError("HB week period must be a string.")
    if not isinstance(configured_hb_time_unit, TimeUnit):
        raise TypeError("Configured HB time unit must be a TimeUnit.")
    if configured_hb_time_unit.frequency is not TimeUnitType.WEEK:
        raise ValueError("HB week period parsing requires a WEEK TimeUnit.")

    period_match = _CANONICAL_WEEK_PATTERN.fullmatch(selected_hb_week_period)
    if period_match is None:
        raise ValueError(
            "HB week period must use the canonical YYYY-Www format: "
            f"{selected_hb_week_period!r}."
        )

    iso_week_year = int(period_match.group("year"))
    iso_week_number = int(period_match.group("week"))
    try:
        iso_week_monday = date.fromisocalendar(
            iso_week_year,
            iso_week_number,
            1,
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid HB ISO week period: {selected_hb_week_period!r}."
        ) from error

    try:
        return TimeUnit.parse(configured_hb_time_unit, selected_hb_week_period)
    except ValueError as error:
        if _UNSUPPORTED_PENDULUM_WEEK_TOKEN not in str(error):
            raise

    return SelectedTimeUnit(
        timeunit=configured_hb_time_unit,
        dt=pendulum.datetime(
            iso_week_monday.year,
            month=iso_week_monday.month,
            day=iso_week_monday.day,
        ),
    )


def format_hb_week_period(selected_hb_week: SelectedTimeUnit) -> str:
    """Format a selected HB week using its ISO week-year and week number."""
    if selected_hb_week.timeunit.frequency is not TimeUnitType.WEEK:
        raise ValueError("HB week period formatting requires a WEEK TimeUnit.")

    iso_week_year, iso_week_number, _ = selected_hb_week.dt.isocalendar()
    return f"{iso_week_year:04d}-W{iso_week_number:02d}"
