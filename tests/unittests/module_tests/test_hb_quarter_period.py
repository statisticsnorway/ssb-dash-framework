import pytest

from ssb_dash_framework.modules.hb.quarter_period import format_hb_quarter_period
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


@pytest.mark.parametrize(
    "quarter_period",
    ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"],
)
def test_hb_quarter_period_formats_canonically(quarter_period: str) -> None:
    quarter_time_unit = TimeUnit(name="quarter", frequency=TimeUnitType.QUARTER)
    selected_hb_quarter = TimeUnit.parse(quarter_time_unit, quarter_period)

    assert format_hb_quarter_period(selected_hb_quarter) == quarter_period


def test_hb_quarter_period_subtraction_formats_previous_year_q4() -> None:
    quarter_time_unit = TimeUnit(name="quarter", frequency=TimeUnitType.QUARTER)
    selected_hb_quarter = TimeUnit.parse(quarter_time_unit, "2024-Q1")

    previous_hb_quarter = selected_hb_quarter.subtract(1)

    assert format_hb_quarter_period(previous_hb_quarter) == "2023-Q4"


def test_hb_quarter_period_formatter_rejects_non_quarter_time_unit() -> None:
    month_time_unit = TimeUnit(name="month", frequency=TimeUnitType.MONTH)
    selected_hb_month = TimeUnit.parse(month_time_unit, "2024-01")

    with pytest.raises(ValueError, match="requires a QUARTER TimeUnit"):
        format_hb_quarter_period(selected_hb_month)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Remove the HB formatter when shared SelectedTimeUnit.to_str() "
        "formats canonical QUARTER periods."
    ),
)
def test_shared_timeunit_quarter_period_round_trip_is_supported() -> None:
    quarter_time_unit = TimeUnit(name="quarter", frequency=TimeUnitType.QUARTER)
    selected_hb_quarter = TimeUnit.parse(quarter_time_unit, "2024-Q1")

    assert selected_hb_quarter.to_str() == "2024-Q1"
