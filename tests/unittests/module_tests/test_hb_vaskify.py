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


def valid_vaskify_result_dataframe(
    comparison_periods: tuple[str, str] = ("2023", "2024"),
    *,
    include_strata: bool = False,
) -> pd.DataFrame:
    result = pd.DataFrame(
        {
            "unit_id": ["unit-1"],
            f"value_{comparison_periods[0]}": [10.0],
            f"value_{comparison_periods[1]}": [12.0],
            "lower_limit": [0.8],
            "upper_limit": [1.2],
            "ratio": [1.2],
            "median_ratio": [1.0],
            "flag_hb": [0],
        }
    )
    if include_strata:
        result["strata"] = ["group-1"]
    return result


def _run_direct_vaskify_hb(
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
) -> pd.DataFrame:
    detector = hb_vaskify.Detect(hb_input_dataframe, id_nr="unit_id")
    return detector.hb(
        y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="",
        pu=0.5,
        pa=0.05,
        pc=20,
        percentiles=(0.25, 0.75),
        flag="flag_hb",
        output_format="wide",
        output_scope="all",
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
    expected_result = valid_vaskify_result_dataframe(
        include_strata=configured_hb_strata_variable is not None,
    )
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
    "invalid_result",
    [None, [], {"unit_id": ["unit-1"]}],
)
def test_run_hb_vaskify_rejects_non_dataframe_results(
    monkeypatch: pytest.MonkeyPatch,
    invalid_result: object,
) -> None:
    detector = Mock()
    detector.hb.return_value = invalid_result
    monkeypatch.setattr(hb_vaskify, "Detect", Mock(return_value=detector))

    with pytest.raises(TypeError, match="result must be a pandas DataFrame"):
        hb_vaskify.run_hb_vaskify(
            valid_hb_input_dataframe(),
            hb_comparison_periods=("2023", "2024"),
        )


@pytest.mark.parametrize(
    "missing_column",
    [
        "unit_id",
        "value_2023",
        "value_2024",
        "lower_limit",
        "upper_limit",
        "ratio",
        "median_ratio",
        "flag_hb",
    ],
)
def test_run_hb_vaskify_rejects_results_missing_required_columns(
    monkeypatch: pytest.MonkeyPatch,
    missing_column: str,
) -> None:
    detector = Mock()
    detector.hb.return_value = valid_vaskify_result_dataframe().drop(
        columns=[missing_column]
    )
    monkeypatch.setattr(hb_vaskify, "Detect", Mock(return_value=detector))

    with pytest.raises(ValueError, match=missing_column):
        hb_vaskify.run_hb_vaskify(
            valid_hb_input_dataframe(),
            hb_comparison_periods=("2023", "2024"),
        )


def test_run_hb_vaskify_requires_result_strata_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    detector = Mock()
    detector.hb.return_value = valid_vaskify_result_dataframe()
    monkeypatch.setattr(hb_vaskify, "Detect", Mock(return_value=detector))

    with pytest.raises(ValueError, match="strata"):
        hb_vaskify.run_hb_vaskify(
            valid_hb_input_dataframe(),
            hb_comparison_periods=("2023", "2024"),
            configured_hb_strata_variable="industry",
        )


def test_run_hb_vaskify_allows_extra_columns_and_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_result = valid_vaskify_result_dataframe()
    expected_result["context"] = ["preserved"]
    detector = Mock()
    detector.hb.return_value = expected_result
    monkeypatch.setattr(hb_vaskify, "Detect", Mock(return_value=detector))

    result = hb_vaskify.run_hb_vaskify(
        valid_hb_input_dataframe(),
        hb_comparison_periods=("2023", "2024"),
    )

    assert result is expected_result

    empty_result = valid_vaskify_result_dataframe().iloc[0:0]
    detector.hb.return_value = empty_result
    result = hb_vaskify.run_hb_vaskify(
        valid_hb_input_dataframe(),
        hb_comparison_periods=("2023", "2024"),
    )

    assert result is empty_result


@pytest.mark.parametrize(
    ("comparison_periods", "error_type", "error_message"),
    [
        ((), ValueError, "exactly two periods"),
        (("2023",), ValueError, "exactly two periods"),
        (("2023", "2024", "2025"), ValueError, "exactly two periods"),
        (("2023", "2023"), ValueError, "must be distinct"),
        (("2023", "2024-13"), ValueError, "must be canonical"),
        (("2023", "2023-01"), ValueError, "same canonical TimeUnit frequency"),
        (("2023-Q1", "2023-01"), ValueError, "same canonical TimeUnit frequency"),
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


@pytest.mark.parametrize(
    "comparison_periods",
    [("2023-1", "2023-2"), ("2023-2", "2024-1")],
)
def test_run_hb_vaskify_rejects_half_year_periods_before_detect(
    monkeypatch: pytest.MonkeyPatch,
    comparison_periods: tuple[str, str],
) -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": [
                comparison_periods[0],
                comparison_periods[1],
                comparison_periods[0],
                comparison_periods[1],
            ],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )
    detect = Mock()
    monkeypatch.setattr(hb_vaskify, "Detect", detect)

    with pytest.raises(ValueError, match="HALF_YEAR comparisons are disabled"):
        hb_vaskify.run_hb_vaskify(
            hb_input_dataframe,
            hb_comparison_periods=comparison_periods,
        )

    detect.assert_not_called()


@pytest.mark.parametrize(
    "comparison_periods",
    [
        ("2023", "2024"),
        ("2023-Q1", "2023-Q2"),
        ("2023-01", "2023-02"),
        ("2024-W01", "2024-W02"),
        ("2024-01-01", "2024-01-02"),
    ],
)
def test_run_hb_vaskify_allows_other_canonical_frequencies(
    monkeypatch: pytest.MonkeyPatch,
    comparison_periods: tuple[str, str],
) -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": [
                comparison_periods[0],
                comparison_periods[1],
                comparison_periods[0],
                comparison_periods[1],
            ],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )
    detector = Mock()
    detector.hb.return_value = valid_vaskify_result_dataframe(comparison_periods)
    detect = Mock(return_value=detector)
    monkeypatch.setattr(hb_vaskify, "Detect", detect)

    hb_vaskify.run_hb_vaskify(
        hb_input_dataframe,
        hb_comparison_periods=comparison_periods,
    )

    detect.assert_called_once_with(hb_input_dataframe, id_nr="unit_id")
    assert detector.hb.call_args.kwargs["time_periods"] == list(comparison_periods)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Native Vaskify half-year support is available; remove the HALF_YEAR "
        "execution guard and enable native half-year periods."
    ),
)
def test_installed_vaskify_supports_canonical_half_year_periods() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": ["2023-2", "2024-1", "2023-2", "2024-1"],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )

    result = _run_direct_vaskify_hb(
        hb_input_dataframe,
        ("2023-2", "2024-1"),
    )

    assert not result.empty
    assert "unit_id" in result.columns
