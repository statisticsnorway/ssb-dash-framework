from ssb_dash_framework import MacroModuleConsolidated
from ssb_dash_framework import MacroModuleConsolidatedTab
from ssb_dash_framework import MacroModuleConsolidatedWindow
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert MacroModuleConsolidated is not None
    assert MacroModuleConsolidatedTab is not None
    assert MacroModuleConsolidatedWindow is not None


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
    MacroModuleConsolidatedTab(
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
    MacroModuleConsolidatedWindow(
        time_units=["aar"],
        base_path="/buckets/produkt/dummybucket/klargjorte-data",
        conn=ibis_polars_conn,
    )
