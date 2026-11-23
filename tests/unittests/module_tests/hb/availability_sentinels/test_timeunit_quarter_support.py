import pytest

from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType


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
