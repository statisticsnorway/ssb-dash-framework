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


@pytest.mark.parametrize(
    ("frequency", "invalid_hb_period"),
    [
        (TimeUnitType.YEAR, "24"),
        (TimeUnitType.HALF_YEAR, "2024-3"),
        (TimeUnitType.QUARTER, "2024-Q5"),
        (TimeUnitType.MONTH, "2024-13"),
        (TimeUnitType.WEEK, "2021-W53"),
        (TimeUnitType.DAY, "2024-02-30"),
    ],
)
def test_hb_comparison_period_resolution_rejects_invalid_periods(
    frequency: TimeUnitType,
    invalid_hb_period: str,
) -> None:
    configured_hb_time_unit = TimeUnit(
        name=frequency.name.lower(),
        frequency=frequency,
    )

    with pytest.raises(ValueError) as error:
        resolve_hb_comparison_periods(
            invalid_hb_period,
            configured_hb_time_unit,
        )

    assert f"canonical value for {frequency.name}" in str(error.value)
    assert repr(invalid_hb_period) in str(error.value)


@pytest.mark.parametrize(
    ("frequency", "canonical_hb_period_for_another_frequency"),
    [
        (TimeUnitType.YEAR, "2024-01"),
        (TimeUnitType.HALF_YEAR, "2024"),
        (TimeUnitType.QUARTER, "2024-1"),
        (TimeUnitType.MONTH, "2024-Q1"),
        (TimeUnitType.WEEK, "2024-01"),
        (TimeUnitType.DAY, "2024-W01"),
    ],
)
def test_hb_comparison_period_resolution_rejects_frequency_mismatch(
    frequency: TimeUnitType,
    canonical_hb_period_for_another_frequency: str,
) -> None:
    configured_hb_time_unit = TimeUnit(
        name=frequency.name.lower(),
        frequency=frequency,
    )

    with pytest.raises(ValueError) as error:
        resolve_hb_comparison_periods(
            canonical_hb_period_for_another_frequency,
            configured_hb_time_unit,
        )

    assert f"canonical value for {frequency.name}" in str(error.value)
