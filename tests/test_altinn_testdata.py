"""Checks that the configured backend serves the Altinn testdata to the framework."""

from ssb_dash_framework.utils.config_tools.connection import get_connection

EXPECTED_TABLES = {
    "enheter",
    "enhetsinfo",
    "kontaktinfo",
    "skjemadata",
    "skjemamottak",
}


def test_all_testdata_tables_are_available() -> None:
    with get_connection() as conn:
        assert EXPECTED_TABLES <= set(conn.list_tables())


def test_data_survives_between_connections() -> None:
    """Each get_connection() must reach the same database, not a fresh empty one."""
    with get_connection() as conn:
        first = conn.table("skjemadata").count().to_pyarrow().as_py()
    with get_connection() as conn:
        second = conn.table("skjemadata").count().to_pyarrow().as_py()

    assert first == 443
    assert second == first
