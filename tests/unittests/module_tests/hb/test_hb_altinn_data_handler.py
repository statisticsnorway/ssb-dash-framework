from contextlib import contextmanager
from unittest.mock import Mock

import ibis
import pandas as pd
import pytest

import ssb_dash_framework.modules.hb.altinn_candidate_retrieval as candidate_retrieval
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
        "configured_hb_strata_variable": None,
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


def test_altinn_hb_data_handler_retrieves_strata_from_selected_submissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sqlite_backend = ibis.sqlite.connect(":memory:")
    sqlite_backend.raw_sql(
        "CREATE TABLE enheter (iso_periode TEXT, skjema TEXT, ident TEXT)"
    )
    sqlite_backend.raw_sql(
        "CREATE TABLE skjemamottak (iso_periode TEXT, skjema TEXT, ident TEXT, "
        "refnr TEXT, dato_mottatt TIMESTAMP, aktiv BOOLEAN)"
    )
    sqlite_backend.raw_sql(
        "CREATE TABLE skjemadata (iso_periode TEXT, skjema TEXT, ident TEXT, "
        "refnr TEXT, feltsti TEXT, feltnavn TEXT, verdi TEXT, dybde INTEGER, "
        "indeks INTEGER)"
    )
    sqlite_backend.raw_sql(
        "INSERT INTO enheter VALUES "
        "('2024', 'RA-0187', 'unit-1'), "
        "('2025', 'RA-0187', 'unit-1')"
    )
    sqlite_backend.raw_sql(
        "INSERT INTO skjemamottak VALUES "
        "('2024', 'RA-0187', 'unit-1', 'old-2024', '2024-01-01', TRUE), "
        "('2024', 'RA-0187', 'unit-1', 'active-2024', '2024-01-02', TRUE), "
        "('2025', 'RA-0187', 'unit-1', 'active-2025', '2025-01-02', TRUE)"
    )
    sqlite_backend.raw_sql(
        "INSERT INTO skjemadata VALUES "
        "('2024', 'RA-0187', 'unit-1', 'old-2024', '/turnover', "
        "'turnover', '900', 1, 0), "
        "('2024', 'RA-0187', 'unit-1', 'old-2024', '/region', "
        "'region', 'old', 1, 0), "
        "('2024', 'RA-0187', 'unit-1', 'active-2024', '/turnover', "
        "'turnover', '100', 1, 0), "
        "('2024', 'RA-0187', 'unit-1', 'active-2024', '/region', "
        "'region', '001', 1, 0), "
        "('2025', 'RA-0187', 'unit-1', 'active-2025', '/turnover', "
        "'turnover', '120', 1, 0), "
        "('2025', 'RA-0187', 'unit-1', 'active-2025', '/region', "
        "'region', '002', 1, 0), "
        "('2025', 'RA-0187', 'unit-1', 'active-2024', '/turnover', "
        "'turnover', '777', 1, 0), "
        "('2025', 'RA-0187', 'unit-1', 'active-2024', '/region', "
        "'region', 'wrong-period', 1, 0), "
        "('2024', 'RA-0187', 'unit-1', 'active-2024', '/other', "
        "'other', 'not-selected', 1, 0)"
    )

    @contextmanager
    def use_sqlite_backend():
        yield sqlite_backend

    monkeypatch.setattr(
        candidate_retrieval,
        "get_connection",
        use_sqlite_backend,
    )
    hb_data_handler = AltinnHBDataHandler(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={
            "turnover": "/turnover",
            "region": "/region",
        },
    )

    try:
        hb_data_result = hb_data_handler.get_hb_dataframe(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2024", "2025"),
            configured_hb_strata_variable="region",
        )
    finally:
        sqlite_backend.disconnect()

    hb_dataframe = hb_data_result.hb_dataframe
    assert list(hb_dataframe.columns) == ["unit_id", "period", "value", "strata"]
    assert hb_dataframe.set_index(["unit_id", "period"])["value"].to_dict() == {
        ("unit-1", "2024"): 100.0,
        ("unit-1", "2025"): 120.0,
    }
    assert hb_dataframe.set_index(["unit_id", "period"])["strata"].to_dict() == {
        ("unit-1", "2024"): "001",
        ("unit-1", "2025"): "002",
    }
    assert all(isinstance(value, str) for value in hb_dataframe["strata"])
    assert not hb_dataframe.duplicated(["unit_id", "period"]).any()
    assert hb_data_result.hb_warnings == ()


def test_altinn_hb_data_handler_rejects_unmapped_strata_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    altinn_connection_getter = Mock()
    monkeypatch.setattr(
        candidate_retrieval,
        "get_connection",
        altinn_connection_getter,
    )
    hb_data_handler = AltinnHBDataHandler(
        configured_hb_form="RA-0187",
        hb_variable_to_feltsti={"turnover": "/turnover"},
    )

    with pytest.raises(ValueError, match="No Altinn feltsti is configured"):
        hb_data_handler.get_hb_dataframe(
            selected_hb_variable="turnover",
            hb_comparison_periods=("2024", "2025"),
            configured_hb_strata_variable="region",
        )

    altinn_connection_getter.assert_not_called()


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
