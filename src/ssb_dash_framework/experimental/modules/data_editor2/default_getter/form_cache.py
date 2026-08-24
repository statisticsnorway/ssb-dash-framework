

from dataclasses import dataclass
import logging
import time

import tzlocal

from pydantic import BaseModel, ConfigDict
from ibis import Table
import ibis
from ibis import _
from ibis.expr.types.relations import Table
from ibis.expr.types.relations import Table

from ssb_dash_framework import get_connection

logger = logging.getLogger(__name__)
local_tz = tzlocal.get_localzone()

class CallbackSettings(BaseModel):
    model_config = ConfigDict(extra="allow")
    form_data_table: str
    form_reference_number_column: str
    formdata_field_value_column_name: str
    formdata_fieldname_column: str

    mapping_table: str = "mapping_variabelnavn"
    mapping_match_column: str = "variabel"
    mapping_result_column: str = "feltsti"

    table_selector_id: str | None = None
    form_selector_id: str | None = None


@dataclass
class CacheEntry:
    entry: Table
    last_cache_hit: float


class FormGetterCached:
    data: dict[str, CacheEntry] = {}

    @staticmethod
    def get_table(refnr: str, settings: CallbackSettings) -> Table:
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
                settings.form_reference_number_column not in t.columns
            ):  # catch errors with querying from wrong table
                raise ValueError(
                    f"Column '{settings.form_reference_number_column}' not in table "
                    f"'{settings.form_data_table}'. Available: {t.columns}"
                )
            df = t.filter(
                t[settings.form_reference_number_column] == refnr,
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
    def get_form(cls, refnr: str, settings: CallbackSettings) -> Table:
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