"""Tests for ``set_postgres_connection``'s optional per-connection ``configure`` hook."""

from unittest.mock import patch

from ssb_dash_framework.utils.config_tools import connection


def test_set_postgres_connection_forwards_configure_callback() -> None:
    """A provided ``configure`` callback is passed straight through to ConnectionPool."""

    def my_configure(conn: object) -> None:  # pragma: no cover - not invoked in this test
        pass

    with (
        patch.object(connection, "ConnectionPool") as pool_cls,
        patch.object(connection, "set_connection"),
    ):
        connection.set_postgres_connection(
            database_url="postgresql://example",
            pool_min_size=2,
            pool_max_size=8,
            configure=my_configure,
        )

    pool_cls.assert_called_once_with(
        conninfo="postgresql://example",
        min_size=2,
        max_size=8,
        configure=my_configure,
    )


def test_set_postgres_connection_defaults_configure_to_none() -> None:
    """Existing callers that omit ``configure`` still pass ``configure=None`` (no-op)."""
    with (
        patch.object(connection, "ConnectionPool") as pool_cls,
        patch.object(connection, "set_connection"),
    ):
        connection.set_postgres_connection(database_url="postgresql://example")

    _, kwargs = pool_cls.call_args
    assert kwargs["configure"] is None
    assert kwargs["conninfo"] == "postgresql://example"
    assert kwargs["min_size"] == 1
    assert kwargs["max_size"] == 1
