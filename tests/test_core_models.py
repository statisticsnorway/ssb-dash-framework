"""Tests for UpdateSkjemadata's configurable mapping-table lookup (``_get_feltsti``)."""

import ibis
import pandas as pd

from ssb_dash_framework.utils.core_models import UpdateSkjemadata


def _make_update(**overrides: object) -> UpdateSkjemadata:
    base: dict[str, object] = dict(
        table="skjemadata_foretak",
        skjema="RA-0255",
        ident="123",
        refnr="r1",
        time_units={"aar": "2024"},
        column="verdi",
        variable="omsetning",
        value="100",
        old_value=None,
        long=True,
    )
    base.update(overrides)
    return UpdateSkjemadata(**base)  # type: ignore[arg-type]


def _conn_with_mapping(data: dict[str, list[str]]) -> ibis.BaseBackend:
    conn = ibis.connect("duckdb://")
    conn.create_table("mapping_variabelnavn", pd.DataFrame(data))
    return conn


def test_updateskjemadata_mapping_config_defaults() -> None:
    """Defaults preserve the previous hardcoded behaviour."""
    update = _make_update()
    assert update.mapping_table == "mapping_variabelnavn"
    assert update.mapping_match_column == "variabel"
    assert update.mapping_result_column == "feltsti"


def test_get_feltsti_default_columns() -> None:
    """Default columns (variabel -> feltsti) keep resolving the long name."""
    conn = _conn_with_mapping(
        {
            "aar": ["2024"],
            "skjema": ["RA-0255"],
            "variabel": ["omsetning"],
            "feltsti": ["sum.omsetning.total"],
        }
    )
    update = _make_update()
    assert update._get_feltsti(conn) == "sum.omsetning.total"


def test_get_feltsti_custom_columns() -> None:
    """A project whose table uses variabel_kortnavn/variabel_feltsti can configure it."""
    conn = ibis.connect("duckdb://")
    conn.create_table(
        "mapping_variabelnavn",
        pd.DataFrame(
            {
                "aar": ["2024"],
                "skjema": ["RA-0255"],
                "variabel_kortnavn": ["omsetning"],
                "variabel_feltsti": ["sum.omsetning.total"],
            }
        ),
    )
    update = _make_update(
        mapping_match_column="variabel_kortnavn",
        mapping_result_column="variabel_feltsti",
    )
    assert update._get_feltsti(conn) == "sum.omsetning.total"


def test_get_feltsti_custom_table_name() -> None:
    """The lookup table name itself is configurable."""
    conn = ibis.connect("duckdb://")
    conn.create_table(
        "feltsti_mapping",
        pd.DataFrame(
            {
                "aar": ["2024"],
                "skjema": ["RA-0255"],
                "variabel": ["omsetning"],
                "feltsti": ["sum.omsetning.total"],
            }
        ),
    )
    update = _make_update(mapping_table="feltsti_mapping")
    assert update._get_feltsti(conn) == "sum.omsetning.total"


def test_get_feltsti_falls_back_to_short_name_when_missing() -> None:
    """No matching row -> fall back to the short name (self.variable)."""
    conn = _conn_with_mapping(
        {
            "aar": ["2024"],
            "skjema": ["RA-0255"],
            "variabel": ["something_else"],
            "feltsti": ["x"],
        }
    )
    update = _make_update(variable="omsetning")
    assert update._get_feltsti(conn) == "omsetning"
