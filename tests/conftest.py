from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import ibis
import pytest

from ssb_dash_framework import VariableSelector
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import set_connection


@pytest.fixture
def config_yaml():
    yaml_file = Path(__file__).parent / "config" / "example_config.yaml"
    return config_parser_yaml(yaml_file)


@pytest.fixture(autouse=True)
def clear_VariableSelector_variableselectoroptions() -> Generator[None]:
    """Automatically clears the VariableSelector registry before each test.

    This ensures that each test starts with an empty codelist (so VariableSelector
    sees no codes unless the test explicitly creates some). After yielding to
    the test, it clears the registry again.

    Yields:
        None: Control is yielded to the test, after which the registry is cleared.
    """
    VariableSelector._variableselectoroptions.clear()
    yield
    VariableSelector._variableselectoroptions.clear()


import polars as pl


def load_demo_dataset(con: ibis.BaseBackend) -> None:
    # -----------------------------
    # Enheter
    # -----------------------------
    enheter = pl.DataFrame(
        {
            "aar": [2024, 2024, 2024],
            "ident": ["1001", "1002", "1003"],
            "skjema": ["RA-001", "RA-001", "RA-002"],
        }
    )

    # -----------------------------
    # Enhetsinfo
    # -----------------------------
    enhetsinfo = pl.DataFrame(
        {
            "aar": [2024, 2024, 2024, 2024],
            "ident": ["1001", "1001", "1002", "1003"],
            "variabel": [
                "naring",
                "ansatte",
                "naring",
                "omsetning",
            ],
            "verdi": [
                "IT Consulting",
                "15",
                "Retail",
                "2500000",
            ],
        }
    )

    # -----------------------------
    # Skjemadata
    # -----------------------------
    skjemadata = pl.DataFrame(
        {
            "aar": [2024, 2024, 2024, 2024],
            "ident": ["1001", "1001", "1002", "1003"],
            "skjema": ["RA-001", "RA-001", "RA-001", "RA-002"],
            "refnr": [1, 2, 1, 1],
            "feltsti": [
                "resultat.omsetning",
                "resultat.kostnad",
                "butikk.areal",
                "finans.inntekt",
            ],
            "feltnavn": [
                "Omsetning",
                "Kostnad",
                "Butikkareal",
                "Finansinntekt",
            ],
            "verdi": ["1200000", "400000", "250", "900000"],
            "alias": [
                "revenue",
                "cost",
                "store_area",
                "finance_income",
            ],
            "dybde": [1, 1, 2, 1],
            "indeks": [0, 1, 0, 0],
        }
    )

    # -----------------------------
    # Skjemamottak
    # -----------------------------
    skjemamottak = pl.DataFrame(
        {
            "aar": [2024, 2024, 2024],
            "ident": ["1001", "1002", "1003"],
            "skjema": ["RA-001", "RA-001", "RA-002"],
            "refnr": [1, 1, 1],
            "kommentar_intern": [
                "Godkjent automatisk",
                "Mangler vedlegg",
                "Manuell kontroll utført",
            ],
            "dato_mottatt": [
                "2024-01-15",
                "2024-01-18",
                "2024-02-01",
            ],
            "status": [
                "OK",
                "PENDING",
                "OK",
            ],
        }
    )

    # -----------------------------
    # Kontaktinfo
    # -----------------------------
    kontaktinfo = pl.DataFrame(
        {
            "aar": [2024, 2024, 2024],
            "ident": ["1001", "1002", "1003"],
            "skjema": ["RA-001", "RA-001", "RA-002"],
            "refnr": [1, 1, 1],
            "kontaktperson": [
                "Ola Nordmann",
                "Kari Hansen",
                "Per Johansen",
            ],
            "epost": [
                "ola@example.no",
                "kari@example.no",
                "per@example.no",
            ],
            "telefon": [
                "+4791111111",
                "+4792222222",
                "+4793333333",
            ],
            "bekreftet_kontaktinfo": [True, False, True],
            "kommentar_kontaktinfo": [
                "",
                "Telefon ikke verifisert",
                "",
            ],
            "kommentar_krevende": [
                False,
                True,
                False,
            ],
        }
    )

    # Register tables in ibis/polars connection
    con.create_table("enheter", enheter, overwrite=True)
    con.create_table("enhetsinfo", enhetsinfo, overwrite=True)
    con.create_table("skjemadata_hoved", skjemadata, overwrite=True)
    con.create_table("skjemamottak", skjemamottak, overwrite=True)
    con.create_table("kontaktinfo", kontaktinfo, overwrite=True)


@pytest.fixture(autouse=True, scope="session")
def testing_connection():
    ibis_polars_conn = ibis.polars.connect()
    load_demo_dataset(ibis_polars_conn)

    @contextmanager
    def _ibis_polars_cm(*args, **kwargs):
        yield ibis_polars_conn

    set_connection(_ibis_polars_cm, is_pooled=False)

    yield ibis_polars_conn

    try:
        ibis_polars_conn.close()
    except Exception:
        pass


@pytest.fixture(autouse=True, scope="session")
def ibis_polars_conn():
    print("Setting up connection...")
    # Example: create a DB connection, API client, etc.
    ibis_polars_conn = ibis.polars.connect()
    yield ibis_polars_conn
