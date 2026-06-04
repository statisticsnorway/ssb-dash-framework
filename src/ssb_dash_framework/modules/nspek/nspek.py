import logging
import os
import re
import time
from pathlib import Path
from typing import ClassVar
from typing import Any

import dash_bootstrap_components as dbc
import ibis
import pandas as pd
from dash import callback
from dash import dcc
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from dash_ag_grid import AgGrid
from dash_iconify import DashIconify
from ibis import _
from ibis.backends import BaseBackend
from pandas.core.frame import DataFrame

from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator
from .nspek_controls import NspekControls
from .nspek_utils import get_nspek_connection
from .nspek_utils import set_nspek_connection

ibis.options.interactive = True
logger = logging.getLogger(__name__)

virksomhetsinfo_variabler = [
    "virksomhetstype",
    "regeltypeForAarsregnskap",
    "regnskapspliktstype",
    "start",
    "slutt",
]

BALANSE_STRUCTURE = {
    "eiendeler": {
        "anleggsmidler": (1000, 1399),
        "omløpsmidler": (1400, 1999),
    },
    "egenkapital_og_gjeld": {
        "egenkapital": (2000, 2099),
        "langsiktig gjeld": (2100, 2299),
        "kortsiktig gjeld": (2300, 2999),
    },
}

RESULTAT_STRUCTURE = {
    "driftsinntekter": {
        "salgsinntekter": (3000, 3399),
        "andre driftsinntekter": (3400, 3999),
    },
    "driftskostnader": {
        "varekostnader": (4000, 4999),
        "lønn og kostnader til ansatte": (5000, 5999),
        "andre driftskostnader": (6000, 7999),
    },
    "finansposter og skattekostnad": {
        "finansinntekter": (8000, 8099),
        "finanskostnader": (8100, 8299),
        "skattekostnader": (8300, 8999),
    },
}

NEGATIVE_ACCOUNTS = {
    "1296",
    "1298",
    "1299",
    "2010",
    "2080",
    "2095",
    "3300",
    "4995",
    "6998",
    "7099",
}


def add_ui_sums(df: pd.DataFrame, structure: dict) -> pd.DataFrame:
    """Adds UI sum rows used for display aggregation in AG Grid.

    Example use: add_ui_sums(df, RESULTAT_STRUCTURE)
    """
    df = df.copy()

    if "post" not in df.columns or "verdi" not in df.columns:
        return df

    df["post"] = df["post"].astype(str)

    post_numeric = pd.to_numeric(df["post"], errors="coerce")
    df_numeric = df.loc[post_numeric.notna()].copy()
    df_numeric["post_int"] = post_numeric.loc[post_numeric.notna()].astype(int)

    def apply_sign(row):
        return -1 if row["post"] in NEGATIVE_ACCOUNTS else 1

    df_numeric["sign"] = df_numeric.apply(apply_sign, axis=1)

    ui_sum_rows = {}

    for _, subgroups in structure.items():
        for label, (start, end) in subgroups.items():

            subset = df_numeric[df_numeric["post_int"].between(start, end)]

            if subset.empty:
                continue

            value = (subset["verdi"].fillna(0) * subset["sign"]).sum()

            ui_sum_rows[f"UI_SUM_{start}_{end}"] = {
                "beskrivelse": f"SUM forslag for {label}",
                "post": f"UI_SUM_{start}_{end}",
                "verdi": value,
                "verdi_compare": None,
                "diff": None,
                "sekvensnummer": None,
                "is_ui_sum": True,
            }

    if structure is RESULTAT_STRUCTURE:

        driftsinntekter = (
            ui_sum_rows["UI_SUM_3000_3399"]["verdi"]
            + ui_sum_rows["UI_SUM_3400_3999"]["verdi"]
        )

        driftskostnader = (
            ui_sum_rows["UI_SUM_4000_4999"]["verdi"]
            + ui_sum_rows["UI_SUM_5000_5999"]["verdi"]
            + ui_sum_rows["UI_SUM_6000_7999"]["verdi"]
        )

        finansposter_og_skattekostnad = (
            ui_sum_rows["UI_SUM_8000_8099"]["verdi"]
            + ui_sum_rows["UI_SUM_8100_8299"]["verdi"]
            + ui_sum_rows["UI_SUM_8300_8999"]["verdi"]
        )

        ui_sum_rows["UI_SUM_3000_3999"] = {
            "beskrivelse": "SUM forslag for driftsinntekter",
            "post": "UI_SUM_3000_3999",
            "verdi": driftsinntekter,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

        ui_sum_rows["UI_SUM_4000_7999"] = {
            "beskrivelse": "SUM forslag for driftskostnader",
            "post": "UI_SUM_4000_7999",
            "verdi": driftskostnader,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

        ui_sum_rows["UI_SUM_8000_8999"] = {
            "beskrivelse": "SUM forslag for finansposter og skattekostnad",
            "post": "UI_SUM_8000_8999",
            "verdi": finansposter_og_skattekostnad,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

        årsresultat = (
            ui_sum_rows["UI_SUM_3000_3999"]["verdi"]
            - ui_sum_rows["UI_SUM_4000_7999"]["verdi"]
            + ui_sum_rows["UI_SUM_8000_8099"]["verdi"]
            - ui_sum_rows["UI_SUM_8100_8299"]["verdi"]
            - ui_sum_rows["UI_SUM_8300_8999"]["verdi"]
        )

        ui_sum_rows["UI_SUM_3000_8999"] = {
            "beskrivelse": "SUM forslag for årsresultat",
            "post": "UI_SUM_3000_8999",
            "verdi": årsresultat,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

    if structure is BALANSE_STRUCTURE:

        eiendeler = (
            ui_sum_rows["UI_SUM_1000_1399"]["verdi"]
            + ui_sum_rows["UI_SUM_1400_1999"]["verdi"]
        )

        egenkapital_og_gjeld = (
            ui_sum_rows["UI_SUM_2000_2099"]["verdi"]
            + ui_sum_rows["UI_SUM_2100_2299"]["verdi"]
            + ui_sum_rows["UI_SUM_2300_2999"]["verdi"]
        )

        ui_sum_rows["UI_SUM_1000_1999"] = {
            "beskrivelse": "SUM forslag for eiendeler",
            "post": "UI_SUM_1000_1999",
            "verdi": eiendeler,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

        ui_sum_rows["UI_SUM_2000_2999"] = {
            "beskrivelse": "SUM forslag for egenkapital og gjeld",
            "post": "UI_SUM_2000_2999",
            "verdi": egenkapital_og_gjeld,
            "verdi_compare": None,
            "diff": None,
            "sekvensnummer": None,
            "is_ui_sum": True,
        }

    insert_after_map = {
        "UI_SUM_1000_1399": "sumBalanseverdiForAnleggsmiddel",
        "UI_SUM_1400_1999": "sumBalanseverdiForOmloepsmiddel",
        "UI_SUM_1000_1999": "sumBalanseverdiForEiendel",
        "UI_SUM_2000_2099": "sumEgenkapital",
        "UI_SUM_2100_2299": "sumLangsiktigGjeld",
        "UI_SUM_2300_2999": "sumKortsiktigGjeld",
        "UI_SUM_2000_2999": "sumGjeldOgEgenkapital",
        "UI_SUM_3000_3399": "3300",
        "UI_SUM_3400_3999": "3911",
        "UI_SUM_4000_4999": "4995",
        "UI_SUM_5000_5999": "5950",
        "UI_SUM_6000_7999": "7913",
        "UI_SUM_3000_3999": "sumDriftsinntekt",
        "UI_SUM_4000_7999": "sumDriftskostnad",
        "UI_SUM_8000_8099": "sumFinansinntekt",
        "UI_SUM_8100_8299": "sumFinanskostnad",
        "UI_SUM_8300_8999": "sumSkattekostnad",
        "": "sumSkattekostnad",
        "UI_SUM_8000_8999": "sumSkattekostnad",
        "UI_SUM_3000_8999": "aarsresultat",
    }

    new_rows = []

    for _, row in df.iterrows():
        new_rows.append(row.to_dict())

        post = row["post"]

        for ui_key, anchor_post in insert_after_map.items():
            if post == anchor_post and ui_key in ui_sum_rows:
                new_rows.append(ui_sum_rows[ui_key])

    for row in new_rows:
        if row.get("is_ui_sum") and row.get("verdi") == 0:
            row["verdi"] = None

    return pd.DataFrame(new_rows)


PETROLEUM_ORGNR = {
    "913905881",
    "914807077",
    "915419062",
    "916358857",
    "918110127",
    "918175334",
    "918500863",
    "918980946",
    "919160675",
    "921166753",
    "924186720",
    "927066440",
    "953133210",
    "975871932",
    "985224323",
    "988217867",
    "988400025",
    "989795848",
    "990888213",
    "991317155",
    "993787787",
    "995152142",
    "996739910",
    "996888177",
    "997015231",
    "998726441",
    "913561473",
    "914048990",
    "919886080",
    "977095239",
}

PETROLEUM_POSTS = {
    "3001",
    "3002",
    "3003",
    "3004",
    "3005",
    "3006",
    "3007",
    "3008",
    "3886",
}


def apply_petroleum_filter(
    df: pd.DataFrame, orgnr: str, toggle_petroleum: list[str]
) -> pd.DataFrame:
    """Filters petroleum-related rows (PETROLEUM_POSTS) based on orgnr (PETROLEUM_ORGNR) and user toggle i UI checkbox.

    Example use: apply_petroleum_filter(df, "979443137", ["show_petroleum"])
    """
    if "show_petroleum" in (toggle_petroleum or []):
        return df

    return df[~df["post"].astype(str).isin(PETROLEUM_POSTS)].copy()


def apply_blank_filter(df: pd.DataFrame, toggle_blank: list[str]) -> pd.DataFrame:
    """Removes or retains rows with blank values and header/subheader row depending on UI toggle state in checkbox.

    Example use: apply_blank_filter(df, ["show_blank"])
    """
    if "show_blank" in (toggle_blank or []):
        return df

    if "verdi_compare" not in df.columns:
        df["verdi_compare"] = pd.NA

    keep_rows = (
        df["verdi"].notna()
        | df["verdi_compare"].notna()
        | df["beskrivelse"].isin(
            [
                "",
                "Eiendeler",
                "Anleggsmidler",
                "Omløpsmidler",
                "Egenkapital og gjeld",
                "Egenkapital",
                "Langsiktig gjeld",
                "Kortsiktig gjeld",
                "Driftsinntekter",
                "Salgsinntekter",
                "Andre driftsinntekter ",
                "Driftskostnader",
                "Varekostnader",
                "Lønn og kostnader til ansatte",
                "Andre driftskostnader",
                "Finansposter og skattekostnad",
                "Finansinntekter",
                "Finanskostnader",
                "Skattekostnader",
            ]
        )
        | df["beskrivelse"].str.startswith("SUM", na=False)
    )

    return df.loc[keep_rows].copy()


TYPE_REGNSKAP_TABLE = {  # type: {database: exampleregnskap, table: tema_example}
    "registrering": {
        "database": "nspek_core",
        "table": "registrering",
    },
    "v_registrering_versjon": {
        "database": "nspek_core",
        "table": "v_registrering_versjon",
    },
    "virksomhet": {
        "database": "virksomhet",
        "table": "tema_virksomhet",
    },
    "balanseregnskap": {
        "database": "balanseregnskap",
        "table": "tema_balanse",
    },
    "resultatregnskap": {
        "database": "resultatregnskap",
        "table": "tema_resultat",
    },
    "enhet_opplysninger": {
        "database": "nspek_core",
        "table": "enhet_opplysninger",
    },
}


def get_versions(conn, ident: str, aar: str) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing all sekvensnummer sorted by versjon_nr from nspek_core view v_registrering_versjon.

    Example use: get_versions(self.conn, "979443137", "2024")
    """
    config = TYPE_REGNSKAP_TABLE["v_registrering_versjon"]

    t = conn.table(config["table"], database=config["database"])

    df = (
        t.filter((_.orgnr == ident) & (_.aar == int(aar)))
        .order_by(_.versjon_nr)
        .select(_.sekvensnummer, _.versjon_nr, _.antall_versjoner, _.dato_mottatt)
        .execute()
    )

    df["label"] = (
        "v"
        + df["versjon_nr"].astype(str)
        + " – "
        + pd.to_datetime(df["dato_mottatt"]).dt.strftime("%Y-%m-%d %H:%M")
    )

    return df


def get_virksomhetsinfo(
    conn, variables_to_fetch: list, ident: str, aar: str, sekvensnummer: int
) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing virksomhetsinfo from nspek files for specified variables for a unit.

    Example use: get_virksomhetsinfo(self.conn, virksomhetsinfo_variabler, "979443137", "2024", 2291859)
    """
    config = TYPE_REGNSKAP_TABLE["virksomhet"]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.filter(t["felt"].isin(variables_to_fetch)).select(["felt", "char_verdi"])
    df = filtered.execute()

    return df


def get_skjoennslignet(
    conn, ident: str, aar: str, sekvensnummer: int
) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing virksomhetsinfo from nspek files for specified variables for a unit.

    Example use: get_skjoennslignet(self.conn, virksomhetsinfo_variabler, "979443137", "2024", 2291859)
    """
    config = TYPE_REGNSKAP_TABLE["enhet_opplysninger"]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.filter(_.opplysning == "skjoennslignet").select(["opplysning"])
    df = filtered.execute()

    return df


def get_bofinfo(ident: str, aar: str) -> pd.DataFrame:
    """
    Fetch and return pandas dataframe containing BOF info from parquet or sqlite fallback for a given orgnr.

    Example use: get_bofinfo("979443137", "2024")
    """

    year = str(aar)

    parquet_paths = [
        (
            f"/buckets/shared/vof/"
            f"situttak/vof-aarsfil_data/"
            f"klargjorte-data/parquet/"
            f"vof-aarsfil_p{year}_v1.parquet"
        ),
        (
            f"/buckets/shared/vof/"
            f"situttak/vof-aarsfil_data/"
            f"klargjorte-data/parquet/"
            f"vof-aarsfil-forelopig_p{year}_v1.parquet"
        ),
    ]

    rename_map = {
        "org_nr": "orgnr",
        "navn": "navn",
        "org_form": "org_form",
        "sn2025_1": "sn2025_1",
        "nace1_sn07": "sn07_1",
        "reg_type": "sf_type",
        "fkommune": "f_kommunenr",
        "status": "statuskode",
        "syss": "sysselsatte",
        "sektor_2014": "sektor_2014",
        "undersektor_2014": "undersektor_2014",
    }

    expected_columns = [
        "orgnr",
        "navn",
        "org_form",
        "sn2025_1",
        "sn07_1",
        "sf_type",
        "f_kommunenr",
        "statuskode",
        "sysselsatte",
        "sektor_2014",
        "undersektor_2014",
    ]

    for path in parquet_paths:

        if not Path(path).exists():
            continue

        try:
            conn = ibis.duckdb.connect()

            t = conn.read_parquet(path)

            df = (
                t.filter(_.org_nr == str(ident))
                .execute()
            )

            if df.empty:
                return pd.DataFrame(columns=expected_columns)

            df = df.rename(columns=rename_map)

            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""

            return df[expected_columns]

        except Exception as e:
            logger.error(
                f"Failed reading parquet {path}: {e}",
                exc_info=True,
            )

    # fallback sqlite
    try:
        conn = ibis.sqlite.connect(
            "/buckets/shared/vof/oracle-hns/ssb_foretak.db"
        )

        t = conn.table("ssb_foretak")

        df = (
            t.filter(_.orgnr == ident)
            .execute()
        )

        return df

    except Exception as e:
        logger.error(
            f"Failed reading sqlite fallback: {e}",
            exc_info=True,
        )

        return pd.DataFrame(columns=expected_columns)


def get_value(series) -> str:
    """Return first value or empty string if no match."""
    return "" if series.empty else str(series.iloc[0])


def post_description_data(regnskapstype: str) -> DataFrame:
    """Returns a pandas dataframe with the npspek posts and their names.

    Example use: post_description_data("balanseregnskap")
    """
    base_path = Path(__file__).parent

    if regnskapstype == "balanseregnskap":
        poster = "nspek_balanseposter"
    elif regnskapstype == "resultatregnskap":
        poster = "nspek_resultatposter"

    post_file_path = base_path / f"{poster}.csv"

    df = pd.read_csv(
        f"{post_file_path}", dtype={"felt": "string"}, keep_default_na=False
    )

    return df[["tekst", "felt"]]


def comment_icon_column():
    return {
        "field": "comment_icon",
        "headerName": "",
        "width": 60,
        "sortable": False,
        "filter": False,
        "resizable": True,
        "pinned": "right",
        "cellStyle": {
            "styleConditions": [
                {
                    "condition": "params.value",
                    "style": {
                        "textAlign": "center",
                        "fontSize": "16px",
                        "cursor": "pointer",
                    },
                }
            ]
        },
        "tooltipField": "comment_text",
    }


def build_column_defs(sekvens_compare=None):

    columns = ["beskrivelse", "post", "verdi", "verdi_compare", "diff", "sekvensnummer"]

    if not sekvens_compare:
        columns = [c for c in columns if c not in ["verdi_compare", "diff"]]

    header_rows: list[str] = [
        "Eiendeler",
        "SUM Eiendeler",
        "SUM forslag for eiendeler",
        "Egenkapital og gjeld",
        "SUM Egenkapital og gjeld",
        "SUM forslag for egenkapital og gjeld",
        "Driftsinntekter",
        "SUM Driftsinntekter",
        "SUM forslag for driftsinntekter",
        "Driftskostnader",
        "SUM Driftskostnader",
        "SUM forslag for driftskostnader",
        "Finansposter og skattekostnad",
        "SUM Finansposter og skattekostnad",
        "SUM forslag for finansposter og skattekostnad",
        "SUM Årsresultat",
        "SUM forslag for årsresultat",
    ]

    subheader_rows: list[str] = [
        "Anleggsmidler",
        "SUM Anleggsmidler",
        "SUM forslag for anleggsmidler",
        "SUM Omløpsmidler",
        "Omløpsmidler",
        "SUM forslag for omløpsmidler",
        "Egenkapital",
        "SUM Egenkapital",
        "SUM forslag for egenkapital",
        "Langsiktig gjeld",
        "SUM Langsiktig gjeld",
        "SUM forslag for langsiktig gjeld",
        "Kortsiktig gjeld",
        "SUM Kortsiktig gjeld",
        "SUM forslag for kortsiktig gjeld",
        "Salgsinntekter",
        "SUM Salgsinntekter",
        "SUM forslag for salgsinntekter",
        "Andre driftsinntekter ",
        "SUM Andre driftsinntekter",
        "SUM forslag for andre driftsinntekter",
        "Varekostnader",
        "SUM Varekostnader",
        "SUM forslag for varekostnader",
        "Lønn og kostnader til ansatte",
        "SUM Lønn og kostnader til ansatte",
        "SUM forslag for lønn og kostnader til ansatte",
        "Andre driftskostnader",
        "SUM Andre driftskostnader",
        "SUM forslag for andre driftskostnader",
        "Finansinntekter",
        "SUM Finansinntekter",
        "SUM forslag for finansinntekter",
        "Finanskostnader",
        "SUM Finanskostnader",
        "SUM forslag for finanskostnader",
        "Skattekostnader",
        "SUM Skattekostnader",
        "SUM forslag for skattekostnader",
    ]

    column_defs = [
        {
            "field": col,
            "headerName": col,
            "sortable": False,
            "resizable": True,
            "hide": col == "sekvensnummer",
            "editable": col == "verdi",
            "flex": 3 if col == "beskrivelse" else 2 if col == "post" else 1,
            "valueFormatter": {
                "function": (
                    "params.value == null ? '' : params.value.toLocaleString('no-NO')"
                    if col in ["verdi", "verdi_compare", "diff"]
                    else None
                )
            },
            "cellStyle": {
                "styleConditions": [
                    {
                        "condition": "params.colDef.field === 'diff' && params.value > 0",
                        "style": {
                            #"backgroundColor": "#e8f5e9",
                            "color": "#1A9D49",
                            "fontWeight": "bold",
                            "textAlign": "right",
                            "paddingRight": "10px",
                        },
                    },
                    {
                        "condition": "params.colDef.field === 'diff' && params.value < 0",
                        "style": {
                            #"backgroundColor": "#ffebee",
                            "color": "#DC3400",
                            "fontWeight": "bold",
                            "textAlign": "right",
                            "paddingRight": "10px",
                        },
                    },
                    {
                        "condition": "['verdi','verdi_compare','diff'].includes(params.colDef.field)",
                        "style": {"textAlign": "right", "paddingRight": "10px"},
                    },
                    {
                        "condition": "params.data.beskrivelse && params.data.beskrivelse.startsWith('SUM') && ['verdi','verdi_compare','diff'].includes(params.colDef.field)",
                        "style": {
                            "fontWeight": "bold",
                            "textAlign": "right",
                            "paddingRight": "10px",
                        },
                    },
                    {
                        "condition": f"params.data && {header_rows}.includes(params.data.beskrivelse)",
                        "style": {"fontWeight": "bold"},
                    },
                    {
                        "condition": f"params.data && {subheader_rows}.includes(params.data.beskrivelse)",
                        "style": {"fontWeight": "bold", "paddingLeft": "30px"},
                    },
                    {
                        "condition": "params.colDef.field === 'beskrivelse'",
                        "style": {"paddingLeft": "50px"},
                    },
                ],
                "defaultStyle": {},
            },
        }
        for col in columns
    ]

    column_defs.append(comment_icon_column())

    return column_defs


def fetch_data_by_orgnr(
    conn, regnskapstype: str, ident: str, aar: str, sekvensnummer: int
) -> pd.DataFrame:
    """Returns a pandas dataframe with all nspek values found in the specified regnskapstype for a unit/orgnr.

    Example use: fetch_data_by_orgnr(self.conn, "resultatregnskap", "932598957", "2024", 2291859)
    """
    config = TYPE_REGNSKAP_TABLE[regnskapstype]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.select(["felt", "belop"])
    df = filtered.to_pandas()

    return df


def get_latest_field_comments(conn, orgnr: str) -> dict:
    """Returns a dictonary with latest aktiv comment for each variabel sorted by opprett descending.

    Example use: get_latest_field_comments(conn, "932598957")
    """
    query = f"""
        SELECT DISTINCT ON (variabel)
            variabel,
            kommentar,
            opprettet,
            opprettet_av
        FROM nspek_core.kommentarfelt_test_2
        WHERE orgnr = '{orgnr}'
        AND nivaa = 'variabel'
        AND aktiv = true
        ORDER BY variabel, opprettet DESC
    """

    cursor = conn.raw_sql(query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        return {}

    latest = {}

    for _, row in df.iterrows():
        felt = str(row["variabel"])

        latest[felt] = {
            "kommentar": row["kommentar"] or "",
            "endret_dato": (
                pd.to_datetime(row["opprettet"]).strftime("%Y-%m-%d %H:%M")
                if pd.notna(row["opprettet"])
                else ""
            ),
            "opprettet_av": row["opprettet_av"] or "",
        }

    return latest


def trigger_refresh(current_data, key):
    """Triggers refresh for a specific UI domain key.

    Example use: trigger_refresh(refresh_data, "balanse")
    """
    new_data = {"status": key}
    new_data["ts"] = time.time_ns()
    return new_data


def clean_whitespace(value: str) -> str:
    """Cleans user input by stripping whitespace.

    Example use: clean_whitespace(" 123 ") returns "123"
    """
    if value is None:
        return ""
    value = str(value).strip()
    return re.sub(r"\s+", "", value)


def validate_orgnr(orgnr: str) -> tuple[bool, str]:
    """Validates organisation number format.

    Example use: validate_orgnr("979443137")
    """
    if not orgnr:
        return False, "Organisasjonsnummer mangler"

    if not orgnr.isdigit():
        return False, "Organisasjonsnummer må kun inneholde tall"

    if len(orgnr) != 9:
        return False, "Organisasjonsnummer må være 9 siffer"

    return True, ""


def orgnr_exists_in_bof(orgnr: str) -> bool:
    """Checks if organisation exists in BOF registry.

    Example use: orgnr_exists_in_bof("979443137")
    """
    try:
        conn = ibis.sqlite.connect("/buckets/shared/vof/oracle-hns/ssb_foretak.db")
        t = conn.table("ssb_foretak")

        df = t.filter(_.orgnr == orgnr).limit(1).execute()

        return not df.empty

    except Exception as e:
        logger.error(f"BOF lookup feilet: {e}")
        return True


def validate_aar(aar: str) -> tuple[bool, str]:
    """Validates year format and range.

    Example use: validate_aar("2024")
    """
    if not aar:
        return False, "År mangler"

    try:
        aar_int = int(aar)
    except ValueError:
        return False, "År må være et tall"

    if aar_int < 2024 or aar_int > 2024:
        return False, "Årgangen finnes ikke i NSPEK enda."

    return True, ""


def has_data(conn, orgnr: str, aar: str) -> bool:
    """Checks if NSPEK data exists for given organisation and year.

    Example use: has_data(conn, "979443137", "2024")
    """
    config = TYPE_REGNSKAP_TABLE["v_registrering_versjon"]

    t = conn.table(config["table"], database=config["database"])

    df = t.filter((_.orgnr == orgnr) & (_.aar == int(aar))).limit(1).execute()

    return not df.empty


MAX_ALLOWED_VALUE = 999_999_999_999


def validate_numeric_input(value: str) -> tuple[bool, str | None]:
    """Validates integer input for nspek grid cells and check for extreme values.

    Example use: validate_numeric_input("1200")
    """
    if value is None or value == "":
        return False, "Verdi kan ikke være tom"

    value = clean_whitespace(str(value))

    try:
        int(value)
    except ValueError:
        return False, "Kun heltall er tillatt"

    if abs(int(value)) > MAX_ALLOWED_VALUE:
        return False, f"Verdien er for stor (maks {MAX_ALLOWED_VALUE})"

    return True, None


def is_negative(value: str) -> bool:
    """Checks whether a numeric string is negative.

    Example use: is_negative("-10")
    """
    try:
        return int(value) < 0
    except Exception:
        return False


def save_regnskap_value(
    conn, regnskapstype: str, sekvensnummer: int, post: str, value: str
):
    """Inserts or updates nspek regnskap values.

    Example use:
    save_regnskap_value(conn, "balanseregnskap", 123, "A1", "1000")
    """
    config = TYPE_REGNSKAP_TABLE[regnskapstype]

    query = f"""
        INSERT INTO {config["database"]}.{config["table"]}
        (sekvensnummer, felt, belop)
        VALUES ({sekvensnummer}, '{post}', '{value}')
        ON CONFLICT (sekvensnummer, felt)
        DO UPDATE SET belop = EXCLUDED.belop
    """

    conn.raw_sql(query)


def handle_regnskap_edit(
    edited, alert_store, refresh_data, regnskapstype: str, refresh_key: str
):
    """Central handler for nspek grid edits (balanse + resultat).

    Example use:
    handle_regnskap_edit(..., "balanseregnskap", "balanse")
    """
    alert_store = alert_store or []

    row = edited[0]["data"]

    if row.get("is_ui_sum") or not str(row.get("post", "")).strip():
        raise PreventUpdate

    ident = row["sekvensnummer"]
    sekvensnummer = row["sekvensnummer"]
    post = row["post"]

    value = clean_whitespace(edited[0]["value"])
    old_value = edited[0]["oldValue"]

    ok, error = validate_numeric_input(value)

    if not ok:
        alert_store = [
            create_alert(error, "danger", ephemeral=True),
            *alert_store,
        ]
        return alert_store, refresh_data, False, None, no_update

    if is_negative(value):

        pending = {
            "regnskapstype": regnskapstype,
            "sekvensnummer": sekvensnummer,
            "post": post,
            "value": value,
            "old_value": old_value,
            "ident": ident,
            "refresh_key": refresh_key,
        }

        message = (
            f"Du forsøker å lagre en negativ verdi {value} for post {post}. "
            f"Dette skal kun skje unntaksvis. Er du sikker?"
        )

        return (
            alert_store,
            refresh_data,
            True,
            pending,
            message,
        )

    try:
        with get_nspek_connection() as conn:

            user = os.getenv("DAPLA_USER", "")[:3]

            conn.raw_sql(f"SET nspek_app.user_id = '{user}'")
            conn.raw_sql("SET nspek_app.process_type = 'editering'")

            save_regnskap_value(conn, regnskapstype, sekvensnummer, post, value)

        alert_store = [
            create_alert(
                f"{post} oppdatert fra {old_value} til {value}",
                "success",
                ephemeral=True,
            ),
            *alert_store,
        ]

    except Exception as e:
        logger.error(e, exc_info=True)

        alert_store = [
            create_alert(
                f"Feil: {str(e)[:80]}",
                "danger",
                ephemeral=True,
            ),
            *alert_store,
        ]

    refresh_data = trigger_refresh(refresh_data, refresh_key)

    return alert_store, refresh_data, False, None, no_update


class Naeringsspesifikasjon:
    """The Naeringsspesifikasjon module lets you view the nspek/naeringsspesifikasjon for a specified foretak (var-ident)."""

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the module_callbacks.
            "foretak",
        ]
    )

    def __init__(self, time_units: list[str], db_user: str | None) -> None:
        """Explanation of module."""
        set_nspek_connection(
            db_user if db_user else "strukt-naering-developers@dapla-group-sa-p-ye.iam"
        )
        self.module_number = Naeringsspesifikasjon._id_number
        self.module_name = self.__class__.__name__
        self.icon = "📒"
        self.label = "NSPEK"

        self.conn: BaseBackend = get_nspek_connection().__enter__()
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        logger.debug("TIME UNITS ", self.time_units)

        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in Naeringsspesifikasjon._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"Naeringsspesifikasjon requires the variable selector option '{var}' to be set."
                ) from e

    def create_info_card(self, title: str, component_id: str, var_type: str):
        card_info = html.Div(
            className="ssb-input",
            children=[
                html.Label(title),
                html.Div(
                    className="input-wrapper",
                    children=[
                        dbc.Input(
                            id=component_id,
                            type=var_type,
                        )
                    ],
                ),
            ],
        )
        return card_info

    def create_dropdown_card(self, title: str, component_id: str):
        dropdown_card = html.Div(
            className="ssb-dropdown",
            children=[
                html.Span(title, className="dropdown-label"),
                dcc.Dropdown(
                    id=component_id,
                    placeholder="-- Velg --",
                    clearable=True,
                ),
            ],
        )
        return dropdown_card

    def create_checkbox(
        self, component_id: str, label: str, value: str, checked: bool = False
    ):
        checkbox = html.Div(
            className="ssb-checkbox d-flex align-items-center",
            children=[
                dcc.Checklist(
                    id=component_id,
                    options=[{"label": "", "value": value}],
                    value=[value] if checked else [],
                ),
                html.Label(
                    label,
                    className="mb-1 ms-2",
                ),
            ],
        )
        return checkbox

    def create_dialog(self, variant: str, title: str, message: str):
        dialog = html.Div(
            className=f"ssb-dialog {variant} mt-2 mb-1",
            children=[
                html.Div(
                    DashIconify(icon=self._map_icon(variant), width=40),
                    className="icon-panel",
                ),
                html.Div(
                    [
                        html.Div(title, className="dialog-title"),
                        html.Div(message, className="content"),
                    ],
                    className="dialog-content",
                ),
                html.Button(
                    "✕",
                    id="close-version-warning",
                    n_clicks=0,
                    className="dialog-close",
                ),
            ],
        )
        return dialog

    def _map_icon(self, variant):
        variant = {
            "warning": "feather:alert-triangle",
            "info": "feather:info",
        }.get(variant, "feather:info")
        return variant

    def get_edit_log_row_style(self):
        return {
            "styleConditions": [
                {
                    "condition": "params.data && params.data.operation_type === 'INSERT' && params.data.process_type === 'editering'",
                    "style": {"backgroundColor": "#c8e6c9"},  # lys grønn
                },
                {
                    "condition": "params.data && params.data.operation_type === 'UPDATE'",
                    "style": {"backgroundColor": "#ffe082"},  # lys gul
                },
                {
                    "condition": "params.data && params.data.operation_type === 'INSERT' && params.data.process_type === 'innsamling'",
                    "style": {"backgroundColor": "#bde4ff"},  # lys blå
                },
            ]
        }

    def get_row_style_with_comments(self):
        return {
            "styleConditions": [
                {
                    "condition": "params.data && params.data.comment_icon",
                    "style": {"backgroundColor": "#ECFEED"},  # SSB grønn 1
                },
            ]
        }

    def get_row_style_ui_sums(self):
        return {
            "styleConditions": [
                {
                    "condition": "params.data && params.data.is_ui_sum",
                    "style": {
                        "fontStyle": "italic",
                        "fontWeight": "normal",
                        "backgroundColor": "#F0F8F9",  # SSB mørk 1
                        "color": "#333333",
                    },
                },
            ]
        }

    def get_row_style_active_comment(self):
        return {
            "styleConditions": [
                {
                    "condition": "params.data.aktiv === false",
                    "style": {"opacity": "0.5"},
                }
            ]
        }

    def get_row_style_kontrollutslag(self):
        return {
            "styleConditions": [
                {
                    "condition": "params.data && params.data.utslag",
                    "style": {"backgroundColor": "#C3DCDC"},  # SSB mørk 2
                },
                {
                    "condition": "params.data.utslag === false",
                    "style": {"opacity": "0.5"},
                },
            ]
        }

    def _create_layout(self):
        layout = html.Div(
            [
                dcc.Store(id="refresh-manager", data={}),
                dcc.Store(
                    id="pending-regnskap-edit",
                    data=None,
                ),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    self.create_info_card(
                                        title="Organisasjonsnummer",
                                        component_id="nspek-info-card-organisasjonsnummer",
                                        var_type="text",
                                    ),
                                    width=2,
                                ),
                                dbc.Col(
                                    self.create_info_card(
                                        title="Årgang",
                                        component_id="nspek-info-card-aar",
                                        var_type="number",
                                    ),
                                    width=2,
                                ),
                                dbc.Col(
                                    self.create_dropdown_card(
                                        title="Versjon",
                                        component_id="nspek-versjon-dropdown",
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    self.create_dropdown_card(
                                        title="Sammenlign med versjon / årgang",
                                        component_id="nspek-versjon-dropdown-compare",
                                    ),
                                    width=4,
                                ),
                            ],
                            className="g-2 align-items-end",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "Oppdater data",
                                        id="btn-hent-data",
                                        className="ssb-btn primary-btn",
                                    ),
                                    width=2,
                                ),
                                dbc.Col(width=2),  # tom spacer
                                dbc.Col(
                                    dbc.Button(
                                        "Editeringslogg",
                                        id="btn-vis-editeringslogg",
                                        className="ssb-btn primary-btn",
                                    ),
                                    width=2,
                                ),
                            ],
                            className="g-2 mt-1 align-items-end",
                        ),
                        html.Div(
                            id="nspek-version-warning",
                            children=self.create_dialog(
                                variant="info", title="Tittel", message="Melding"
                            ),
                            style={"display": "none"},
                        ),
                        dcc.Store(id="nspek-version-warning-closed", data=False),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(
                                    dbc.ModalTitle(
                                        "Editeringslogg",
                                        id="modal-editeringslogg-title",
                                    )
                                ),
                                dbc.ModalBody(
                                    AgGrid(
                                        id="nspek-editeringslogg-grid",
                                        className="ag-theme-alpine ag-theme-ssb mb-2",
                                        columnDefs=[
                                            {"field": "tekst", "flex": 5},
                                            {"field": "felt", "flex": 3},
                                            {
                                                "field": "belop",
                                                "flex": 2,
                                                "type": "numericColumn",
                                                "valueFormatter": {
                                                    "function": "params.value == null ? '' : params.value.toLocaleString('no-NO')"
                                                },
                                                "cellStyle": {"textAlign": "right"},
                                            },
                                            {"field": "endret_av", "flex": 2},
                                            {"field": "endret_dato", "flex": 2},
                                            {"field": "operation_type", "hide": True},
                                            {"field": "process_type", "hide": True},
                                        ],
                                        rowData=[],
                                        dashGridOptions={
                                            "enableCellTextSelection": True,
                                            "ensureDomOrder": True,
                                            "enableRangeSelection": True,
                                        },
                                        getRowStyle=self.get_edit_log_row_style(),
                                        style={"height": "83vh", "width": "100%"},
                                    )
                                ),
                                dbc.ModalFooter(
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label(
                                                    [
                                                        html.Span(
                                                            "■",
                                                            style={
                                                                "color": "#c8e6c9",
                                                                "marginRight": "5px",
                                                            },
                                                        ),
                                                        html.Span("Satt inn nytt felt"),
                                                        html.Span(
                                                            "   ■",
                                                            style={
                                                                "color": "#ffe082",
                                                                "marginLeft": "15px",
                                                                "marginRight": "5px",
                                                            },
                                                        ),
                                                        html.Span("Editert felt"),
                                                        html.Span(
                                                            "   ■",
                                                            style={
                                                                "color": "#9fc5e8",
                                                                "marginLeft": "15px",
                                                                "marginRight": "5px",
                                                            },
                                                        ),
                                                        html.Span("Innsamling fra SKE"),
                                                    ],
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(width=True),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Lukk",
                                                    id="btn-lukk-editeringslogg",
                                                    className="ssb-btn primary-btn",
                                                ),
                                                width="auto",
                                            ),
                                        ],
                                        align="center",
                                        className="w-100",
                                    )
                                ),
                            ],
                            id="modal-editeringslogg",
                            is_open=False,
                            size="xl",
                            style={
                                "maxWidth": "100vw",
                                "width": "100vw",
                            },
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(
                                    dbc.ModalTitle(
                                        id="modal-generell-kommentar-historikk-title"
                                    )
                                ),
                                dbc.ModalBody(
                                    AgGrid(
                                        id="generell-kommentar-historikk-grid",
                                        className="ag-theme-alpine ag-theme-ssb mb-2",
                                        columnDefs=[
                                            {
                                                "field": "id",
                                                "headerName": "ID",
                                                "width": 80,
                                                "hide": True,
                                            },
                                            {
                                                "field": "kommentar",
                                                "headerName": "Kommentar",
                                                "flex": 1,
                                                "wrapText": True,
                                                "autoHeight": True,
                                                "cellStyle": {
                                                    "whiteSpace": "normal",
                                                    "lineHeight": "1.4",
                                                    "paddingTop": "6px",
                                                    "paddingBottom": "6px",
                                                },
                                            },
                                            {
                                                "field": "opprettet",
                                                "headerName": "Opprettet",
                                                "width": 160,
                                            },
                                            {
                                                "field": "opprettet_av",
                                                "headerName": "Opprettet av",
                                                "width": 120,
                                            },
                                            {
                                                "field": "aktiv",
                                                "headerName": "Aktiv",
                                                "width": 90,
                                                "editable": True,
                                            },
                                        ],
                                        rowData=[],
                                        dashGridOptions={
                                            "rowSelection": "single",
                                            "animateRows": True,
                                            "enableCellTextSelection": True,
                                        },
                                        style={"height": "83vh", "width": "100%"},
                                    )
                                ),
                                dbc.ModalFooter(
                                    dbc.Button(
                                        "Lukk",
                                        id="close-generell-historikk",
                                        className="ssb-btn primary-btn",
                                    )
                                ),
                            ],
                            id="modal-generell-kommentar-historikk",
                            is_open=False,
                            size="xl",
                            style={
                                "maxWidth": "100vw",
                                "width": "100vw",
                            },
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Advarsel")),
                                dbc.ModalBody(id="negative-value-modal-body"),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Avbryt",
                                            id="btn-cancel-negative-edit",
                                            color="secondary",
                                            className="ssb-btn",
                                        ),
                                        dbc.Button(
                                            "Bekreft",
                                            id="btn-confirm-negative-edit",
                                            color="danger",
                                            className="ssb-btn primary-btn",
                                        ),
                                    ]
                                ),
                            ],
                            id="modal-negative-value",
                            is_open=False,
                            centered=True,
                            backdrop="static",
                            className="negative-warning-modal",
                        ),
                    ],
                    style={"marginBottom": "10px"},
                ),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Organisasjonsnummer",
                                            component_id="bof-info-card-organisasjonsnummer",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Navn",
                                            component_id="bof-info-card-navn",
                                            var_type="text",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Orgform",
                                            component_id="bof-info-card-organisasjonsform",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Næringskode SN25",
                                            component_id="bof-info-card-naringskode25",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Næringskode SN07",
                                            component_id="bof-info-card-naringskode07",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Typekode",
                                            component_id="bof-info-card-typekode",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Kommune",
                                            component_id="bof-info-card-kommunekode",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Statuskode",
                                            component_id="bof-info-card-statuskode",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Sysselsatte",
                                            component_id="bof-info-card-sysselsatte",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Sektorkode",
                                            component_id="bof-info-card-sektorkode",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Undersektorkode",
                                            component_id="bof-info-card-undersektorkode",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                ],
                                className="bof-info-cards gy-2",
                            ),
                            title="BOF informasjon",
                            className="ssb-accordion",
                        ),
                        dbc.AccordionItem(
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Virksomhetstype",
                                            component_id="nspek-info-card-virksomhetstype",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Regeltype",
                                            component_id="nspek-info-card-regeltypeforaarsregnskap",
                                            var_type="text",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Type regnskapsplikt",
                                            component_id="nspek-info-card-regnskapspliktstype",
                                            var_type="text",
                                        ),
                                        width=3,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Skjønnslignet av SKE",
                                            component_id="nspek-info-card-skjoennslignet",
                                            var_type="text",
                                        ),
                                        width=3,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Startdato",
                                            component_id="nspek-info-card-start",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                    dbc.Col(
                                        self.create_info_card(
                                            title="Sluttdato",
                                            component_id="nspek-info-card-slutt",
                                            var_type="text",
                                        ),
                                        width=2,
                                    ),
                                ],
                                className="nspek-info-cards gy-2",
                            ),
                            title="NSPEK informasjon",
                            className="ssb-accordion",
                        ),
                        dbc.AccordionItem(
                            dbc.Accordion(
                                [
                                    dbc.AccordionItem(
                                        html.Div(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Historikk",
                                                                id="btn-generell-kommentar-historikk",
                                                                className="ssb-btn primary-btn",
                                                            ),
                                                            width="auto",
                                                        ),
                                                        dbc.Col(
                                                            self.create_info_card(
                                                                title="Endret av:",
                                                                component_id="nspek-info-card-endret-av",
                                                                var_type="text",
                                                            ),
                                                            width=2,
                                                        ),
                                                        dbc.Col(
                                                            self.create_info_card(
                                                                title="Dato:",
                                                                component_id="nspek-info-card-endret-dato",
                                                                var_type="text",
                                                            ),
                                                            width=2,
                                                        ),
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Lagre",
                                                                id="btn-save-kommentar",
                                                                className="ssb-btn primary-btn",
                                                            ),
                                                            width="auto",
                                                        ),
                                                    ],
                                                    className="g-2 mb-2 justify-content-end align-items-end",
                                                ),
                                                html.Div(
                                                    className="ssb-text-area",
                                                    children=[
                                                        dcc.Textarea(
                                                            id="kommentar-text",
                                                            placeholder="Skriv kommentar her...",
                                                            className="comment-textarea",
                                                            style={
                                                                "width": "100%",
                                                                "height": "200px",
                                                                "padding": "10px 12px",
                                                                "borderRadius": "6px",
                                                            },
                                                        ),
                                                    ],
                                                ),
                                            ]
                                        ),
                                        title="Generell kommentar",
                                    ),
                                    dbc.AccordionItem(
                                        html.Div(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            self.create_checkbox(
                                                                component_id="toggle-show-inactive",
                                                                label="Vis inaktive kommentarer",
                                                                value="show_inactive",
                                                                checked=False,
                                                            ),
                                                            width="auto",
                                                        ),
                                                    ],
                                                    align="center",
                                                    className="g-2 mb-2 justify-content-end align-items-end",
                                                ),
                                                AgGrid(
                                                    id="nspek-feltkommentar-grid",
                                                    className="ag-theme-alpine ag-theme-ssb mb-2",
                                                    columnDefs=[
                                                        {"field": "id", "hide": True},
                                                        {
                                                            "field": "felt",
                                                            "headerName": "Felt",
                                                            "width": 120,
                                                        },
                                                        {
                                                            "field": "kommentar",
                                                            "flex": 1,
                                                        },
                                                        {
                                                            "field": "opprettet_av",
                                                            "width": 120,
                                                        },
                                                        {
                                                            "field": "opprettet",
                                                            "width": 150,
                                                        },
                                                        {
                                                            "field": "aktiv",
                                                            "width": 70,
                                                            "editable": True,
                                                        },
                                                    ],
                                                    rowData=[],
                                                    dashGridOptions={
                                                        "rowSelection": "single",
                                                        "animateRows": True,
                                                    },
                                                    getRowStyle=self.get_row_style_active_comment(),
                                                    style={"height": "300px"},
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            self.create_info_card(
                                                                title="Felt",
                                                                component_id="input-felt",
                                                                var_type="number",
                                                            ),
                                                            width=1,
                                                        ),
                                                        dbc.Col(
                                                            self.create_info_card(
                                                                title="Legg inn ny feltkommentar",
                                                                component_id="input-felt-kommentar",
                                                                var_type="text",
                                                            ),
                                                            width=True,
                                                        ),
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Lagre",
                                                                id="btn-save-feltkommentar",
                                                                className="ssb-btn primary-btn",
                                                            ),
                                                            width="auto",
                                                        ),
                                                    ],
                                                    className="g-2 mb-2 justify-content-end align-items-end",
                                                ),
                                            ]
                                        ),
                                        title="Feltkommentar",
                                    ),
                                ],
                                always_open=True,
                                start_collapsed=False,
                                className="ssb-nested-accordion",
                            ),
                            title="Kommentarer",
                            className="ssb-accordion",
                        ),
                    ],
                    always_open=True,
                    start_collapsed=True,
                    className="mb-2",
                ),
                dcc.Tabs(
                    id="nspek-tabs",
                    children=[
                        dcc.Tab(
                            label="Resultatregnskap",
                            value="resultat",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            self.create_checkbox(
                                                component_id="toggle-show-blank-values-resultat",
                                                label="Vis blanke verdier",
                                                value="show_blank",
                                                checked=True,
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            self.create_checkbox(
                                                component_id="toggle-show-petroleum-fields-resultat",
                                                label="Vis petroleumsposter",
                                                value="show_petroleum",
                                                checked=False,
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                AgGrid(
                                    id="nspek-resultatdata-grid",
                                    className="ag-theme-alpine ag-theme-ssb mb-2",
                                    # getRowId="params.data.id",   ### Bør vurdere å legge til dette på sikt.
                                    defaultColDef={"resizable": True},
                                    rowData=[],
                                    columnDefs=[],
                                    dashGridOptions={
                                        "rowSelection": "single",
                                        "enableCellTextSelection": True,
                                        "enableBrowserTooltips": True,
                                    },
                                    # getRowStyle=self.get_row_style_with_comments(),
                                    getRowStyle=self.get_row_style_ui_sums(),
                                    style={
                                        "height": "70vh",
                                        "width": "100%",
                                    },
                                ),
                            ],
                        ),
                        dcc.Tab(
                            label="Balanseregnskap",
                            value="balanse",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            self.create_checkbox(
                                                component_id="toggle-show-blank-values-balanse",
                                                label="Vis blanke verdier",
                                                value="show_blank",
                                                checked=True,
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            self.create_checkbox(
                                                component_id="toggle-show-petroleum-fields-balanse",
                                                label="Vis petroleumsposter",
                                                value="show_petroleum",
                                                checked=False,
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                AgGrid(
                                    id="nspek-balansedata-grid",
                                    className="ag-theme-alpine ag-theme-ssb mb-2",
                                    # getRowId="params.data.id",   ### Bør vurdere å legge til dette på sikt.
                                    defaultColDef={"resizable": True},
                                    rowData=[],
                                    columnDefs=[],
                                    dashGridOptions={
                                        "rowSelection": "single",
                                        "enableCellTextSelection": True,
                                        "enableBrowserTooltips": True,
                                    },
                                    # getRowStyle=self.get_row_style_with_comments(),
                                    getRowStyle=self.get_row_style_ui_sums(),
                                    style={
                                        "height": "70vh",
                                        "width": "100%",
                                    },
                                ),
                            ],
                        ),
                        dcc.Tab(
                            id="kontrollutslag-tab",
                            label="Kontrollutslag",
                            value="kontrollutslag",
                            children=[
                                AgGrid(
                                    id="nspek-kontrollutslag-grid",
                                    className="ag-theme-alpine ag-theme-ssb mb-2",
                                    defaultColDef={
                                        "resizable": True,
                                        "sortable": True,
                                    },
                                    columnDefs=[
                                        {
                                            "field": "aar",
                                            "headerName": "År",
                                            "hide": True,
                                        },
                                        {
                                            "field": "kontrollid",
                                            "headerName": "Kontroll",
                                            "flex": 1,
                                            "minWidth": 250,
                                        },
                                        {
                                            "field": "tema",
                                            "headerName": "Tema",
                                            "flex": 1,
                                            "minWidth": 120,
                                        },
                                        {
                                            "field": "skildring",
                                            "headerName": "Beskrivelse",
                                            "flex": 4,
                                            "minWidth": 200,
                                        },
                                        {
                                            "field": "ident",
                                            "headerName": "Ident",
                                            "hide": True,
                                        },
                                        {
                                            "field": "utslag",
                                            "headerName": "Utslag",
                                            "flex": 1,
                                            "minWidth": 100,
                                        },
                                        {
                                            "field": "verdi",
                                            "headerName": "Verdi",
                                            "flex": 1,
                                            "minWidth": 100,
                                        },
                                    ],
                                    dashGridOptions={
                                        "rowSelection": "single",
                                        "animateRows": True,
                                    },
                                    #getRowStyle=self.get_row_style_kontrollutslag(),
                                    style={
                                        "height": "50vh",
                                        "width": "100%",
                                        #'display': 'none',
                                    },
                                ),
                            ],
                        ),
                    ],
                    className="ssb-tabs mb-3",
                ),
            ],
            style={
                "width": "100%",
                "minWidth": "0",
            },
        )

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Naeringsspesifikasjon module."""

        @callback(
            Output(
                component_id="bof-info-card-organisasjonsnummer",
                component_property="value",
            ),
            Output(component_id="bof-info-card-navn", component_property="value"),
            Output(
                component_id="bof-info-card-organisasjonsform",
                component_property="value",
            ),
            Output(
                component_id="bof-info-card-naringskode25", component_property="value"
            ),
            Output(
                component_id="bof-info-card-naringskode07", component_property="value"
            ),
            Output(component_id="bof-info-card-typekode", component_property="value"),
            Output(
                component_id="bof-info-card-kommunekode", component_property="value"
            ),
            Output(component_id="bof-info-card-statuskode", component_property="value"),
            Output(
                component_id="bof-info-card-sysselsatte", component_property="value"
            ),
            Output(component_id="bof-info-card-sektorkode", component_property="value"),
            Output(component_id="bof-info-card-undersektorkode", component_property="value"),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
        )
        def create_info_cards_bof(orgnr_foretak: str, aar: str) -> tuple[str, str, str, str, str]:
            """Returns a tuple of strings with the values for info cards for the top of the bof accordion.
            These cards will hold bof information for the foretak.
            """

            if not orgnr_foretak or not aar:
                raise PreventUpdate

            df = get_bofinfo(ident=orgnr_foretak, aar=aar)

            if df.empty:
                return ("", "", "", "", "", "", "", "", "", "", "")

            orgnr = get_value(df["orgnr"])
            navn = get_value(df["navn"])
            org_form = get_value(df["org_form"])
            sn2025_1 = get_value(df["sn2025_1"])
            sn07_1 = get_value(df["sn07_1"])
            sf_type = get_value(df["sf_type"])
            f_kommunenr = get_value(df["f_kommunenr"])
            statuskode = get_value(df["statuskode"])
            sysselsatte = get_value(df["sysselsatte"])
            sektor_2014 = get_value(df["sektor_2014"])
            undersektor_2014 = get_value(df["undersektor_2014"])

            return (
                orgnr,
                navn,
                org_form,
                sn2025_1,
                sn07_1,
                sf_type,
                f_kommunenr,
                statuskode,
                sysselsatte,
                sektor_2014,
                undersektor_2014,
            )

        @callback(
            Output(
                component_id="nspek-info-card-virksomhetstype",
                component_property="value",
            ),
            Output(
                component_id="nspek-info-card-regeltypeforaarsregnskap",
                component_property="value",
            ),
            Output(
                component_id="nspek-info-card-regnskapspliktstype",
                component_property="value",
            ),
            Output(component_id="nspek-info-card-start", component_property="value"),
            Output(component_id="nspek-info-card-slutt", component_property="value"),
            Input("var-aar", "value"),
            Input("var-ident", "value"),
            Input("nspek-versjon-dropdown", "value"),
        )
        def create_info_cards_virksomhet(
            aar: str, orgnr_foretak: str, sekvensnummer: int
        ) -> tuple[str, str, str, str, str]:
            """Returns a tuple of strings with the values for info cards for the top of the nspek module.
            These cards will hold virksomhetsinfo for the foretak.
            """
            if not aar or not orgnr_foretak or not sekvensnummer:
                return "", "", "", "", ""

            if not has_data(self.conn, orgnr_foretak, aar):
                return "", "", "", "", ""

            df = get_virksomhetsinfo(
                conn=self.conn,
                variables_to_fetch=virksomhetsinfo_variabler,
                ident=orgnr_foretak,
                aar=aar,
                sekvensnummer=sekvensnummer,
            )

            if df.empty:
                return "", "", "", "", ""

            virksomhetstype = get_value(df[df["felt"] == "virksomhetstype"]["char_verdi"])
            regeltype = get_value(df[df["felt"] == "regeltypeForAarsregnskap"]["char_verdi"])
            regnskapspliktstype = get_value(df[df["felt"] == "regnskapspliktstype"]["char_verdi"])
            start = get_value(df[df["felt"] == "start"]["char_verdi"])
            slutt = get_value(df[df["felt"] == "slutt"]["char_verdi"])

            return (virksomhetstype, regeltype, regnskapspliktstype, start, slutt)

        @callback(
            Output(
                component_id="nspek-info-card-skjoennslignet",
                component_property="value",
            ),
            Input("var-aar", "value"),
            Input("var-ident", "value"),
            Input("nspek-versjon-dropdown", "value"),
        )
        def create_info_cards_skjoennslignet(
            aar: str, orgnr_foretak: str, sekvensnummer: int
        ) -> str:
            """Returns a with the values for info card skjoennslignet inn the nspek module."""
            if not aar or not orgnr_foretak or not sekvensnummer:
                return ""

            if not has_data(self.conn, orgnr_foretak, aar):
                return ""

            df = get_skjoennslignet(
                conn=self.conn,
                ident=orgnr_foretak,
                aar=aar,
                sekvensnummer=sekvensnummer,
            )

            if df.empty:
                return "Nei"

            skjoennslignet = "Ja"

            return skjoennslignet

        @callback(
            Output("nspek-balansedata-grid", "rowData"),
            Output("nspek-balansedata-grid", "columnDefs"),
            Input("btn-hent-data", "n_clicks"),
            Input("refresh-manager", "data"),
            Input("var-aar", "value"),
            Input("var-ident", "value"),
            Input("toggle-show-blank-values-balanse", "value"),
            Input("nspek-versjon-dropdown", "value"),
            Input("nspek-versjon-dropdown-compare", "value"),
            Input("toggle-show-petroleum-fields-balanse", "value"),
        )
        def show_balanseregnskap(
            n_clicks,
            refresh_data,
            aar: str,
            orgnr_foretak: str,
            toggle_blank: list[str],
            sekvensnummer: int,
            sekvens_compare: int,
            toggle_petroleum: list[str],
        ):

            # if refresh_data and "balanse" not in refresh_data:
            #     raise PreventUpdate

            if not aar or not orgnr_foretak:
                raise PreventUpdate

            if refresh_data and refresh_data.get("status") == "invalid_search":
                return [], []

            post_descriptions = post_description_data("balanseregnskap")
            ident_data = fetch_data_by_orgnr(
                self.conn, "balanseregnskap", orgnr_foretak, aar, sekvensnummer
            )

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df_main = post_descriptions.merge(ident_data, how="left", on="felt")
            df_main["sekvensnummer"] = sekvensnummer
            df_main = df_main.rename(
                columns={"tekst": "beskrivelse", "felt": "post", "belop": "verdi"}
            )

            if sekvens_compare:
                df_compare = fetch_data_by_orgnr(
                    self.conn, "balanseregnskap", orgnr_foretak, aar, sekvens_compare
                )
                df_compare = df_compare.rename(
                    columns={
                        "tekst": "beskrivelse",
                        "felt": "post",
                        "belop": "verdi_compare",
                    }
                )

                df = df_main.merge(df_compare, on="post", how="left")
                verdi = df["verdi"]
                verdi_compare = df["verdi_compare"]
                verdi_calc = verdi.fillna(0)
                verdi_compare_calc = verdi_compare.fillna(0)
                df["diff"] = (verdi_calc - verdi_compare_calc).where(
                    ~(verdi.isna() & verdi_compare.isna())
                )

            else:
                df = df_main

            df = add_ui_sums(df, BALANSE_STRUCTURE)
            df = apply_blank_filter(df, toggle_blank)
            df = apply_petroleum_filter(df, orgnr_foretak, toggle_petroleum)

            comments = get_latest_field_comments(self.conn, orgnr_foretak)
            df["comment_icon"] = df["post"].map(lambda x: "💬" if x in comments else "")
            df["comment_text"] = df["post"].map(
                lambda x: comments.get(x, {}).get("kommentar", "")
            )

            row_data = df.to_dict("records")
            column_defs = build_column_defs(sekvens_compare)

            return row_data, column_defs

        @callback(
            Output("nspek-resultatdata-grid", "rowData"),
            Output("nspek-resultatdata-grid", "columnDefs"),
            Input("btn-hent-data", "n_clicks"),
            Input("refresh-manager", "data"),
            Input("var-aar", "value"),
            Input("var-ident", "value"),
            Input("toggle-show-blank-values-resultat", "value"),
            Input("nspek-versjon-dropdown", "value"),
            Input("nspek-versjon-dropdown-compare", "value"),
            Input("toggle-show-petroleum-fields-resultat", "value"),
        )
        def show_resultatregnskap(
            n_clicks,
            refresh_data,
            aar: str,
            orgnr_foretak: str,
            toggle_blank: list[str],
            sekvensnummer: int,
            sekvens_compare: int,
            toggle_petroleum: list[str],
        ):

            # if refresh_data and "resultat" not in refresh_data:
            #     raise PreventUpdate

            if not aar or not orgnr_foretak:
                raise PreventUpdate

            if refresh_data and refresh_data.get("status") == "invalid_search":
                return [], []

            post_descriptions = post_description_data("resultatregnskap")
            ident_data = fetch_data_by_orgnr(
                self.conn, "resultatregnskap", orgnr_foretak, aar, sekvensnummer
            )

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df_main = post_descriptions.merge(ident_data, how="left", on="felt")
            df_main["sekvensnummer"] = sekvensnummer
            df_main = df_main.rename(
                columns={"tekst": "beskrivelse", "felt": "post", "belop": "verdi"}
            )

            if sekvens_compare:
                df_compare = fetch_data_by_orgnr(
                    self.conn, "resultatregnskap", orgnr_foretak, aar, sekvens_compare
                )
                df_compare = df_compare.rename(
                    columns={
                        "tekst": "beskrivelse",
                        "felt": "post",
                        "belop": "verdi_compare",
                    }
                )

                df = df_main.merge(df_compare, on="post", how="left")
                verdi = df["verdi"]
                verdi_compare = df["verdi_compare"]
                verdi_calc = verdi.fillna(0)
                verdi_compare_calc = verdi_compare.fillna(0)
                df["diff"] = (verdi_calc - verdi_compare_calc).where(
                    ~(verdi.isna() & verdi_compare.isna())
                )

            else:
                df = df_main

            df = add_ui_sums(df, RESULTAT_STRUCTURE)
            df = apply_blank_filter(df, toggle_blank)
            df = apply_petroleum_filter(df, orgnr_foretak, toggle_petroleum)

            comments = get_latest_field_comments(self.conn, orgnr_foretak)
            df["comment_icon"] = df["post"].map(lambda x: "💬" if x in comments else "")
            df["comment_text"] = df["post"].map(
                lambda x: comments.get(x, {}).get("kommentar", "")
            )

            row_data = df.to_dict("records")
            column_defs = build_column_defs(sekvens_compare)

            return row_data, column_defs

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("refresh-manager", "data", allow_duplicate=True),
            Output("modal-negative-value", "is_open", allow_duplicate=True),
            Output("pending-regnskap-edit", "data", allow_duplicate=True),
            Output("negative-value-modal-body", "children"),
            Input("nspek-balansedata-grid", "cellValueChanged"),
            State("alert_store", "data"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def edit_balanseregnskap(edited, alert_store, refresh_data):
            return handle_regnskap_edit(
                edited,
                alert_store,
                refresh_data,
                regnskapstype="balanseregnskap",
                refresh_key="balanse",
            )

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("refresh-manager", "data", allow_duplicate=True),
            Output("modal-negative-value", "is_open", allow_duplicate=True),
            Output("pending-regnskap-edit", "data", allow_duplicate=True),
            Output("negative-value-modal-body", "children", allow_duplicate=True),
            Input("nspek-resultatdata-grid", "cellValueChanged"),
            State("alert_store", "data"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def edit_resultatregnskap(edited, alert_store, refresh_data):
            return handle_regnskap_edit(
                edited,
                alert_store,
                refresh_data,
                regnskapstype="resultatregnskap",
                refresh_key="resultat",
            )

        @callback(
            Output("modal-negative-value", "is_open", allow_duplicate=True),
            Output("pending-regnskap-edit", "data", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Output("refresh-manager", "data", allow_duplicate=True),
            Input("btn-confirm-negative-edit", "n_clicks"),
            State("pending-regnskap-edit", "data"),
            State("alert_store", "data"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def confirm_negative(_, pending, alert_store, refresh_data):
            if not pending:
                raise PreventUpdate

            try:
                with get_nspek_connection() as conn:

                    user = os.getenv("DAPLA_USER", "")[:3]

                    conn.raw_sql(f"SET nspek_app.user_id = '{user}'")
                    conn.raw_sql("SET nspek_app.process_type = 'editering'")

                    save_regnskap_value(
                        conn,
                        pending["regnskapstype"],
                        pending["sekvensnummer"],
                        pending["post"],
                        pending["value"],
                    )

                alert_store = [
                    create_alert(
                        f"{pending['post']} oppdatert til {pending['value']}",
                        "success",
                        ephemeral=True,
                    ),
                    *alert_store,
                ]

            except Exception as e:
                logger.error(e, exc_info=True)

                alert_store = [
                    create_alert(
                        f"Feil: {str(e)[:80]}",
                        "danger",
                        ephemeral=True,
                    ),
                    *alert_store,
                ]

            refresh_data = trigger_refresh(refresh_data, pending["refresh_key"])

            return False, None, alert_store, refresh_data

        @callback(
            Output("modal-negative-value", "is_open", allow_duplicate=True),
            Output("pending-regnskap-edit", "data", allow_duplicate=True),
            Input("btn-cancel-negative-edit", "n_clicks"),
            prevent_initial_call=True,
        )
        def cancel_negative(_):
            """Cancels negative value edit.

            Example use: modal cancel button.
            """
            return False, None

        @callback(
            Output("nspek-info-card-organisasjonsnummer", "value"),
            Output("nspek-info-card-aar", "value"),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
        )
        def sync_ui_fields(orgnr, aar):
            if not orgnr or not aar:
                raise PreventUpdate

            return orgnr, aar

        @callback(
            self.variableselector.get_output_object("ident"),
            self.variableselector.get_output_object("aar"),
            self.variableselector.get_output_object("foretak"),
            Output("refresh-manager", "data", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input("btn-hent-data", "n_clicks"),
            Input("nspek-info-card-organisasjonsnummer", "n_submit"),
            Input("nspek-info-card-aar", "n_submit"),
            State("nspek-info-card-organisasjonsnummer", "value"),
            State("nspek-info-card-aar", "value"),
            State("refresh-manager", "data"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_variableselector(
            n_clicks, orgnr_submit, aar_submit, orgnr, aar, refresh_data, alert_store
        ):

            alert_store = alert_store or []

            orgnr = clean_whitespace(orgnr)

            ok_org, msg_org = validate_orgnr(orgnr)
            if not ok_org:
                refresh_data = trigger_refresh(refresh_data, "invalid_search")
                return (
                    no_update,
                    no_update,
                    no_update,
                    refresh_data,
                    [
                        create_alert(msg_org, "danger", ephemeral=True),
                        *alert_store,
                    ],
                )

            ok_aar, msg_aar = validate_aar(aar)
            if not ok_aar:
                refresh_data = trigger_refresh(refresh_data, "invalid_search")
                return (
                    no_update,
                    no_update,
                    no_update,
                    refresh_data,
                    [
                        create_alert(msg_aar, "danger", ephemeral=True),
                        *alert_store,
                    ],
                )

            if not orgnr_exists_in_bof(orgnr):
                refresh_data = trigger_refresh(refresh_data, "invalid_search")
                return (
                    no_update,
                    no_update,
                    no_update,
                    refresh_data,
                    [
                        create_alert(
                            f"Organisasjonsnummer {orgnr} finnes ikke i BOF",
                            "warning",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ],
                )

            if not has_data(self.conn, orgnr, aar):
                refresh_data = trigger_refresh(refresh_data, "invalid_search")
                return (
                    no_update,
                    no_update,
                    no_update,
                    refresh_data,
                    [
                        create_alert(
                            f"Ingen data funnet for orgnr {orgnr} og årgang {aar} i NSPEK",
                            "warning",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ],
                )

            refresh_data = trigger_refresh(refresh_data, "valid_search")

            return orgnr, aar, orgnr, refresh_data, alert_store

        @callback(
            Output("nspek-versjon-dropdown", "options"),
            Output("nspek-versjon-dropdown", "value"),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
        )
        def load_versions(orgnr, aar):
            if not orgnr or not aar:
                raise PreventUpdate

            if not has_data(self.conn, orgnr, aar):
                return [], None

            df = get_versions(self.conn, orgnr, aar)

            if df.empty:
                return [], None

            sekvens_liste = df["sekvensnummer"].tolist()

            t = self.conn.table("v_update_counts", database="nspek_core")

            df_updates = (
                t.filter(_.sekvensnummer.isin(sekvens_liste))
                .select(_.sekvensnummer, _.antall_endringer)
                .execute()
            )

            df = df.merge(df_updates, on="sekvensnummer", how="left")
            df["antall_endringer"] = df["antall_endringer"].fillna(0)
            df["label"] = df.apply(
                lambda row: row["label"]
                + (" (editert)" if row["antall_endringer"] > 0 else ""),
                axis=1,
            )

            options = [
                {"label": row["label"], "value": row["sekvensnummer"]}
                for _, row in df.iterrows()
            ]

            df_with_changes = df[df["antall_endringer"] > 0]

            if not df_with_changes.empty:
                default_value = df_with_changes.sort_values(
                    "dato_mottatt", ascending=False
                ).iloc[0]["sekvensnummer"]
            else:
                default_value = df.sort_values(
                    by=["dato_mottatt", "sekvensnummer"], ascending=[False, False]
                ).iloc[0]["sekvensnummer"]

            return options, default_value

        @callback(
            Output("nspek-version-warning", "style"),
            Output("nspek-version-warning", "children"),
            Output("nspek-version-warning-closed", "data"),
            Input("nspek-versjon-dropdown", "value"),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
            Input("close-version-warning", "n_clicks"),
            State("nspek-version-warning-closed", "data"),
        )
        def toggle_version_warning(selected_sekvens, orgnr, aar, close_clicks, closed):
            if close_clicks:
                return {"display": "none"}, "", True

            if not selected_sekvens or not orgnr or not aar:
                return {"display": "none"}, "", False

            if not has_data(self.conn, orgnr, aar):
                return {"display": "none"}, "", False

            df = get_versions(self.conn, orgnr, aar)

            if df.empty:
                return {"display": "none"}, "", False

            latest_sekvens = df.sort_values(
                by=["dato_mottatt", "sekvensnummer"], ascending=[False, False]
            ).iloc[0]["sekvensnummer"]

            if selected_sekvens != latest_sekvens:
                return (
                    {"display": "flex"},
                    self.create_dialog(
                        variant="info",
                        title="Ikke siste versjon",
                        message="Du ser nå ikke på siste innsendte versjon i NSPEK. Hvis du vil se site versjon må du velge den i listen over.",
                    ),
                    False,
                )

            return {"display": "none"}, "", False

        @callback(
            Output("nspek-versjon-dropdown-compare", "options"),
            Input("nspek-versjon-dropdown", "options"),
        )
        def sync_compare_options(options):
            return options

        @callback(
            Output("modal-editeringslogg", "is_open"),
            Input("btn-vis-editeringslogg", "n_clicks"),
            Input("btn-lukk-editeringslogg", "n_clicks"),
            State("modal-editeringslogg", "is_open"),
        )
        def toggle_modal_editeringslogg(open_click, close_click, is_open):
            if open_click or close_click:
                return not is_open
            return is_open

        @callback(
            Output("btn-vis-editeringslogg", "disabled"),
            Input("nspek-tabs", "value"),
        )
        def toggle_editeringslogg_button(active_tab):
            return active_tab not in ["resultat", "balanse"]

        @callback(
            Output("nspek-editeringslogg-grid", "rowData"),
            Output("modal-editeringslogg-title", "children"),
            Input("btn-vis-editeringslogg", "n_clicks"),
            State("nspek-versjon-dropdown", "value"),
            State("nspek-tabs", "value"),
            prevent_initial_call=True,
        )
        def load_logg(n_clicks, sekvensnummer, active_tab):
            if not sekvensnummer:
                raise PreventUpdate

            if active_tab == "balanse":
                table = "balanseregnskap.tema_balanse_hist"
                regnskapstype = "balanseregnskap"
                title = "Editeringslogg - Balanseregnskap"
            elif active_tab == "resultat":
                table = "resultatregnskap.tema_resultat_hist"
                regnskapstype = "resultatregnskap"
                title = "Editeringslogg - Resultatregnskap"

            query = f"""
                SELECT *
                FROM {table}
                WHERE sekvensnummer = {sekvensnummer}
                ORDER BY felt, hist_id DESC
            """
            # WHERE sekvensnummer = {sekvensnummer} and process_type = 'editering'   ### Må se an brukerbehov hvilken som skal brukes.
            with get_nspek_connection() as conn:
                cursor = conn.raw_sql(query)

                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

                df = pd.DataFrame(rows, columns=columns)

                post_descriptions = post_description_data(regnskapstype)

                post_descriptions["felt"] = post_descriptions["felt"].astype(str)
                df["felt"] = df["felt"].astype(str)

                df = post_descriptions.merge(df, how="right", on="felt")

                df["endret_dato"] = pd.to_datetime(df["endret_dato"]).dt.strftime(
                    "%Y-%m-%d %H:%M"
                )

            return df.to_dict("records"), title

        @callback(
            Output("kommentar-text", "value"),
            Output("nspek-info-card-endret-av", "value"),
            Output("nspek-info-card-endret-dato", "value"),
            Input("var-ident", "value"),
            Input("alert_store", "data"),
        )
        def load_kommentar(orgnr, alert_store):
            if not orgnr:
                raise PreventUpdate

            query = f"""
                SELECT
                    kommentar,
                    opprettet_av,
                    opprettet
                FROM nspek_core.kommentarfelt_test_2
                WHERE orgnr = '{orgnr}'
                AND nivaa = 'generell'
                AND aktiv = true
                ORDER BY opprettet DESC
                LIMIT 1
            """

            with get_nspek_connection() as conn:
                cursor = conn.raw_sql(query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            if df.empty:
                return "", "", ""

            row = df.iloc[0]

            kommentar = row["kommentar"] or ""
            endret_av = row["opprettet_av"] or ""
            endret_dato = (
                pd.to_datetime(row["opprettet"]).strftime("%Y-%m-%d %H:%M")
                if pd.notna(row["opprettet"])
                else ""
            )

            return kommentar, endret_av, endret_dato

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input("btn-save-kommentar", "n_clicks"),
            State("var-ident", "value"),
            State("kommentar-text", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def save_kommentar(n_clicks, orgnr, kommentar, alert_store):

            if not orgnr:
                raise PreventUpdate

            kommentar = kommentar or ""

            query_deactivate = f"""
                UPDATE nspek_core.kommentarfelt_test_2
                SET aktiv = false
                WHERE orgnr = '{orgnr}'
                AND nivaa = 'generell'
                AND aktiv = true
            """

            query_insert = f"""
                INSERT INTO nspek_core.kommentarfelt_test_2 (
                    orgnr,
                    nivaa,
                    kommentar,
                    versjon,
                    aktiv,
                    opprettet,
                    opprettet_av
                )
                VALUES (
                    '{orgnr}',
                    'generell',
                    '{kommentar.replace("'", "''")}',
                    1,
                    true,
                    NOW(),
                    current_setting('nspek_app.user_id')
                )
            """

            try:
                with get_nspek_connection() as conn:
                    dapla_user = os.getenv("DAPLA_USER", None)[:3]
                    PROCESS_TYPE = "editering"
                    conn.raw_sql(f"SET nspek_app.user_id = {dapla_user}")
                    conn.raw_sql(f"SET nspek_app.process_type = {PROCESS_TYPE}")
                    conn.raw_sql(query_deactivate)
                    conn.raw_sql(query_insert)

                alert_store = [
                    create_alert("Kommentar lagret", "success", ephemeral=True),
                    *alert_store,
                ]

            except Exception as e:
                alert_store = [
                    create_alert(
                        f"Feil ved lagring: {str(e)[:100]}",
                        "danger",
                        ephemeral=True,
                    ),
                    *alert_store,
                ]

            return alert_store

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("input-felt", "value"),
            Output("input-felt-kommentar", "value"),
            Output("refresh-manager", "data", allow_duplicate=True),
            Input("btn-save-feltkommentar", "n_clicks"),
            State("var-ident", "value"),
            State("input-felt", "value"),
            State("input-felt-kommentar", "value"),
            State("alert_store", "data"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def save_feltkommentar(
            n_clicks, orgnr, felt, kommentar, alert_store, refresh_data
        ):

            if not orgnr:
                raise PreventUpdate

            if felt is None:
                return (
                    [
                        create_alert("Felt må fylles ut", "danger", ephemeral=True),
                        *alert_store,
                    ],
                    None,
                    "",
                )

            try:
                felt = int(felt)
            except ValueError:
                return (
                    [
                        create_alert("Felt må være tall", "danger", ephemeral=True),
                        *alert_store,
                    ],
                    None,
                    "",
                )

            kommentar = kommentar or ""

            query_deactivate = f"""
                UPDATE nspek_core.kommentarfelt_test_2
                SET aktiv = false
                WHERE orgnr = '{orgnr}'
                AND nivaa = 'variabel'
                AND variabel = '{felt}'
                AND aktiv = true
            """

            query_insert = f"""
                INSERT INTO nspek_core.kommentarfelt_test_2 (
                    orgnr,
                    nivaa,
                    variabel,
                    kommentar,
                    versjon,
                    aktiv,
                    opprettet,
                    opprettet_av
                )
                VALUES (
                    '{orgnr}',
                    'variabel',
                    '{felt}',
                    '{kommentar.replace("'", "''")}',
                    1,
                    true,
                    NOW(),
                    ''current_setting('nspek_app.user_id')''
                )
            """

            try:
                with get_nspek_connection() as conn:
                    dapla_user = os.getenv("DAPLA_USER", None)[:3]
                    PROCESS_TYPE = "editering"
                    conn.raw_sql(f"SET nspek_app.user_id = {dapla_user}")
                    conn.raw_sql(f"SET nspek_app.process_type = {PROCESS_TYPE}")
                    conn.raw_sql(query_deactivate)
                    conn.raw_sql(query_insert)

                alert_store = [
                    create_alert("Feltkommentar lagret", "success", ephemeral=True),
                    *alert_store,
                ]

            except Exception as e:
                alert_store = [
                    create_alert(f"Feil: {str(e)[:100]}", "danger", ephemeral=True),
                    *alert_store,
                ]

            refresh_data = trigger_refresh(refresh_data, "comments")

            return alert_store, None, "", refresh_data

        @callback(
            Output("nspek-feltkommentar-grid", "rowData"),
            Input("var-ident", "value"),
            Input("btn-save-feltkommentar", "n_clicks"),
            Input("toggle-show-inactive", "value"),
        )
        def load_feltkommentarer(orgnr, _, toggle_inactive):

            if not orgnr:
                raise PreventUpdate

            query = f"""
                SELECT
                    id,
                    variabel AS felt,
                    kommentar,
                    opprettet_av,
                    opprettet,
                    aktiv
                FROM nspek_core.kommentarfelt_test_2
                WHERE orgnr = '{orgnr}'
                AND nivaa = 'variabel'
                ORDER BY opprettet DESC
            """

            with get_nspek_connection() as conn:
                cursor = conn.raw_sql(query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            if df.empty:
                return []

            if "show_inactive" not in toggle_inactive:
                df = df[df["aktiv"] == True]

            df["opprettet"] = pd.to_datetime(df["opprettet"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )

            return df.to_dict("records")

        @callback(
            Output("nspek-feltkommentar-grid", "rowData", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Output("refresh-manager", "data", allow_duplicate=True),
            Input("nspek-feltkommentar-grid", "cellValueChanged"),
            State("var-ident", "value"),
            State("alert_store", "data"),
            State("toggle-show-inactive", "value"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def toggle_feltkommentar_aktiv(
            edited, orgnr, alert_store, toggle_inactive, refresh_data
        ):

            logger.debug(f"edited: {edited}\norgnr: {orgnr}\n")

            refresh_data = refresh_data or {}

            if not edited or not orgnr:
                raise PreventUpdate

            try:
                row = edited[0]["data"]
                kommentar_id = row["id"]
                felt = row["felt"]
                new_value = row["aktiv"]

                if new_value is True:

                    query_deactivate_others = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = false
                        WHERE orgnr = '{orgnr}'
                        AND nivaa = 'variabel'
                        AND variabel = '{felt}'
                    """

                    query_activate = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = true
                        WHERE id = {kommentar_id}
                    """

                    with get_nspek_connection() as conn:
                        conn.raw_sql(query_deactivate_others)
                        conn.raw_sql(query_activate)

                    msg = f"Aktivert kommentar for felt {felt}"

                else:

                    query_deactivate = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = false
                        WHERE id = {kommentar_id}
                    """

                    with get_nspek_connection() as conn:
                        conn.raw_sql(query_deactivate)

                    msg = f"Deaktivert kommentar for felt {felt}"

                alert_store = [
                    create_alert(msg, "success", ephemeral=True),
                    *(alert_store or []),
                ]

                refresh_data = trigger_refresh(refresh_data, "comments")

                return (
                    load_feltkommentarer(orgnr, None, toggle_inactive),
                    alert_store,
                    refresh_data,
                )

            except Exception as e:

                logger.error(e, exc_info=True)

                alert_store = [
                    create_alert(
                        f"Oppdatering feilet: {str(e)[:80]}",
                        "danger",
                        ephemeral=True,
                    ),
                    *(alert_store or []),
                ]

                return (
                    load_feltkommentarer(orgnr, None, toggle_inactive),
                    alert_store,
                    refresh_data,
                )

        @callback(
            Output("toggle-show-petroleum-fields-balanse", "value"),
            Output("toggle-show-petroleum-fields-resultat", "value"),
            Input("var-ident", "value"),
        )
        def set_default_petroleum_toggle(orgnr):
            if not orgnr:
                return [], []

            if str(orgnr) in PETROLEUM_ORGNR:
                return ["show_petroleum"], ["show_petroleum"]

            return [], []

        @callback(
            Output("modal-generell-kommentar-historikk", "is_open"),
            Input("btn-generell-kommentar-historikk", "n_clicks"),
            Input("close-generell-historikk", "n_clicks"),
            State("modal-generell-kommentar-historikk", "is_open"),
        )
        def toggle_modal_kommentar_historikk(open_click, close_click, is_open):
            if open_click or close_click:
                return not is_open
            return is_open

        @callback(
            Output("generell-kommentar-historikk-grid", "rowData"),
            Output("modal-generell-kommentar-historikk-title", "children"),
            Input("btn-generell-kommentar-historikk", "n_clicks"),
            State("var-ident", "value"),
            prevent_initial_call=True,
        )
        def load_kommentar_historikk(n_clicks, orgnr):

            if not orgnr:
                raise PreventUpdate

            query = f"""
                SELECT
                    id,
                    kommentar,
                    opprettet,
                    opprettet_av,
                    aktiv
                FROM nspek_core.kommentarfelt_test_2
                WHERE orgnr = '{orgnr}'
                AND nivaa = 'generell'
                ORDER BY opprettet DESC
            """

            with get_nspek_connection() as conn:
                cursor = conn.raw_sql(query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            if df.empty:
                return [], "Ingen historikk funnet"

            df["opprettet"] = pd.to_datetime(df["opprettet"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )

            title = f"Generell kommentar - historikk ({orgnr})"

            return df.to_dict("records"), title

        @callback(
            Output(
                "generell-kommentar-historikk-grid", "rowData", allow_duplicate=True
            ),
            Output("alert_store", "data", allow_duplicate=True),
            Input("generell-kommentar-historikk-grid", "cellValueChanged"),
            State("var-ident", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def toggle_kommentar_aktiv(edited, orgnr, alert_store):

            if not edited or not orgnr:
                raise PreventUpdate

            try:
                row = edited[0]["data"]
                kommentar_id = row["id"]
                new_value = row["aktiv"]

                if new_value is True:

                    query_deactivate = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = false
                        WHERE orgnr = '{orgnr}'
                        AND nivaa = 'generell'
                    """

                    query_activate = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = true
                        WHERE id = {kommentar_id}
                    """

                    msg = "Kommentar aktivert"

                    with get_nspek_connection() as conn:
                        conn.raw_sql(query_deactivate)
                        conn.raw_sql(query_activate)

                else:

                    query = f"""
                        UPDATE nspek_core.kommentarfelt_test_2
                        SET aktiv = false
                        WHERE id = {kommentar_id}
                    """

                    msg = "Kommentar deaktivert"

                    with get_nspek_connection() as conn:
                        conn.raw_sql(query)

                query_reload = f"""
                    SELECT
                        id,
                        kommentar,
                        opprettet,
                        opprettet_av,
                        aktiv
                    FROM nspek_core.kommentarfelt_test_2
                    WHERE orgnr = '{orgnr}'
                    AND nivaa = 'generell'
                    ORDER BY opprettet DESC
                """

                with get_nspek_connection() as conn:
                    cursor = conn.raw_sql(query_reload)
                    rows = cursor.fetchall()
                    columns = [col[0] for col in cursor.description]

                df = pd.DataFrame(rows, columns=columns)
                df["opprettet"] = pd.to_datetime(df["opprettet"]).dt.strftime(
                    "%Y-%m-%d %H:%M"
                )

                alert_store = [
                    create_alert(msg, "success", ephemeral=True),
                    *(alert_store or []),
                ]

                return df.to_dict("records"), alert_store

            except Exception as e:

                logger.error(e, exc_info=True)

                alert_store = [
                    create_alert(
                        f"Oppdatering feilet: {str(e)[:80]}",
                        "danger",
                        ephemeral=True,
                    ),
                    *(alert_store or []),
                ]

                return no_update, alert_store

        @callback(
            Output("nspek-kontrollutslag-grid", "rowData"),
            Output("kontrollutslag-tab", "label"),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
            Input("refresh-manager", "data"),
        )
        def load_kontrollutslag(ident, aar, refresh_data):

            if not ident or not aar:
                return [], "Kontrollutslag"

            if refresh_data and refresh_data.get("status") == "invalid_search":
                return [], "Kontrollutslag"

            instance = NspekControls(
                time_units=["aar"],
                applies_to_subset={"aar": [int(aar)]},
            )

            kontroller_df = instance.get_current_kontroller()
            kontroller_lookup = kontroller_df.set_index("kontrollid").to_dict("index")

            df = instance.get_current_kontrollutslag()
            df = df[df["ident"] == str(ident)]

            if df.empty:
                return [], "Kontrollutslag"

            df["skildring"] = df["kontrollid"].map(
                lambda x: kontroller_lookup.get(x, {}).get("skildring")
            )
            df["tema"] = df["kontrollid"].map(
                lambda x: kontroller_lookup.get(x, {}).get("tema")
            )

            has_issues = df["utslag"].any()
            tab_label = "⚠️ Kontrollutslag" if has_issues else "Kontrollutslag"

            return df.to_dict("records"), tab_label

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("refresh-manager", "data", allow_duplicate=True),
            Input("var-ident", "value"),
            Input("var-aar", "value"),
            State("alert_store", "data"),
            State("refresh-manager", "data"),
            prevent_initial_call=True,
        )
        def validate_nspek_data_exists(orgnr, aar, alert_store, refresh_data):
            """Validates that orgnr/year exists in NSPEK registrering table.

            Example use: triggered when variable selector updates.
            """
            alert_store = alert_store or []

            if not orgnr or not aar:
                raise PreventUpdate

            if not has_data(self.conn, orgnr, aar):

                refresh_data = trigger_refresh(refresh_data, "invalid_search")

                alert_store = [
                    create_alert(
                        (
                            f"Ingen data funnet for "
                            f"orgnr {orgnr} og år {aar} i NSPEK"
                        ),
                        "danger",
                        ephemeral=True,
                    ),
                    *alert_store,
                ]

                return alert_store, refresh_data

            refresh_data = trigger_refresh(refresh_data, "valid_search")

            return alert_store, refresh_data


class NaeringsspesifikasjonTab(TabImplementation, Naeringsspesifikasjon):
    """NaeringsspesifikasjonTab is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], db_user: str | None = None) -> None:
        """Initializes the NaeringsspesifikasjonTab class."""
        Naeringsspesifikasjon.__init__(self, time_units=time_units, db_user=db_user)
        TabImplementation.__init__(self)


class NaeringsspesifikasjonWindow(WindowImplementation, Naeringsspesifikasjon):
    """NaeringsspesifikasjonWindow is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], db_user: str | None = None, **kwargs: Any) -> None:
        """Initializes the NaeringsspesifikasjonWindow class."""
        Naeringsspesifikasjon.__init__(self, time_units=time_units, db_user=db_user)
        WindowImplementation.__init__(self, **kwargs)
