from ssb_dash_framework import AltinnSkjemadataEditor
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert AltinnSkjemadataEditor is not None


def test_instantiation(ibis_polars_conn) -> None:
    set_variables(["year", "quarter", "refnr", "statistikkvariabel", "ident"])
    AltinnSkjemadataEditor(
        time_units=["year", "quarter"], conn=ibis_polars_conn, variable_connection={}
    )
