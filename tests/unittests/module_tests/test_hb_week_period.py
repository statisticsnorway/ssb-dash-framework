from datetime import date

import pytest

from ssb_dash_framework.modules.hb.week_period import format_hb_week_period
from ssb_dash_framework.modules.hb.week_period import parse_hb_week_period
from ssb_dash_framework.setup.variableselector.time_unit import SelectedTimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


@pytest.mark.parametrize(
    ("week_period", "expected_week_start"),
    [
        ("2024-W01", date(2024, 1, 1)),
        ("2021-W01", date(2021, 1, 4)),
        ("2020-W01", date(2019, 12, 30)),
        ("2025-W01", date(2024, 12, 30)),
        ("2020-W53", date(2020, 12, 28)),
        ("2021-W52", date(2021, 12, 27)),
    ],
)
def test_hb_week_period_parsing_and_formatting_round_trip(
    week_period: str,
    expected_week_start: date,
) -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)

    selected_week = parse_hb_week_period(week_period, week_time_unit)

    assert selected_week.dt.date() == expected_week_start
    assert format_hb_week_period(selected_week) == week_period


def test_hb_week_period_subtraction_preserves_iso_week_year() -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)
    selected_week = parse_hb_week_period("2024-W01", week_time_unit)

    previous_week = selected_week.subtract(1)

    assert format_hb_week_period(previous_week) == "2023-W52"


@pytest.mark.parametrize(
    "week_period",
    ["2024-W1", "2024-W00", "2021-W53", "2024-W54", "0000-W01"],
)
def test_hb_week_period_rejects_noncanonical_or_invalid_iso_weeks(
    week_period: str,
) -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)

    with pytest.raises(ValueError):
        parse_hb_week_period(week_period, week_time_unit)


def test_hb_week_period_reraises_unrelated_timeunit_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)

    def fail_with_unrelated_error(
        _configured_hb_time_unit: TimeUnit,
        _selected_hb_week_period: str,
    ) -> SelectedTimeUnit:
        raise ValueError("An unrelated parser error.")

    monkeypatch.setattr(
        TimeUnit,
        "parse",
        staticmethod(fail_with_unrelated_error),
    )

    with pytest.raises(ValueError, match="unrelated parser error"):
        parse_hb_week_period("2024-W01", week_time_unit)


@pytest.mark.xfail(
    strict=True,
    reason="Remove the HB fallback when shared TimeUnit supports canonical WEEK periods.",
)
def test_shared_timeunit_week_period_round_trip_is_supported() -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)

    selected_week = TimeUnit.parse(week_time_unit, "2024-W01")

    assert selected_week.to_str() == "2024-W01"
