from unittest.mock import Mock

import pandas as pd
import pytest

import ssb_dash_framework.modules.hb.vaskify as hb_vaskify


@pytest.mark.parametrize(
    ("configured_hb_strata_variable", "expected_strata_var"),
    [(None, ""), ("industry", "strata")],
)
def test_run_hb_vaskify_maps_arguments_without_filtering_input(
    monkeypatch: pytest.MonkeyPatch,
    configured_hb_strata_variable: str | None,
    expected_strata_var: str,
) -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": ["2023", "2024", "2023", "2024"],
            "value": [0.0, -5.0, 2.0, float("nan")],
            "strata": [1, 1, 2, 2],
        }
    )
    expected_result = pd.DataFrame({"unit_id": ["unit-1"]})
    detector = Mock()
    detector.hb.return_value = expected_result
    detect = Mock(return_value=detector)
    monkeypatch.setattr(hb_vaskify, "Detect", detect)

    result = hb_vaskify.run_hb_vaskify(
        hb_input_dataframe,
        hb_comparison_periods=("2023", "2024"),
        configured_hb_strata_variable=configured_hb_strata_variable,
    )

    detect.assert_called_once_with(hb_input_dataframe, id_nr="unit_id")
    detector.hb.assert_called_once_with(
        y_var="value",
        time_var="period",
        time_periods=["2023", "2024"],
        strata_var=expected_strata_var,
        pu=0.5,
        pa=0.05,
        pc=20,
        percentiles=(0.25, 0.75),
        flag="flag_hb",
        output_format="wide",
        output_scope="all",
    )
    assert result is expected_result
    assert hb_input_dataframe["value"].tolist()[:3] == [0.0, -5.0, 2.0]
    assert pd.isna(hb_input_dataframe.loc[3, "value"])
