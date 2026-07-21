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
        t.filter(filters).select(settings.formdata_field_value_column_name).to_pandas()
    )
    logger.debug(f"Returning:\n{res}")

    if res.empty:
        return None
    if len(res) > 1:  # catch potential duplicates
        logger.error(
            f"Multiple rows returned for {field_path}, refnr={refnr}. Using first row."
        )
    return res.iloc[0, 0]


def default_updater(
    value: Any,
    skjema: str,
    refnr: str,
    ident: str,
    settings: CallbackSettings,
    field_path: str,
    time_units: dict,
    *args: list[Any],
) -> list[dict[str, Any]]:
    """
    Args:
        value (Any): New value to write.
        refnr (str): Refnr for Altinn3-skjema.
        settings (class): Holds all settings defined in the DataEditor class.
        field_path (str): Variable name.

    """
    logger.debug(f"Updating {field_path}")

    logger.debug(f"Raw incoming value: {value!r}, type: {type(value)}")
    old_value = default_getter(
        refnr, settings, field_path, time_units, *args
    )
    logger.debug(f"Old value from DB: {old_value!r}, type: {type(old_value)}")

    if value == old_value or (value == "" and not old_value):
        raise PreventUpdate

    long = False
    if settings.formdata_fieldname_column == "variabel":
        long = True
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
        refnr=refnr,
        column="status",
        value='Under arbeid',
        on_skjemadata_update=True
    )

    if isinstance(_get_connection_object(), ConnectionPool):
        skjemadata_alert = update_skjemadata.update_ibis(long=long)
        alerts: list[dict[str, Any]] = [skjemadata_alert] if skjemadata_alert else []
        try:
            if "skjemadata" in settings.form_data_table:
                skjemamottak_alert = update_skjemamottak.update_ibis()
                if skjemamottak_alert:
                    alerts.append(skjemamottak_alert)
        except PreventUpdate:
            logger.debug("skjemamottak status update skipped (not 'Ubehandlet')")
        # get_table now returns a materialized snapshot; evict it so the next read
        # (including the old_value lookup on the very next edit) sees the new value.
        FormGetterCached.evict(refnr, settings.form_data_table)

        return alerts
    else:
        raise NotImplementedError(
            f"Connection of type '{type(_get_connection_object())}' is not implemented yet."
        )

def _extend_alert_log(alert_log: list[Any] | None, alert: Any) -> list[Any]:
    """Returns a flat list of alert dicts."""
    log = list(alert_log or [])
    if not alert:
        return log
    if isinstance(alert, list):
        log.extend(a for a in alert if a)
    else:
        log.append(alert)
    return log


def _run_field(
    field: "EditableField",
    *,
    edited: bool,
    value: Any,
    refnr: str,
    ident: str,
    skjema: str,
    settings: "CallbackSettings",
    time_units: dict,
    extra_args: list[Any],
) -> Any:
    """Run one field's updater (if edited) or getter (if not).

    Returns the updater's alert(s) when ``edited`` is True, or the getter's
    value to display when ``edited`` is False.
    """
    if edited:
        return field.update_func(
            value,
            skjema,
            refnr,
            ident,
            settings,
            field.field_path,
            time_units,
            *extra_args,
        )
    try:
        return field.getter_func(
            refnr,
            settings,
            field.field_path,
            time_units,
            *extra_args,
        )
    except Exception:
        logger.exception("getter failed for field %s", field.field_path)
        return no_update

_collect_stack: list[list[tuple["EditableField", CallbackSettings, Any, Any]]] = []

@contextmanager
def batch_editable_fields():
    """Batch every EditableField.create_callback() call made inside this
    block into one callback pair, instead of one pair per field.
    """
    collector: list[tuple[EditableField, CallbackSettings, Any, Any, Any]] = []
    _collect_stack.append(collector)
    try:
        yield
    finally:
        _collect_stack.pop()
        if collector:
            fields = [c[0] for c in collector]
            settings = collector[0][1]
            inputs = collector[0][2]
            states = collector[0][3]
            getter_args = collector[0][4]
            _register_group_callback(fields, settings, inputs, states, getter_args)

class EditableField(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    field_path: str
    getter_func: Callable[..., Any] = Field(default=default_getter)
    update_func: Callable[..., None] = Field(default=default_updater)
    # applies_to_... is used for compatibility with DataEditorDataViewCustom
    applies_to_tables: list[str] = Field(default_factory=list)
    applies_to_forms: list[str] = Field(default_factory=list)
    variabel_trigger: str = "n_blur"

    @computed_field
    @property
    def _id(self) -> str:
        return (
            self.field_path + str(self.applies_to_tables) + str(self.applies_to_forms)
        )

    def __str__(self) -> str:
        parts = [f"EditableField(path='{self.field_path}')"]
        parts.append(f"id={self._id}")

        # Functions
        parts.append(
            f"getter={getattr(self.getter_func, '__name__', str(self.getter_func))}"
        )
        parts.append(
            f"updater={getattr(self.update_func, '__name__', str(self.update_func))}"
        )

        # Guards
        if self.applies_to_tables or self.applies_to_forms:
            parts.append(f"applies to tables={self.applies_to_tables}")
            parts.append(f"applies to forms={self.applies_to_forms}")

        return " | ".join(parts)

    def _build_guard_states(self, settings: CallbackSettings) -> list[State]:
        guard_states = []
        if settings.table_selector_id:
            guard_states.append(State(settings.table_selector_id, "value"))
        if settings.form_selector_id:
            guard_states.append(State(settings.form_selector_id, "value"))
        return guard_states

    def _check_guard(
        self, settings: CallbackSettings, *guard_values: list[Any]
    ) -> bool:
        """Returns True if the guard passes (i.e. we should proceed)."""
        idx = 0
        if settings.table_selector_id and self.applies_to_tables:
            if guard_values[idx] not in self.applies_to_tables:
                return False
            idx += 1
        if settings.form_selector_id and self.applies_to_forms:
            current_form = guard_values[idx]
            if current_form not in self.applies_to_forms and (
                current_form is not None or None not in self.applies_to_forms
            ):
                return False
        return True

    def create_callback(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list[Any] = None,
    ) -> None:
        # guard_states = self._build_guard_states(settings)
        variableselector = VariableSelector(
            selected_inputs=[], selected_states=["ident", "altinnskjema"]
        )

        if _collect_stack:
            # if inside batch_editable_fields() block, batch right away instead of registering
            _collect_stack[-1].append((self, settings, inputs, states, getter_args))
            return
        # else, register a group of just one field
        _register_group_callback([self], settings, inputs, states, getter_args)
        
def _register_group_callback(
    fields: list[EditableField],
    settings: CallbackSettings,
    inputs: list[Input] | None,
    states: list[State] | None,
    getter_args: list[Any] | None,
) -> None:
    """Register one populate/edit callback (+ one variabel callback) for a
    group of fields. Works identically whether ``fields`` has 1 entry
    (a standalone field) or many (a batched microlayout) -- there is only
    ever this one registration path.
    """
    inputs = inputs or []
    states = states or []
    getter_args = list(getter_args or [])
    field_ids = [f._id for f in fields]
 
    # table_selector_id / form_selector_id live on `settings`, which every
    # field in the group shares -- so one set of guard States covers all of them
    guard_states = fields[0]._build_guard_states(settings)
 
    variableselector = VariableSelector(
        selected_inputs=[], selected_states=["ident", "altinnskjema"]
    )
 
    n, m, s, g = len(fields), len(inputs), len(states), len(guard_states)
 
    @callback(
        *[Output(fid, "value", allow_duplicate=True) for fid in field_ids],
        Output("alert_store", "data", allow_duplicate=True),
        Output("skjemamottak-status-signal", "data", allow_duplicate=True),
        Input(settings.form_reference_input_id, "value"),
        variableselector.get_state("ident"),
        variableselector.get_state("altinnskjema"),
        *[Input(fid, "value") for fid in field_ids],
        *inputs,
        *states,
        *getter_args,
        *guard_states,
        State("alert_store", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def populate_or_edit(
            refnr: str, ident: str, skjema: str, *args: Any
        ):

        field_values = args[:n]
        remainder = args[n:]

        alert_log = remainder[-1]

        if g:
            guard_values = remainder[-(g + 1):-1]
            real_args = remainder[:-(g + 1)]
        else:
            guard_values = ()
            real_args = remainder[:-1]

        time_unit_values = real_args[:m]
        extra_state_values = real_args[m:m + s]
        getter_arg_values = real_args[m + s:]

        time_units = dict(zip(get_time_units().keys(), time_unit_values))
        extra_args = [*time_unit_values, *extra_state_values, *getter_arg_values]
 
        triggered_id = ctx.triggered_id
 
        if triggered_id in field_ids:
            idx = field_ids.index(triggered_id)
            f = fields[idx]
            if not f._check_guard(settings, *guard_values):
                logger.debug("Preventing update")
                raise PreventUpdate
 
            alert = _run_field(
                f,
                edited=True,
                value=field_values[idx],
                refnr=refnr,
                ident=ident,
                skjema=skjema,
                settings=settings,
                time_units=time_units,
                extra_args=extra_args,
            )
            alert_log = _extend_alert_log(alert_log, alert)
            return (*([no_update] * n), alert_log, time.time())
 
        # Populate path: refnr / time-unit change / initial load -> fetch
        # every field whose own guard currently passes; leave the rest
        # (no_update) untouched.
        results: list[Any] = []
        for f in fields:
            if not f._check_guard(settings, *guard_values):
                results.append(no_update)
                continue
            results.append(
                _run_field(
                    f,
                    edited=False,
                    value=None,
                    refnr=refnr,
                    ident=ident,
                    skjema=skjema,
                    settings=settings,
                    time_units=time_units,
                    extra_args=extra_args,
                )
            )
        return (*results, no_update, no_update)
 
    triggers = [Input(f._id, f.variabel_trigger) for f in fields]
 
    @callback(
        variableselector.get_output_object("variabel"),
        *triggers,
        prevent_initial_call=True,
    )
    def update_variabel(*_vals: Any):
        tid = ctx.triggered_id
        for f in fields:
            if f._id == tid:
                return f.field_path
        raise PreventUpdate
 
    logger.info(
        "Registered callback for %d field(s) (table=%s)",
        len(fields),
        settings.form_data_table,
    )