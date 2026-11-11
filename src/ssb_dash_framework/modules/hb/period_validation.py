"""Canonical period validation shared by HB input and resolution helpers."""

import re
from datetime import date
from typing import Final

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

_HB_PERIOD_PATTERNS: Final[dict[TimeUnitType, re.Pattern[str]]] = {
    TimeUnitType.YEAR: re.compile(r"\d{4}"),
    TimeUnitType.HALF_YEAR: re.compile(r"\d{4}-[12]"),
    TimeUnitType.QUARTER: re.compile(r"\d{4}-Q[1-4]"),
    TimeUnitType.MONTH: re.compile(r"\d{4}-(?:0[1-9]|1[0-2])"),
    TimeUnitType.WEEK: re.compile(r"\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])"),
    TimeUnitType.DAY: re.compile(r"\d{4}-\d{2}-\d{2}"),
}


def is_canonical_hb_period(
    period_value: object,
    frequency: TimeUnitType,
) -> bool:
    """Return whether a value is valid and canonical for an HB frequency."""
    if not isinstance(frequency, TimeUnitType):
        raise TypeError("HB period frequency must be a TimeUnitType.")
    if not isinstance(period_value, str):
        return False

    period_match = _HB_PERIOD_PATTERNS[frequency].fullmatch(period_value)
    if period_match is None:
        return False

    try:
        match frequency:
            case TimeUnitType.YEAR:
                date(int(period_value), 1, 1)
            case TimeUnitType.HALF_YEAR:
                year, half_year = period_value.split("-")
                date(int(year), 1 if half_year == "1" else 7, 1)
            case TimeUnitType.QUARTER:
                year, quarter = period_value.split("-Q")
                month = 1 + (int(quarter) - 1) * 3
                date(int(year), month, 1)
            case TimeUnitType.MONTH:
                year, month = period_value.split("-")
                date(int(year), int(month), 1)
            case TimeUnitType.WEEK:
                year, week = period_value.split("-W")
                date.fromisocalendar(int(year), int(week), 1)
            case TimeUnitType.DAY:
                date.fromisoformat(period_value)
    except ValueError:
        return False

    return True
