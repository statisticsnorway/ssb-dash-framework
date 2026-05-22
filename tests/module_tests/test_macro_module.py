from ssb_dash_framework import MacroModule
from ssb_dash_framework import MacroModuleTab
from ssb_dash_framework import MacroModuleWindow
from ssb_dash_framework import set_variables

HEATMAP_VARIABLES: dict[str, str] = {
    "omsetning": "omsetning",
    "ts_salgsint": "salgsint",
    "nopost_driftskostnader": "driftskost",
    "sysselsetting_syss": "sysselsatte",
    "sysselsetting_ansatte": "lønnstakere",
    "sysselsetting_arsverk": "årsverk",
    "nopost_lonnskostnader": "lønnskost",
    "nopost_p5000": "lønn",
    "ts_vikarutgifter": "vikarutg",
    "ts_forbruk": "forbruk",
    "nopost_p4005": "p4005",
    "produksjonsverdi": "prodv",
    "bearbeidingsverdi": "bearbv",
    "produktinnsats": "prodins",
    "nopost_driftsresultat": "driftsres",
    "brutto_driftsresultat": "brut_driftsres",
    "ts_varehan": "varehandel",
    "totkjop": "totalkjøp",
    "ts_anlegg": "anlegg",
    "bruttoinvestering_oslo": "brut_inv_oslo",
    "bruttoinvestering_kvgr": "brut_inv_kvgr",
}


def dummy_file_path_resolver(aar: int, foretak_or_bedrift: str) -> str:
    return f"/dummy/path/p{aar}/statistikkfil_{foretak_or_bedrift}.parquet"


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
        conn=ibis_polars_conn,
        heatmap_variables=HEATMAP_VARIABLES,
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
    MacroModuleWindow(
        time_units=["aar"],
        conn=ibis_polars_conn,
        heatmap_variables=HEATMAP_VARIABLES,
        file_path_resolver=dummy_file_path_resolver,
        consolidated=True,
    )
