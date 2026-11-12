from unittest.mock import Mock

import pandas as pd
import pytest

from ssb_dash_framework.modules.hb import AltinnHBDataHandler
from ssb_dash_framework.modules.hb.altinn_candidate_retrieval import (
    AltinnHBCandidateRetriever,
)


def test_altinn_hb_data_handler_composes_candidate_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024", "2024", "2025"],
            "skjema": ["RA-0187"] * 3,
            "ident": ["unit-1", "unit-1", "unit-2"],
            "refnr": ["ref-1", "ref-1", "ref-2"],
            "feltsti": ["/turnover"] * 3,
            "verdi": ["10", "11", "20"],
        }
    )
    retrieve_records = Mock(return_value=candidate_records)
    select_active_records = Mock(return_value=candidate_records)
    monkeypatch.setattr(
        AltinnHBCandidateRetriever,
        "retrieve_candidate_records",
        retrieve_records,
    )
    monkeypatch.setattr(
        AltinnHBCandidateRetriever,
        "select_active_candidate_records",
        select_active_records,
    )

    hb_data_handler = AltinnHBDataHandler(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )

    hb_data_result = hb_data_handler.get_hb_dataframe(
        selected_hb_variable="turnover",
        hb_comparison_periods=("2024", "2025"),
    )

    assert retrieve_records.call_args.kwargs == {
        "selected_hb_variable": "turnover",
        "hb_comparison_periods": ("2024", "2025"),
    }
    assert select_active_records.call_args.args == (candidate_records,)
    assert select_active_records.call_args.kwargs == {
        "hb_comparison_periods": ("2024", "2025"),
    }
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
    ) == [("unit-1", "2024"), ("unit-2", "2025")]
    assert pd.isna(hb_data_result.hb_dataframe["value"].iloc[0])
    assert hb_data_result.hb_dataframe["value"].iloc[1] == 20.0
    assert len(hb_data_result.hb_warnings) == 1
    assert hb_data_result.hb_warnings[0].unit_id == "unit-1"
    assert hb_data_result.hb_warnings[0].period == "2024"


def test_altinn_hb_data_handler_rejects_strata_before_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retrieve_records = Mock()
    monkeypatch.setattr(
        AltinnHBCandidateRetriever,
        "retrieve_candidate_records",
        retrieve_records,
    )
    hb_data_handler = AltinnHBDataHandler(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )

    with pytest.raises(
        NotImplementedError,
        match="does not support a configured strata variable",
    ):
        hb_data_handler.get_hb_dataframe(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2024", "2025"),
            configured_hb_strata_variable="region",
        )

    retrieve_records.assert_not_called()


def test_altinn_hb_data_handler_propagates_missing_active_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024"],
            "skjema": ["RA-0187"],
            "ident": ["unit-1"],
            "refnr": [None],
            "feltsti": ["/turnover"],
            "verdi": [None],
        }
    )
    monkeypatch.setattr(
        AltinnHBCandidateRetriever,
        "retrieve_candidate_records",
        Mock(return_value=candidate_records),
    )
    monkeypatch.setattr(
        AltinnHBCandidateRetriever,
        "select_active_candidate_records",
        Mock(return_value=candidate_records.iloc[0:0]),
    )
    hb_data_handler = AltinnHBDataHandler(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )

    with pytest.raises(
        ValueError,
        match="No active Altinn submission for required unit-period",
    ):
        hb_data_handler.get_hb_dataframe(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2024", "2025"),
        )
