"""Tests for NSPEK connection targets and isolated pool lifecycle handling."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import call

import pytest
from ibis import BaseBackend
from psycopg.conninfo import conninfo_to_dict

from ssb_dash_framework.modules.nspek import nspek_utils


class _FakePool:
    """Keep a real pool type for isinstance checks without opening connections."""

    def __init__(self, conninfo: str, min_size: int, max_size: int) -> None:
        """Record connection parameters and expose mocked pool operations."""
        self.conninfo = conninfo
        self.min_size = min_size
        self.max_size = max_size
        self.connection = MagicMock()
        self.close = MagicMock()


@pytest.fixture(autouse=True)
def isolated_nspek(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Restore module state and avoid registering test pools at process exit."""
    for name in (
        "_IS_POOLED_NSPEK",
        "_CONNECTION_NSPEK",
        "_CONNECTION_CALLABLE_NSPEK",
    ):
        monkeypatch.setattr(nspek_utils, name, None)
    hooks = MagicMock()
    hooks.from_connection.return_value = MagicMock(spec=BaseBackend)
    monkeypatch.setattr(nspek_utils, "ConnectionPool", _FakePool)
    monkeypatch.setattr(
        nspek_utils, "Backend", SimpleNamespace(from_connection=hooks.from_connection)
    )
    monkeypatch.setattr(
        nspek_utils,
        "atexit",
        SimpleNamespace(register=hooks.register, unregister=hooks.unregister),
    )
    return hooks


def test_build_nspek_conninfo_defaults() -> None:
    """Defaults preserve the existing IAM user and localhost database target."""
    user = "nspek-developers@dapla-group-sa-p-ye.iam"
    assert conninfo_to_dict(nspek_utils._build_nspek_conninfo(user)) == {
        "user": user,
        "host": "localhost",
        "port": "5432",
        "dbname": "nspek",
    }


@pytest.mark.parametrize(
    ("user", "host", "database"),
    [
        ("user@iam", "db.internal", "strukt_naering"),
        ("first last+user@iam", "::1", "nspek?sslmode=disable"),
        ("user'\\name@iam", "/tmp/postgres socket", "nspek 'data\\backup"),
    ],
)
def test_build_nspek_conninfo_preserves_target(
    user: str, host: str, database: str
) -> None:
    """Special characters stay in their values rather than adding URL options."""
    conninfo = nspek_utils._build_nspek_conninfo(
        user, host=host, port=6432, database=database
    )
    assert conninfo_to_dict(conninfo) == {
        "user": user,
        "host": host,
        "port": "6432",
        "dbname": database,
    }


def test_set_nspek_connection_forwards_target_to_pool(
    isolated_nspek: MagicMock,
) -> None:
    """A custom target reaches the pool and its Ibis context manager."""
    nspek_utils.set_nspek_connection(
        database_user="user@iam",
        host="db.internal",
        port=6432,
        database="strukt_naering",
    )
    pool = nspek_utils._get_nspek_connection_object()
    assert isinstance(pool, _FakePool)
    assert conninfo_to_dict(pool.conninfo) == {
        "user": "user@iam",
        "host": "db.internal",
        "port": "6432",
        "dbname": "strukt_naering",
    }
    assert (pool.min_size, pool.max_size) == (1, 1)
    isolated_nspek.register.assert_called_once_with(pool.close)
    with nspek_utils.get_nspek_connection() as conn:
        assert conn is isolated_nspek.from_connection.return_value
    assert pool.connection.call_count == 2  # Initial validation and the caller.


def test_set_nspek_connection_defaults_unchanged() -> None:
    """Omitting arguments preserves the default user, host, port and database."""
    nspek_utils.set_nspek_connection()
    pool = nspek_utils._get_nspek_connection_object()
    assert isinstance(pool, _FakePool)
    assert conninfo_to_dict(pool.conninfo) == {
        "user": "nspek-developers@dapla-group-sa-p-ye.iam",
        "host": "localhost",
        "port": "5432",
        "dbname": "nspek",
    }


def test_set_nspek_connection_replaces_previous_pool(isolated_nspek: MagicMock) -> None:
    """Reconfiguration unregisters and closes the old pool before keeping a new one."""
    nspek_utils.set_nspek_connection()
    previous = nspek_utils._get_nspek_connection_object()
    assert isinstance(previous, _FakePool)
    isolated_nspek.attach_mock(previous.close, "previous_close")
    isolated_nspek.reset_mock()

    nspek_utils.set_nspek_connection(database="replacement")
    current = nspek_utils._get_nspek_connection_object()
    assert isinstance(current, _FakePool)
    assert current is not previous
    isolated_nspek.assert_has_calls(
        [
            call.unregister(previous.close),
            call.previous_close(),
            call.register(current.close),
        ]
    )
    previous.close.assert_called_once_with()
    current.close.assert_not_called()
