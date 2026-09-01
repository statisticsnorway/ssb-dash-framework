import logging
import time
from dataclasses import dataclass

import ibis
import tzlocal
from ibis import Table
from ibis.expr.types.relations import Table

from ....utils.config_tools.connection import get_connection
from ..utils import EditorSettings

logger = logging.getLogger(__name__)
local_tz = tzlocal.get_localzone()


@dataclass
class CacheEntry:
    entry: Table
    last_cache_hit: float


class FormGetterCached:
    data: dict[str, CacheEntry] = {}

    @staticmethod
    def get_table(refnr: str, settings: EditorSettings) -> Table:
        """Materialize the whole refnr-filtered form in ONE query.

        The per-field ``default_getter`` re-filters this result once per editable
        field (~48 for RA-0255). Returning a *lazy* Postgres expression here means
        each of those re-filters is a separate database round-trip on every refnr
        change -- the dominant cost of loading the data editor.

        Instead we execute a single query for the whole refnr-filtered form and
        return an in-memory ``ibis.memtable``. The subsequent per-field
        filter/select then run entirely in-process (DuckDB) with no further
        database round-trips. ``get_form`` caches this materialized table; writes
        evict it via :meth:`evict` so reads stay fresh.
        """
        with get_connection() as conn:
            t = conn.table(settings.form_data_table)
            if (
                settings.refnr_col not in t.columns
            ):  # catch errors with querying from wrong table
                raise ValueError(
                    f"Column '{settings.refnr_col}' not in table "
                    f"'{settings.form_data_table}'. Available: {t.columns}"
                )
            df = t.filter(
                t[settings.refnr_col] == refnr,
            ).to_pandas()
        # memtable preserves column names + dtypes; downstream filter/select run
        # in DuckDB, so they never touch the database again.
        return ibis.memtable(df)

    @classmethod
    def clean_cache(cls):
        max_size = 10
        if len(cls.data.keys()) > max_size:
            key, _ = min(cls.data.items(), key=lambda x: x[1].last_cache_hit)
            cls.data.pop(key)

    @classmethod
    def evict(cls, refnr: str, table: str) -> None:
        """Drop the cached form for ``(table, refnr)`` so the next read is fresh.

        Call this after a write: because :meth:`get_table` now returns a
        materialized snapshot, an un-evicted entry would serve stale values for up
        to the ``get_form`` TTL after an edit.
        """
        cls.data.pop(f"{table}::{refnr}", None)

    @classmethod
    def get_form(cls, refnr: str, settings: EditorSettings) -> Table:
        cache_key = (
            f"{settings.form_data_table}::{refnr}"  # for tables not querying skjemadata
        )
        entry = cls.data.get(cache_key)

        if (entry is None) or ((time.perf_counter() - entry.last_cache_hit) > 5.0):
            table = FormGetterCached.get_table(refnr, settings)
            cls.data[cache_key] = CacheEntry(
                entry=table, last_cache_hit=time.perf_counter()
            )
            cls.clean_cache()
            return cls.data[cache_key].entry
        cls.clean_cache()
        return entry.entry
