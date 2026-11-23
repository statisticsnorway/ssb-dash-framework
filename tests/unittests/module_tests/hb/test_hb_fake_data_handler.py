import pandas as pd
import pytest

from ssb_dash_framework.modules.hb.data_handler import HBDataResult
from ssb_dash_framework.modules.hb.data_handler import validate_hb_dataframe

from .fake_hb_data_handler import FakeHBDataHandler
from .fake_hb_data_handler import FakeHBDataRequest


@pytest.mark.parametrize("configured_hb_strata_variable", ["industry", None])
def test_fake_hb_data_handler_returns_validated_data_and_records_request(
    configured_hb_strata_variable: str | None,
) -> None:
    hb_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1"],
            "period": ["2023", "2024"],
            "value": [10.0, 12.5],
            "strata": [1, 1],
        }
    )
    expected_dataframe = hb_dataframe.copy(deep=True)
    fake_hb_data_handler = FakeHBDataHandler(hb_dataframe)

    hb_data_result = fake_hb_data_handler.get_hb_dataframe(
        selected_hb_variable="turnover",
        hb_comparison_periods=("2023", "2024"),
        configured_hb_strata_variable=configured_hb_strata_variable,
    )

    assert isinstance(hb_data_result, HBDataResult)
    assert hb_data_result.hb_dataframe.equals(expected_dataframe)
    assert hb_data_result.hb_dataframe is not hb_dataframe
    assert hb_data_result.hb_warnings == ()
    assert validate_hb_dataframe(hb_data_result.hb_dataframe) is (
        hb_data_result.hb_dataframe
    )
    assert fake_hb_data_handler.requests == [
        FakeHBDataRequest(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2023", "2024"),
            configured_hb_strata_variable=configured_hb_strata_variable,
        )
    ]

    hb_data_result.hb_dataframe.loc[0, "value"] = 99
    assert hb_dataframe.loc[0, "value"] == 10.0


def test_fake_hb_data_handler_rejects_invalid_fixture() -> None:
    duplicate_unit_period_data = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1"],
            "period": ["2024", "2024"],
            "value": [10.0, 12.5],
        }
    )
    fake_hb_data_handler = FakeHBDataHandler(duplicate_unit_period_data)

    with pytest.raises(
        ValueError,
        match="at most one row per unit_id and period",
    ):
        fake_hb_data_handler.get_hb_dataframe(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2023", "2024"),
        )
