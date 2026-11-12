from contextlib import contextmanager
from unittest.mock import Mock
from unittest.mock import call

import ibis
import pandas as pd
import pytest

import ssb_dash_framework.modules.hb.altinn_candidate_retrieval as candidate_retrieval
from ssb_dash_framework.modules.hb.altinn_candidate_retrieval import (
    AltinnHBCandidateRetriever,
)


@pytest.mark.backends("sqlite")
def test_active_candidate_selection_uses_latest_submission_per_period(
    db_backend: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sqlite_backend = ibis.sqlite.connect(":memory:")
    sqlite_backend.raw_sql(
        "CREATE TABLE skjemamottak (iso_periode TEXT, skjema TEXT, ident TEXT, "
        "refnr TEXT, dato_mottatt TIMESTAMP, aktiv BOOLEAN)"
    )
    sqlite_backend.raw_sql(
        "INSERT INTO skjemamottak VALUES "
        "('2024', 'RA-0187', 'unit-1', 'inactive-latest', '2024-01-24', FALSE), "
        "('2024', 'RA-0187', 'unit-1', 'active-old', '2024-01-22', TRUE), "
        "('2024', 'RA-0187', 'unit-1', 'active-latest', '2024-01-23', TRUE), "
        "('2025', 'RA-0187', 'unit-1', 'next-period', '2025-01-23', TRUE), "
        "('2024', 'RA-OTHER', 'unit-1', 'other-form', '2024-01-25', TRUE)"
    )

    @contextmanager
    def use_sqlite_backend():
        yield sqlite_backend

    monkeypatch.setattr(candidate_retrieval, "get_connection", use_sqlite_backend)
    active_refnr_helper = Mock(
        wraps=candidate_retrieval.active_no_duplicates_refnr_list
    )
    monkeypatch.setattr(
        candidate_retrieval,
        "active_no_duplicates_refnr_list",
        active_refnr_helper,
    )
    candidate_retriever = AltinnHBCandidateRetriever(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )
    candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024", "2024", "2024", "2025", "2024"],
            "skjema": ["RA-0187", "RA-0187", "RA-0187", "RA-0187", "RA-OTHER"],
            "ident": ["unit-1"] * 5,
            "refnr": [
                "inactive-latest",
                "active-old",
                "active-latest",
                "next-period",
                "other-form",
            ],
        }
    )

    try:
        selected_candidate_records = (
            candidate_retriever.select_active_candidate_records(
                candidate_records,
                hb_comparison_periods=("2024", "2025"),
            )
        )
    finally:
        sqlite_backend.disconnect()

    assert active_refnr_helper.call_args_list == [
        call(
            sqlite_backend,
            "RA-0187",
            filters={"iso_periode": "2024"},
        ),
        call(
            sqlite_backend,
            "RA-0187",
            filters={"iso_periode": "2025"},
        ),
    ]
    assert list(
        zip(
            selected_candidate_records["iso_periode"],
            selected_candidate_records["skjema"],
            selected_candidate_records["ident"],
            selected_candidate_records["refnr"],
            strict=True,
        )
    ) == [
        ("2024", "RA-0187", "unit-1", "active-latest"),
        ("2025", "RA-0187", "unit-1", "next-period"),
    ]


def test_active_submission_coverage_reports_missing_unit_and_period() -> None:
    candidate_retriever = AltinnHBCandidateRetriever(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )
    candidate_records = pd.DataFrame(
        {
            "iso_periode": ["2024", "2025"],
            "skjema": ["RA-0187", "RA-0187"],
            "ident": ["unit-1", "unit-2"],
            "refnr": ["active-2024", None],
        }
    )
    selected_active_candidate_records = candidate_records.loc[
        candidate_records["refnr"].notna()
    ]

    with pytest.raises(
        ValueError,
        match="unit 'unit-2' in period '2025'",
    ):
        candidate_retriever.validate_active_submission_coverage(
            candidate_records,
            selected_active_candidate_records,
        )
