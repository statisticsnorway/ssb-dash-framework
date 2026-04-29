from ibis.expr.types.relations import Table


import logging
from collections.abc import Callable
from typing import Any
from functools import cache
import time

from ibis import Table

from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash.exceptions import PreventUpdate
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from ....utils.config_tools.connection import get_connection

logger = logging.getLogger(__name__)


class CallbackSettings(BaseModel):
    form_data_table: str
    form_reference_input_id: str
    form_reference_number_column: str
    formdata_field_value_column_name: str
    formdata_fieldname_column: str

    table_selector_id: str | None = None
    form_selector_id: str | None = None


class FormGetterCached:
    data: Table | None = None
    last_cache_hit: None | float = None

    def __init__(self) -> None:
        pass

    @classmethod
    def get_form(cls, refnr: str, settings: CallbackSettings) -> Table:
        if cls.last_cache_hit and ((time.perf_counter() - cls.last_cache_hit) > 5.0) and cls.data:
            return cls.data

        with get_connection() as conn:
            t = conn.table(settings.form_data_table)
            res = t.filter(
                t[settings.form_reference_number_column] == refnr,
            )
            cls.data = res
            cls.last_cache_hit = time.perf_counter()
            return cls.data


def defult_getter(
    refnr: str, settings: CallbackSettings, field_path: str, *args: list[Any]
) -> Any:
    
    logger.debug(f"Getting {field_path} for refnr: {refnr}")
    t = FormGetterCached.get_form(refnr, settings)
    res = (
        t.filter(
            [
                t[settings.form_reference_number_column] == refnr,
                t[settings.formdata_fieldname_column] == field_path,
            ]
        )
        .select(settings.formdata_field_value_column_name)
        .as_scalar()
        .to_pandas()
    )
    logger.debug(f"Returning:\n{res}")
    return res


def default_updater(
    value: Any,
    refnr: str,
    settings: CallbackSettings,
    field_path: str,
    *args: list[Any],
) -> None:
    logger.debug(f"Updating {field_path}")
    with get_connection() as conn:
        query = f"""
            UPDATE {settings.form_data_table}
            SET {settings.formdata_field_value_column_name} = '{value}'
            WHERE refnr = '{refnr}' AND {settings.formdata_fieldname_column} = '{field_path}'
        """
        conn.raw_sql(query)
        logger.info(query)


class EditableField(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    field_path: str
    getter_func: Callable[..., Any] = Field(default=defult_getter)
    update_func: Callable[..., None] = Field(default=default_updater)
    # applies_to_... is used for compatibility with DataEditorDataViewCustom
    applies_to_tables: list[str] = Field(default_factory=list)
    applies_to_forms: list[str] = Field(default_factory=list)

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
            if guard_values[idx] not in self.applies_to_forms:
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

        @callback(
            Output(self._id, "value", allow_duplicate=True),
            Input(self._id, "value"),
            Input(settings.form_reference_input_id, "value"),
            *inputs if inputs else [],
            *states if states else [],
            *guard_states,
            prevent_initial_call="duplicate",
        )
        def populate_field(value: Any, refnr: str, *args: list[Any]):
            # Peel guard values off the end of args
            n_guard = len(guard_states)
            guard_values = args[-n_guard:] if n_guard else ()
            real_args = args[:-n_guard] if n_guard else args
            if not self._check_guard(settings, *guard_values):
                logger.debug("Preventing update")
                raise PreventUpdate

            if ctx.triggered_id == id:
                self.update_func(
                    value,
                    refnr,
                    settings,
                    self.field_path,
                    *real_args,
                    *getter_args if getter_args else [],
                )
                raise PreventUpdate
            else:
                return self.getter_func(
                    refnr,
                    settings,
                    self.field_path,
                    *real_args,
                    *getter_args if getter_args else [],
                )
