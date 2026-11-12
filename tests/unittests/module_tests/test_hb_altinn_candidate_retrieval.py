import pandas as pd
import pytest

from ssb_dash_framework.modules.hb.altinn_candidate_retrieval import (
    AltinnHBCandidateRetriever,
)


@pytest.mark.backends("sqlite")
def test_candidate_retriever_scopes_and_joins_selected_altinn_answers(
    db_backend: str,
) -> None:
    candidate_retriever = AltinnHBCandidateRetriever(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={
            "selected_turnover": "/omsVirksomhetPerioden",
            "previous_turnover": "/omsForrigePerPrefill",
        },
    )

    candidate_records = candidate_retriever.retrieve_candidate_records(
        selected_hb_variable="selected_turnover",
        hb_comparison_periods=("2026-01", "2026-02"),
    )

    assert list(candidate_records.columns) == [
        "iso_periode",
        "skjema",
        "ident",
        "refnr",
        "feltsti",
        "feltnavn",
        "verdi",
        "dybde",
        "indeks",
    ]
    assert set(candidate_records["skjema"]) == {"RA-0187"}
    assert set(candidate_records["iso_periode"]) == {"2026-01", "2026-02"}
    assert set(candidate_records["feltsti"]) == {"/omsVirksomhetPerioden"}
    assert set(candidate_records["feltnavn"]) == {"omsVirksomhetPerioden"}
    assert candidate_records["refnr"].is_unique
    assert candidate_records.set_index("refnr")["verdi"].to_dict() == {
        "6bac48976d75": "6000",
        "1043f5eb9897": "6007",
        "0e91287fe6da": "6014",
        "2ec970116695": "6021",
        "a554ba7db0a3": "6028",
        "36dc58f7b6fe": "6035",
        "03cfdcfc6266": "6042",
    }


@pytest.mark.backends("sqlite")
def test_candidate_retriever_uses_selected_variable_feltsti_mapping(
    db_backend: str,
) -> None:
    candidate_retriever = AltinnHBCandidateRetriever(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={
            "selected_turnover": "/omsVirksomhetPerioden",
            "previous_turnover": "/omsForrigePerPrefill",
        },
    )

    candidate_records = candidate_retriever.retrieve_candidate_records(
        selected_hb_variable="previous_turnover",
        hb_comparison_periods=("2026-01", "2026-02"),
    )

    assert isinstance(candidate_records, pd.DataFrame)
    assert set(candidate_records["feltsti"]) == {"/omsForrigePerPrefill"}
    assert candidate_records.set_index("refnr")["verdi"].to_dict() == {
        "6bac48976d75": "4000",
        "1043f5eb9897": "4005",
        "0e91287fe6da": "4010",
        "2ec970116695": "4015",
        "a554ba7db0a3": "4020",
        "36dc58f7b6fe": "4025",
        "03cfdcfc6266": "4030",
    }
