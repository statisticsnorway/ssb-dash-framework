from ssb_dash_framework import AltinnSkjemadataEditor
from ssb_dash_framework import AltinnSupportTable
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert AltinnSkjemadataEditor is not None
    assert AltinnSupportTable is not None


def test_instantiation() -> None:
    set_variables(["year", "quarter", "refnr", "statistikkvariabel", "ident"])
    AltinnSkjemadataEditor(time_units=["year", "quarter"], variable_connection={})
