from datetime import UTC
from datetime import datetime
from typing import Any

import pandas as pd
from ibis import _
from ibis.backends import BaseBackend

from .nspek_control_config import CONTROL_RULES
from .nspek_control_config import get_controls_for_field
from .nspek_control_config import get_rule_by_id

TYPE_REGNSKAP_TABLE = {
    "registrering": {
        "database": "nspek_core",
        "table": "registrering",
    },
    "v_registrering_versjon": {
        "database": "nspek_core",
        "table": "v_registrering_versjon",
    },
    "v_update_counts": {
        "database": "nspek_core",
        "table": "v_update_counts",
    },
    "balanseregnskap": {
        "database": "balanseregnskap",
        "table": "tema_balanse",
    },
    "resultatregnskap": {
        "database": "resultatregnskap",
        "table": "tema_resultat",
    },
}


def get_active_versions(conn, aar: int) -> pd.DataFrame:
    print("Henter aktive versjoner")

    config = TYPE_REGNSKAP_TABLE["v_registrering_versjon"]

    t_versions = conn.table(config["table"], database=config["database"])

    df_versions = (
        t_versions.filter(_.aar == aar)
        .order_by(_.versjon_nr)
        .select(
            _.orgnr,
            _.aar,
            _.sekvensnummer,
            _.versjon_nr,
            _.antall_versjoner,
            _.dato_mottatt,
        )
        .execute()
    )

    config = TYPE_REGNSKAP_TABLE["v_update_counts"]

    t_updates: Any = conn.table(config["table"], database=config["database"])

    df_updates = t_updates.filter(
        _.sekvensnummer.isin(df_versions["sekvensnummer"].tolist())
    ).execute()

    df_versions = df_versions.merge(df_updates, on="sekvensnummer", how="left")

    df_versions["antall_endringer"] = df_versions["antall_endringer"].fillna(0)
    df_versions["har_endringer"] = df_versions["antall_endringer"] > 0

    df_active = (
        df_versions.sort_values(
            ["orgnr", "aar", "har_endringer", "dato_mottatt"],
            ascending=[True, True, False, False],
        )
        .groupby(["orgnr", "aar"])
        .head(1)
    )

    print(f"Fant {len(df_active)} aktive versjoner")

    return df_active


def get_scope_for_sekvensnummer(conn, sekvensnummer: int) -> pd.DataFrame:

    config = TYPE_REGNSKAP_TABLE["registrering"]

    t = conn.table(config["table"], database=config["database"])

    return (
        t.filter(_.sekvensnummer == sekvensnummer)
        .select(
            _.orgnr,
            _.aar,
            _.sekvensnummer,
        )
        .execute()
    )


def get_regnskaps_data(
    conn, scope_df: pd.DataFrame, regnskapstype: str
) -> pd.DataFrame:

    print(f"Henter {regnskapstype}")

    sekvensnummer_liste = scope_df["sekvensnummer"].tolist()

    config = TYPE_REGNSKAP_TABLE[regnskapstype]

    t = conn.table(config["table"], database=config["database"])

    df = t.filter(_.sekvensnummer.isin(sekvensnummer_liste)).execute()

    df_wide = df.pivot_table(
        index=["sekvensnummer"],
        columns="felt",
        values="belop",
        aggfunc="sum",
    ).reset_index()

    df_wide.columns.name = None

    df_wide = df_wide.merge(
        scope_df[["sekvensnummer", "orgnr", "aar"]], on="sekvensnummer", how="left"
    )

    print(f"Fant {len(df_wide)} rader")

    return df_wide


def make_kontroller_df(aar: int) -> pd.DataFrame:
    print("Lager kontroll_df")
    kontroll_df = pd.DataFrame(
        [
            {
                "aar": aar,
                "tema": rule["tema"],
                "kontrollid": rule["kontrollid"],
                "kategori": rule["kategori"],
                "skildring": rule["skildring"],
                "python_fn": "evaluate_sum_rule",
                "sorteringsvariabel": "verdi",
                "sortering": "DESC",
                "sist_kjoert": datetime.now(UTC),
            }
            for rule in CONTROL_RULES
        ]
    )
    print(f"kontroll_df inneholder {len(kontroll_df)} rader")
    return kontroll_df


def sql_value(v):
    if pd.isna(v):
        return "NULL"

    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"

    if isinstance(v, (datetime, pd.Timestamp)):
        return "'" + v.isoformat(sep=" ") + "'"

    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"

    return str(v)


def insert_batches(
    conn, table_name: str, columns: list[str], rows: list[dict], chunk_size: int = 5000
) -> None:
    if not rows:
        return

    cols_sql = ", ".join(columns)

    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]

        values_sql = ",".join(
            "(" + ",".join(sql_value(v) for v in row.values()) + ")" for row in chunk
        )

        conn.raw_sql(f"""
            INSERT INTO nspek_core.{table_name}
            ({cols_sql})
            VALUES {values_sql}
            """)


def save_full_control_db(
    conn: BaseBackend,
    aar: int,
    df_kontroller: pd.DataFrame,
    df_kontrollutslag: pd.DataFrame,
) -> None:
    print("Sletter og laster til kontrollutslag og kontroll tabellene.")
    kontrollids = df_kontroller["kontrollid"].unique().tolist()
    if not kontrollids:
        return

    kontrollids_sql = ",".join(sql_value(x) for x in kontrollids)

    try:
        conn.raw_sql("BEGIN;")

        conn.raw_sql(f"""
            DELETE FROM nspek_core.kontrollutslag
            WHERE aar = {aar}
            AND kontrollid IN ({kontrollids_sql})
            """)

        conn.raw_sql(f"""
            DELETE FROM nspek_core.kontroller
            WHERE aar = {aar}
            AND kontrollid IN ({kontrollids_sql})
            """)

        insert_batches(
            conn,
            "kontroller",
            [
                "aar",
                "tema",
                "kontrollid",
                "kategori",
                "skildring",
                "python_fn",
                "sorteringsvariabel",
                "sortering",
                "sist_kjoert",
            ],
            df_kontroller.to_dict("records"),
            chunk_size=1000,
        )

        insert_batches(
            conn,
            "kontrollutslag",
            [
                "aar",
                "kontrollid",
                "sekvensnummer",
                "orgnr",
                "utslag",
                "verdi",
            ],
            df_kontrollutslag.to_dict("records"),
            chunk_size=5000,
        )

        conn.raw_sql("COMMIT;")

    except Exception:
        conn.raw_sql("ROLLBACK;")
        raise


def save_incremental_control_db(
    conn: BaseBackend,
    sekvensnummer: int,
    kontrollids: list[str],
    df_kontrollutslag: pd.DataFrame,
):

    if not kontrollids:
        return

    kontrollids_sql = ",".join(sql_value(x) for x in kontrollids)
    try:
        conn.raw_sql("BEGIN;")

        conn.raw_sql(f"""
            DELETE FROM nspek_core.kontrollutslag
            WHERE sekvensnummer = {sekvensnummer}
            AND kontrollid IN ({kontrollids_sql})
            """)

        insert_batches(
            conn,
            "kontrollutslag",
            [
                "aar",
                "kontrollid",
                "sekvensnummer",
                "orgnr",
                "utslag",
                "verdi",
            ],
            df_kontrollutslag.to_dict("records"),
        )

        conn.raw_sql("COMMIT;")

    except Exception:
        conn.raw_sql("ROLLBACK;")
        raise


def evaluate_sum_rule(df: pd.DataFrame, rule: dict) -> pd.DataFrame:
    print(f"Kjører regler for {rule['kontrollid']}:")
    lhs = pd.to_numeric(
        df.get(rule["lhs"], pd.Series(0, index=df.index)),
        errors="coerce",
    ).fillna(0)

    rhs = pd.Series(0, index=df.index, dtype="float64")

    for col, sign in rule["terms"]:

        term = pd.to_numeric(
            df.get(col, pd.Series(0, index=df.index)),
            errors="coerce",
        ).fillna(0)

        rhs = rhs + sign * term

    diff = lhs - rhs
    threshold = rule.get("threshold", 0)

    result = pd.DataFrame(
        {
            "aar": df["aar"],
            "kontrollid": rule["kontrollid"],
            "sekvensnummer": df["sekvensnummer"],
            "orgnr": df["orgnr"],
            "utslag": abs(diff) > threshold,
            "verdi": diff,
        }
    )

    resultat_df = result[result["utslag"]].reset_index(drop=True)
    print(f"Fant {len(resultat_df)} utslag for {rule['kontrollid']}")
    return resultat_df


def run_all_controls(
    df_resultat: pd.DataFrame, df_balanse: pd.DataFrame
) -> pd.DataFrame:
    all_results = []

    for rule in CONTROL_RULES:
        if rule["tema"] == "Resultat":
            df = df_resultat
        elif rule["tema"] == "Balanse":
            df = df_balanse
        else:
            continue

        result = evaluate_sum_rule(df, rule)

        all_results.append(result)

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)


def run_controls_for_changed_fields(
    changed_fields: list[str], df_resultat: pd.DataFrame, df_balanse: pd.DataFrame
) -> pd.DataFrame:
    kontrollids = set()

    for field in changed_fields:
        kontroller = get_controls_for_field(field)
        kontrollids.update(kontroller)

    kontrollids = sorted(kontrollids)

    print(f"Trigget kontroller: " f"{kontrollids}")

    all_results = []

    for kontrollid in kontrollids:

        rule = get_rule_by_id(kontrollid)

        if rule is None:
            print(f"Fant ikke kontroll: {kontrollid}")
            continue

        if rule["tema"] == "Resultat":
            df = df_resultat
        elif rule["tema"] == "Balanse":
            df = df_balanse
        else:
            continue

        result = evaluate_sum_rule(df, rule)

        all_results.append(result)

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)


def run_all_controls_for_year(conn: BaseBackend, aar: int) -> None:

    scope_df = get_active_versions(conn, aar)

    df_resultat = get_regnskaps_data(conn, scope_df, "resultatregnskap")
    df_balanse = get_regnskaps_data(conn, scope_df, "balanseregnskap")

    df_kontrollutslag = run_all_controls(df_resultat, df_balanse)
    df_kontroller = make_kontroller_df(aar)

    save_full_control_db(conn, aar, df_kontroller, df_kontrollutslag)


def run_all_controls_for_sekvensnummer(
    conn: BaseBackend, sekvensnummer: int
) -> pd.DataFrame:

    scope_df = get_scope_for_sekvensnummer(conn, sekvensnummer)

    kontrollids = [rule["kontrollid"] for rule in CONTROL_RULES]

    df_resultat = get_regnskaps_data(
        conn,
        scope_df,
        "resultatregnskap",
    )
    df_balanse = get_regnskaps_data(conn, scope_df, "balanseregnskap")

    df_kontrollutslag = run_all_controls(df_resultat, df_balanse)

    save_incremental_control_db(conn, sekvensnummer, kontrollids, df_kontrollutslag)

    return df_kontrollutslag


def run_controls_changed_fields_for_sekvensnummer(
    conn: BaseBackend, sekvensnummer: int, changed_fields: list[str]
) -> None:

    scope_df = get_scope_for_sekvensnummer(conn, sekvensnummer)

    df_resultat = get_regnskaps_data(conn, scope_df, "resultatregnskap")
    df_balanse = get_regnskaps_data(conn, scope_df, "balanseregnskap")
    df_kontrollutslag = run_controls_for_changed_fields(
        changed_fields, df_resultat, df_balanse
    )

    kontrollids = set()

    for field in changed_fields:
        kontrollids.update(get_controls_for_field(field))

    save_incremental_control_db(
        conn, sekvensnummer, sorted(kontrollids), df_kontrollutslag
    )
