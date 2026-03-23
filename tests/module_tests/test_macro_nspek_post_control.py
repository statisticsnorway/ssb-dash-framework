from ssb_dash_framework import MacroNspekPostControl
from ssb_dash_framework import MacroNspekPostControlTab
from ssb_dash_framework import MacroNspekPostControlWindow
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert MacroNspekPostControl is not None
    assert MacroNspekPostControlTab is not None
    assert MacroNspekPostControlWindow is not None

def dummy_file_path_resolver(aar: int, foretak_or_bedrift: str) -> str:
    return f"/dummy/path/p{aar}/statistikkfil_{foretak_or_bedrift}.parquet"

def test_tab_instantiation(ibis_polars_conn) -> None:
    set_variables(
        [
            "foretak",
            "bedrift",
            "aar",
            "ident",
            "statistikkvariabel",
            "altinnskjema",
            "valgt_tabell",
            "refnr",
        ]
    )
    MacroNspekPostControlTab(
        time_units=["aar"],
        conn=ibis_polars_conn,
        file_path_resolver=dummy_file_path_resolver,
        consolidated=True,

    )


def test_window_instantiation(ibis_polars_conn) -> None:
    set_variables(
        [
            "foretak",
            "bedrift",
            "aar",
            "ident",
            "statistikkvariabel",
            "altinnskjema",
            "valgt_tabell",
            "refnr",
        ]
    )
    MacroNspekPostControlWindow(
        time_units=["aar"],
        conn=ibis_polars_conn,
        file_path_resolver=dummy_file_path_resolver,
        consolidated=True,

    )
