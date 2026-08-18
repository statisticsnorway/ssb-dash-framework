from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
import logging
import time
from typing import Any

from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import no_update
from dash.exceptions import PreventUpdate
from ibis import Table
import ibis
from ibis.expr.types.relations import Table
from ibis.expr.types.relations import Table
from pandas.core.series import Series
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from sqlalchemy import text
from contextlib import contextmanager

from ssb_dash_framework.setup import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from ....utils.alert_handler import create_alert
from ....utils.config_tools.connection import _get_connection_object
from ....utils.config_tools.connection import get_connection
from ....utils.core_models import UpdateSkjemadata, UpdateSkjemamottak

logger = logging.getLogger(__name__)


class CallbackSettings(BaseModel):
    form_data_table: str
    form_reference_input_id: str
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


def default_getter(
    refnr: str,
    settings: CallbackSettings,
    field_path: str,
    time_units: dict,
    *args: list[Any],
) -> Any:
    logger.debug(f"Getting {field_path} for refnr: {refnr}")

    t = FormGetterCached.get_form(refnr, settings)
    filters = [
        t[settings.form_reference_number_column] == refnr,
        t[settings.formdata_fieldname_column] == field_path,
    ]
    if (
        settings.form_reference_number_column != "refnr"
    ):  # apply time_units filter if refnr is not used
        for unit, value in time_units.items():
            if value and unit in t.columns:
                filters.append(t[unit] == value)
    res: Series | Any = (
        t.filter(filters).select(settings.formdata_field_value_column_name).execute()
    )
    logger.debug(f"Returning:\n{res}")

    if res.empty:
        return None
    if len(res) > 1:  # catch potential duplicates
        logger.error(
            f"Multiple rows returned for {field_path}, refnr={refnr}. Using first row."
        )
    return res.iloc[0, 0]


_NO_REVERT = object()


def default_updater(
    value: Any,
    skjema: str,
    refnr: str,
    ident: str,
    settings: CallbackSettings,
    field_path: str,
    time_units: dict,
    *args: list[Any],
) -> tuple[list[dict[str, Any]], Any]:
    """
    Args:
        value (Any): New value to write.
        refnr (str): Refnr for Altinn3-skjema.
        settings (class): Holds all settings defined in the DataEditor class.
        field_path (str): Variable name.

    """
    logger.debug(f"Updating {field_path}")

    logger.debug(f"Raw incoming value: {value!r}, type: {type(value)}")
    old_value = default_getter(refnr, settings, field_path, time_units, *args)
    logger.debug(f"Old value from DB: {old_value!r}, type: {type(old_value)}")

    value = value.strip() if type(value) == str else value

    if value == old_value or (value == "" and not old_value):
        raise PreventUpdate

    long = settings.formdata_fieldname_column == "variabel"
    update_skjemadata = UpdateSkjemadata(
        table=settings.form_data_table,
        skjema=skjema,
        ident=ident,
        identifier_column=settings.form_reference_number_column,
        refnr=refnr,
        time_units=time_units,
        column=settings.formdata_field_value_column_name,
        variable=field_path,
        value=value,
        old_value=old_value,
        long=long,
        mapping_table=settings.mapping_table,
        mapping_match_column=settings.mapping_match_column,
        mapping_result_column=settings.mapping_result_column,
    )
    update_skjemamottak = UpdateSkjemamottak(
        refnr=refnr, column="status", value="Under arbeid", on_skjemadata_update=True
    )

    if not isinstance(_get_connection_object(), ConnectionPool):
        raise NotImplementedError(
            f"Connection of type '{type(_get_connection_object())}' is not implemented yet."
        )

    skjemadata_alert = update_skjemadata.update_ibis(long=long)
    alerts: list[dict[str, Any]] = [skjemadata_alert] if skjemadata_alert else []

    if not skjemadata_alert or skjemadata_alert.get("color") != "success":
        # update failed (e.g. datatype mismatch)
        return alerts, old_value

    try:
        if "skjemadata" in settings.form_data_table:
            skjemamottak_alert = update_skjemamottak.update_ibis()
            if skjemamottak_alert:
                alerts.append(skjemamottak_alert)
    except PreventUpdate:
        logger.debug("skjemamottak status update skipped (not 'Ubehandlet')")

    FormGetterCached.evict(refnr, settings.form_data_table)
    return alerts, _NO_REVERT


class EditableField(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    field_path: str
    variabel_trigger: str = "n_blur"
