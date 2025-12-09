from ssb_dash_framework import MacroModule
from ssb_dash_framework import MacroModuleTab
from ssb_dash_framework import MacroModuleWindow
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert MacroModule is not None
    assert MacroModuleTab is not None
    assert MacroModuleWindow is not None


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
    MacroModuleTab(
        time_units=["aar"],
        base_path="/buckets/produkt/dummybucket/klargjorte-data",
        conn=ibis_polars_conn,
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
    MacroModuleWindow(
        time_units=["aar"],
        base_path="/buckets/produkt/dummybucket/klargjorte-data",
        conn=ibis_polars_conn,
    )
