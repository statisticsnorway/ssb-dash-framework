"""Tests for the configurable nspek postgres connection (host/port/database)."""

from unittest.mock import MagicMock
from unittest.mock import patch

from ibis import BaseBackend

from ssb_dash_framework.modules.nspek import nspek_utils


def test_build_nspek_conn_url_defaults() -> None:
    """Defaults reproduce the previous hardcoded localhost:5432/nspek URL."""
    url = nspek_utils._build_nspek_conn_url("nspek-developers@dapla-group-sa-p-ye.iam")
    assert url == (
        "postgresql://nspek-developers%40dapla-group-sa-p-ye.iam@localhost:5432/nspek"
    )


def test_build_nspek_conn_url_custom_target() -> None:
    """Host, port and database are all overridable."""
    url = nspek_utils._build_nspek_conn_url(
        "user@iam", host="10.0.0.5", port=6432, database="strukt_naering"
    )
    assert url == "postgresql://user%40iam@10.0.0.5:6432/strukt_naering"


def test_set_nspek_connection_forwards_target_to_pool() -> None:
    """set_nspek_connection builds the conninfo from host/port/database and passes it on."""
    with (
        patch.object(nspek_utils, "ConnectionPool") as pool_cls,
        patch.object(nspek_utils, "Backend") as backend,
    ):
        # Make the post-construction validation pass without a real DB.
        backend.from_connection.return_value = MagicMock(spec=BaseBackend)
        nspek_utils.set_nspek_connection(
            database_user="user@iam",
            host="db.internal",
            port=6432,
            database="strukt_naering",
        )

    pool_cls.assert_called_once_with(
        conninfo="postgresql://user%40iam@db.internal:6432/strukt_naering",
        min_size=1,
        max_size=1,
    )


def test_set_nspek_connection_defaults_unchanged() -> None:
    """Omitting the new args keeps the original localhost:5432/nspek behavior."""
    with (
        patch.object(nspek_utils, "ConnectionPool") as pool_cls,
        patch.object(nspek_utils, "Backend") as backend,
    ):
        backend.from_connection.return_value = MagicMock(spec=BaseBackend)
        nspek_utils.set_nspek_connection(database_user="nspek-developers@x")

    _, kwargs = pool_cls.call_args
    assert kwargs["conninfo"] == "postgresql://nspek-developers%40x@localhost:5432/nspek"
