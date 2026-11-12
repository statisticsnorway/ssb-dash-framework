import pandas as pd
import pytest
from pandas.api.types import is_numeric_dtype

from ssb_dash_framework.modules.hb.altinn_normalization import (
    normalize_altinn_hb_candidate_records,
)


def test_normalize_altinn_hb_candidate_records_maps_values_and_preserves_missing() -> (
    None
):
    selected_active_candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024", "2024", "2025"],
            "skjema": ["RA-0187"] * 3,
            "ident": ["unit-1", "unit-2", "unit-1"],
            "refnr": ["ref-1", "ref-2", "ref-3"],
            "feltsti": ["/turnover", "/turnover", "/other-field"],
            "verdi": ["12.5", None, "999"],
            "feltnavn": ["turnover", "turnover", "other"],
        }
    )

    hb_data_result = normalize_altinn_hb_candidate_records(
        selected_active_candidate_records,
        selected_feltsti="/turnover",
    )

    assert list(hb_data_result.hb_dataframe.columns) == [
        "unit_id",
        "period",
        "value",
    ]
    assert list(
        zip(
            hb_data_result.hb_dataframe["unit_id"],
            hb_data_result.hb_dataframe["period"],
            strict=True,
        )
    ) == [("unit-1", "2024"), ("unit-2", "2024"), ("unit-1", "2025")]
    assert hb_data_result.hb_dataframe["value"].iloc[0] == 12.5
    assert pd.isna(hb_data_result.hb_dataframe["value"].iloc[1])
    assert pd.isna(hb_data_result.hb_dataframe["value"].iloc[2])
    assert is_numeric_dtype(hb_data_result.hb_dataframe["value"])
    assert not hb_data_result.hb_dataframe.duplicated(["unit_id", "period"]).any()
    assert hb_data_result.hb_warnings == ()


def test_normalize_altinn_hb_candidate_records_reports_ambiguous_exact_answers() -> (
    None
):
    selected_active_candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024", "2024", "2024"],
            "skjema": ["RA-0187"] * 3,
            "ident": ["unit-1"] * 3,
            "refnr": ["ref-1"] * 3,
            "feltsti": ["/turnover", "/turnover", "/other-field"],
            "verdi": ["12.5", "13.5", "999"],
        }
    )

    hb_data_result = normalize_altinn_hb_candidate_records(
        selected_active_candidate_records,
        selected_feltsti="/turnover",
    )

    assert len(hb_data_result.hb_dataframe) == 1
    assert pd.isna(hb_data_result.hb_dataframe.loc[0, "value"])
    assert len(hb_data_result.hb_warnings) == 1
    assert hb_data_result.hb_warnings[0].unit_id == "unit-1"
    assert hb_data_result.hb_warnings[0].period == "2024"
    assert hb_data_result.hb_warnings[0].message == (
        "Multiple answers matched the configured field for unit unit-1 in "
        "period 2024. No value was selected. The analysis method determines "
        "how this missing value affects the results. Excluding units can "
        "change the population used to calculate results and may affect "
        "outlier thresholds or classifications for other units."
    )


@pytest.mark.parametrize("raw_value", ["not-a-number", True, [1]])
def test_normalize_altinn_hb_candidate_records_rejects_unconvertible_values(
    raw_value: object,
) -> None:
    selected_active_candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024"],
            "skjema": ["RA-0187"],
            "ident": ["unit-1"],
            "feltsti": ["/turnover"],
            "verdi": [raw_value],
        }
    )

    with pytest.raises(
        ValueError,
        match=r"unit 'unit-1' in period '2024'.*not a real number",
    ):
        normalize_altinn_hb_candidate_records(
            selected_active_candidate_records,
            selected_feltsti="/turnover",
        )


def test_normalize_altinn_hb_candidate_records_rejects_empty_input() -> None:
    selected_active_candidate_records = pd.DataFrame(
        columns=["iso_periode", "skjema", "ident", "feltsti", "verdi"]
    )

    with pytest.raises(ValueError, match="No selected Altinn HB candidate records"):
        normalize_altinn_hb_candidate_records(
            selected_active_candidate_records,
            selected_feltsti="/turnover",
        )


def test_normalize_altinn_hb_candidate_records_rejects_missing_columns() -> None:
    with pytest.raises(
        ValueError,
        match="missing required columns: feltsti, ident, iso_periode, skjema, verdi",
    ):
        normalize_altinn_hb_candidate_records(
            pd.DataFrame({"refnr": ["ref-1"]}),
            selected_feltsti="/turnover",
        )


def test_normalize_altinn_hb_candidate_records_rejects_duplicate_columns() -> None:
    selected_active_candidate_records = pd.DataFrame(
        [
            ["2024", "RA-0187", "unit-1", "/turnover", "12.5", "12.5"],
        ],
        columns=[
            "iso_periode",
            "skjema",
            "ident",
            "feltsti",
            "verdi",
            "verdi",
        ],
    )

    with pytest.raises(ValueError, match="must not have duplicate columns"):
        normalize_altinn_hb_candidate_records(
            selected_active_candidate_records,
            selected_feltsti="/turnover",
        )


def test_normalize_altinn_hb_candidate_records_rejects_empty_feltsti() -> None:
    with pytest.raises(ValueError, match="selected_feltsti must be a non-empty"):
        normalize_altinn_hb_candidate_records(
            pd.DataFrame(),
            selected_feltsti=" ",
        )


def test_normalize_altinn_hb_candidate_records_requires_dataframe() -> None:
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        normalize_altinn_hb_candidate_records(
            [],
            selected_feltsti="/turnover",
        )
