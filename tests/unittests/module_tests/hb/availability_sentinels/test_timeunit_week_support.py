import pytest

from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType


@pytest.mark.xfail(
    strict=True,
    reason="Remove the HB fallback when shared TimeUnit supports canonical WEEK periods.",
)
def test_shared_timeunit_week_period_round_trip_is_supported() -> None:
    week_time_unit = TimeUnit(name="week", frequency=TimeUnitType.WEEK)

    selected_week = TimeUnit.parse(week_time_unit, "2024-W01")

    assert selected_week.to_str() == "2024-W01"
