import pytest

from ssb_dash_framework.modules.hb.period_resolution import (
    resolve_hb_comparison_periods,
)
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


@pytest.mark.parametrize(
    ("frequency", "selected_hb_period", "expected_previous_hb_period"),
    [
        (TimeUnitType.YEAR, "2024", "2023"),
        (TimeUnitType.HALF_YEAR, "2024-1", "2023-2"),
        (TimeUnitType.QUARTER, "2024-Q1", "2023-Q4"),
        (TimeUnitType.MONTH, "2024-01", "2023-12"),
        (TimeUnitType.WEEK, "2024-W01", "2023-W52"),
        (TimeUnitType.DAY, "2024-01-01", "2023-12-31"),
    ],
)
def test_hb_comparison_period_resolution_rolls_back_one_period(
    frequency: TimeUnitType,
    selected_hb_period: str,
    expected_previous_hb_period: str,
) -> None:
    configured_hb_time_unit = TimeUnit(
        name=frequency.name.lower(),
        frequency=frequency,
    )

    hb_comparison_periods = resolve_hb_comparison_periods(
        selected_hb_period,
        configured_hb_time_unit,
    )

    assert hb_comparison_periods == (
        expected_previous_hb_period,
        selected_hb_period,
    )
