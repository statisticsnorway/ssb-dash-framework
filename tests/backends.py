"""Registry of database backends the whole test suite is run against.

Each entry configures the framework's global connection (``set_connection`` or one
of its helpers) so that ``get_connection()`` yields an ibis backend holding the
Altinn testdata. To add a variation, add one ``BackendSpec`` to ``BACKENDS``.
"""

import os
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import AbstractContextManager
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from ssb_dash_framework.utils.config_tools import connection

from .testdata.altinn import build_db

POSTGRES_URL_ENV = "TEST_POSTGRES_URL"


@dataclass(frozen=True)
class BackendSpec:
    """A single way of configuring the framework's global database connection."""

    name: str
    setup: Callable[[Path], AbstractContextManager[None]]
    skip_reason: Callable[[], str | None] = field(default=lambda: None)


def _reset_connection_state() -> None:
    connection._IS_POOLED = None
    connection._CONNECTION = None
    connection._CONNECTION_CALLABLE = None


@contextmanager
def _sqlite(tmp_dir: Path) -> Iterator[None]:
    # An on-disk file is required: set_sqlite_connection() opens a new ibis
    # connection per get_connection() call, so ":memory:" would be empty each time.
    db_path = tmp_dir / "altinn.sqlite"
    build_db.seed_sqlite(db_path)
    connection.set_sqlite_connection(str(db_path))
    try:
        yield
    finally:
        _reset_connection_state()


def _postgres_skip_reason() -> str | None:
    if not os.environ.get(POSTGRES_URL_ENV):
        return f"{POSTGRES_URL_ENV} is not set"
    return None


@contextmanager
def _postgres(tmp_dir: Path) -> Iterator[None]:
    database_url = os.environ[POSTGRES_URL_ENV]
    build_db.seed_postgres(database_url)
    connection.set_postgres_connection(database_url)
    try:
        yield
    finally:
        pool = connection._get_connection_object()
        if pool is not None:
            pool.close()  # type: ignore[attr-defined]
        _reset_connection_state()


BACKENDS: dict[str, BackendSpec] = {
    spec.name: spec
    for spec in (
        BackendSpec(name="sqlite", setup=_sqlite),
        BackendSpec(
            name="postgres", setup=_postgres, skip_reason=_postgres_skip_reason
        ),
    )
}
