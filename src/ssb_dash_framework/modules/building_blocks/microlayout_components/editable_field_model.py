from ibis.expr.types.relations import Table

import logging
from collections.abc import Callable
from pandas.core.series import Series
from typing import Any
from ibis.expr.types.relations import Table
from functools import cache
from ibis import Table
from dataclasses import dataclass
import time

from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import no_update
from dash.exceptions import PreventUpdate
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from sqlalchemy import text

from ssb_dash_framework.setup import VariableSelector
from ....utils.core_models import UpdateSkjemadata
from ....utils.config_tools.connection import _get_connection_object
from ....utils.alert_handler import create_alert
from ....utils.config_tools.connection import get_connection
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

logger = logging.getLogger(__name__)


class CallbackSettings(BaseModel):
    form_data_table: str
    form_reference_input_id: str
    form_reference_number_column: str
    formdata_field_value_column_name: str
    formdata_fieldname_column: str

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
        with get_connection() as conn:
            t = conn.table(settings.form_data_table)
            if (
                settings.form_reference_number_column not in t.columns
            ):  # catch errors with querying from wrong table
                raise ValueError(
                    f"Column '{settings.form_reference_number_column}' not in table "
                    f"'{settings.form_data_table}'. Available: {t.columns}"
                )
            res = t.filter(
                t[settings.form_reference_number_column] == refnr,
            )
        return res

    @classmethod
    def clean_cache(cls):
        max_size = 10
        if len(cls.data.keys()) > max_size:
            key, _ = min(cls.data.items(), key=lambda x: x[1].last_cache_hit)
            cls.data.pop(key)

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
) -> None:
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
    update = UpdateSkjemadata(
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
    )

    if isinstance(_get_connection_object(), ConnectionPool):
        return update.update_ibis(long=long)
    else:
        raise NotImplementedError(
            f"Connection of type '{type(_get_connection_object())}' is not implemented yet."
        )


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
        guard_states = self._build_guard_states(settings)
        variableselector = VariableSelector(
            selected_inputs=[], selected_states=["ident", "altinnskjema"]
        )

        @callback(
            Output(self._id, "value", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(settings.form_reference_input_id, component_property="value"),
            variableselector.get_state("ident"),
            variableselector.get_state("altinnskjema"),
            Input(self._id, "value"),
            *inputs if inputs else [],
            *states if states else [],
            *getter_args if getter_args else [],
            *guard_states,
            State("alert_store", "data"),
            prevent_initial_call="initial_duplicate",
        )
        def populate_field(
            refnr: str, ident: str, skjema: str, value: Any, *args: list[Any]
        ):
            # Peel guard values off the end of args
            n_guard = len(guard_states)
            alert_log = args[-1]
            guard_values = args[-(n_guard + 1) : -1] if n_guard else ()
            real_args = (
                args[: -(n_guard + 1)] if n_guard else args[:-1]
            )  # exclude alert_log

            time_unit_keys = list(get_time_units().keys())
            time_units = dict(zip(time_unit_keys, real_args))

            if not self._check_guard(settings, *guard_values):
                logger.debug("Preventing update")
                raise PreventUpdate

            if ctx.triggered_id == self._id:
                # field was edited by user
                alert = self.update_func(
                    value,
                    skjema,
                    refnr,
                    ident,
                    settings,
                    self.field_path,
                    time_units,
                    *real_args,
                    *getter_args if getter_args else [],
                )
                alert_log = list(alert_log or [])
                if alert:
                    alert_log.append(alert)
                return no_update, alert_log
            else:
                result = self.getter_func(
                    refnr,
                    settings,
                    self.field_path,
                    time_units,
                    *real_args,
                    *getter_args if getter_args else [],
                )
                logger.info(
                    f"getter returned {result!r} for {self.field_path}, refnr={refnr}"
                )
                return result, no_update

        @callback(
            variableselector.get_output_object("variabel"),
            Input(self._id, self.variabel_trigger),
            prevent_initial_call=True,
        )
        def update_variabel(_):
            return self.field_path

        update_variabel.__name__ = f"update_variabel_{self._id}"
