from typing import cast
from unittest.mock import Mock

import pandas as pd
import pytest

import ssb_dash_framework.modules.hb.vaskify as hb_vaskify


def valid_hb_input_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": ["2023", "2024", "2023", "2024"],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )


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


@pytest.mark.parametrize(
    ("comparison_periods", "error_type", "error_message"),
    [
        ((), ValueError, "exactly two periods"),
        (("2023",), ValueError, "exactly two periods"),
        (("2023", "2024", "2025"), ValueError, "exactly two periods"),
        (("2023", "2023"), ValueError, "must be distinct"),
        (("2023", "2024-13"), ValueError, "must be canonical"),
        (("2022", "2024"), ValueError, "exactly the requested comparison periods"),
    ],
)
def test_run_hb_vaskify_rejects_invalid_comparison_periods(
    monkeypatch: pytest.MonkeyPatch,
    comparison_periods: tuple[str, ...],
    error_type: type[Exception],
    error_message: str,
) -> None:
    detect = Mock()
    monkeypatch.setattr(hb_vaskify, "Detect", detect)

    with pytest.raises(error_type, match=error_message):
        hb_vaskify.run_hb_vaskify(
            valid_hb_input_dataframe(),
            hb_comparison_periods=cast(
                tuple[str, str],
                comparison_periods,
            ),
        )

    detect.assert_not_called()


@pytest.mark.parametrize("missing_column", ["unit_id", "period", "value"])
def test_run_hb_vaskify_rejects_missing_required_columns(
    monkeypatch: pytest.MonkeyPatch,
    missing_column: str,
) -> None:
    detect = Mock()
    monkeypatch.setattr(hb_vaskify, "Detect", detect)
    hb_input_dataframe = valid_hb_input_dataframe().drop(columns=[missing_column])

    with pytest.raises(ValueError, match=missing_column):
        hb_vaskify.run_hb_vaskify(
            hb_input_dataframe,
            hb_comparison_periods=("2023", "2024"),
        )

    detect.assert_not_called()


@pytest.mark.parametrize(
    ("column_name", "invalid_values", "error_message"),
    [
        ("unit_id", [1, 1, 2, 2], "unit_id"),
        ("period", [2023, 2024, 2023, 2024], "period"),
        ("value", ["10", "12", "15", "16"], "value"),
    ],
)
def test_run_hb_vaskify_rejects_incompatible_required_column_dtypes(
    monkeypatch: pytest.MonkeyPatch,
    column_name: str,
    invalid_values: list[object],
    error_message: str,
) -> None:
    detect = Mock()
    monkeypatch.setattr(hb_vaskify, "Detect", detect)
    hb_input_dataframe = valid_hb_input_dataframe()
    hb_input_dataframe[column_name] = invalid_values

    with pytest.raises(TypeError, match=error_message):
        hb_vaskify.run_hb_vaskify(
            hb_input_dataframe,
            hb_comparison_periods=("2023", "2024"),
        )

    detect.assert_not_called()


def test_run_hb_vaskify_rejects_missing_configured_strata_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    detect = Mock()
    monkeypatch.setattr(hb_vaskify, "Detect", detect)

    with pytest.raises(ValueError, match="'strata' column"):
        hb_vaskify.run_hb_vaskify(
            valid_hb_input_dataframe(),
            hb_comparison_periods=("2023", "2024"),
            configured_hb_strata_variable="industry",
        )

    detect.assert_not_called()
