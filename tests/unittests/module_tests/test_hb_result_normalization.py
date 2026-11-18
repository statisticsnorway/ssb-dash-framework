import pandas as pd
import pytest

from ssb_dash_framework.modules.hb.vaskify import normalize_hb_result


def test_normalize_hb_result_preserves_candidate_states() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2", "unit-3", "unit-3"],
            "period": ["2023", "2024"] * 3,
            "value": [10.0, 15.0, 20.0, 25.0, 30.0, 35.0],
        }
    )
    hb_vaskify_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-2"],
            "value_2023": [10.0, 20.0],
            "value_2024": [15.0, 25.0],
            "lower_limit": [0.8, 0.8],
            "upper_limit": [1.2, 1.2],
            "ratio": [1.5, 1.0],
            "median_ratio": [1.1, 1.1],
            "flag_hb": [1, 0],
        }
    )

    hb_result_dataframe = normalize_hb_result(
        hb_input_dataframe,
        hb_vaskify_result_dataframe,
        hb_comparison_periods=("2023", "2024"),
    )

    assert hb_result_dataframe["flag_hb"].iloc[:2].tolist() == [1, 0]
    assert pd.isna(hb_result_dataframe.loc[2, "flag_hb"])
    assert pd.isna(hb_result_dataframe.loc[2, "ratio"])
    assert pd.isna(hb_result_dataframe.loc[2, "median_ratio"])
    assert pd.isna(hb_result_dataframe.loc[2, "lower_limit"])
    assert pd.isna(hb_result_dataframe.loc[2, "upper_limit"])


def test_normalize_hb_result_reconciles_units_values_context_and_diagnostics() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": [
                "unit-1",
                "unit-1",
                "unit-2",
                "unit-2",
                "unit-3",
                "unit-3",
            ],
            "period": ["2023", "2024"] * 3,
            "value": [10.0, 15.0, 20.0, 25.0, 30.0, 35.0],
            "strata": ["A", "A", "B", "B", "A", "A"],
            "selector_unit_identifier": [
                "unit-1",
                "unit-1",
                "unit-2",
                "unit-2",
                "unit-3",
                "unit-3",
            ],
            "source_label": [
                "old-1",
                "new-1",
                "old-2",
                "old-2",
                "old-3",
                "new-3",
            ],
        }
    )
    hb_vaskify_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-3"],
            "value_2023": [10.0, 30.0],
            "value_2024": [15.0, 35.0],
            "strata": ["A", "A"],
            "lower_limit": [0.8, 0.8],
            "upper_limit": [1.2, 1.2],
            "ratio": [1.5, 1.0],
            "median_ratio": [1.1, 1.1],
            "flag_hb": [1, 0],
            "method_diagnostic": ["diagnostic-1", "diagnostic-3"],
        }
    )

    hb_result_dataframe = normalize_hb_result(
        hb_input_dataframe,
        hb_vaskify_result_dataframe,
        hb_comparison_periods=("2023", "2024"),
        configured_hb_strata_variable="industry",
    )

    assert hb_result_dataframe["unit_id"].tolist() == [
        "unit-1",
        "unit-2",
        "unit-3",
    ]
    assert hb_result_dataframe["value_2023"].tolist() == [10.0, 20.0, 30.0]
    assert hb_result_dataframe["value_2024"].tolist() == [15.0, 25.0, 35.0]
    assert hb_result_dataframe["strata"].tolist() == ["A", "B", "A"]
    assert hb_result_dataframe["selector_unit_identifier"].tolist() == [
        "unit-1",
        "unit-2",
        "unit-3",
    ]
    assert hb_result_dataframe["source_label_2023"].tolist() == [
        "old-1",
        "old-2",
        "old-3",
    ]
    assert hb_result_dataframe["source_label_2024"].tolist() == [
        "new-1",
        "old-2",
        "new-3",
    ]
    assert hb_result_dataframe.loc[0, "flag_hb"] == 1
    assert hb_result_dataframe.loc[2, "flag_hb"] == 0
    assert hb_result_dataframe.loc[0, "method_diagnostic"] == "diagnostic-1"
    assert hb_result_dataframe.loc[2, "method_diagnostic"] == "diagnostic-3"
    assert pd.isna(hb_result_dataframe.loc[1, "flag_hb"])
    assert pd.isna(hb_result_dataframe.loc[1, "ratio"])
    assert pd.isna(hb_result_dataframe.loc[1, "lower_limit"])
    assert pd.isna(hb_result_dataframe.loc[1, "upper_limit"])
    assert pd.isna(hb_result_dataframe.loc[1, "method_diagnostic"])


def test_normalize_hb_result_rejects_context_column_collisions() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1"],
            "period": ["2023", "2024"],
            "value": [10.0, 15.0],
            "value_2023": ["context", "context"],
        }
    )
    hb_vaskify_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1"],
            "value_2023": [10.0],
            "value_2024": [15.0],
            "lower_limit": [0.8],
            "upper_limit": [1.2],
            "ratio": [1.5],
            "median_ratio": [1.1],
            "flag_hb": [1],
        }
    )

    with pytest.raises(ValueError, match="source context collides"):
        normalize_hb_result(
            hb_input_dataframe,
            hb_vaskify_result_dataframe,
            hb_comparison_periods=("2023", "2024"),
        )
