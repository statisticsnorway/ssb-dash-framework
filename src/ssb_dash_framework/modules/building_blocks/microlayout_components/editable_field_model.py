import logging
from collections.abc import Callable
from typing import Any

from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import no_update
from dash.exceptions import PreventUpdate
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

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


def defult_getter(refnr: str, settings: CallbackSettings, field_path: str, *args: list[Any]) -> Any:
    logger.debug(f"Getting {field_path} for refnr: {refnr}")
    time_unit_keys = list(get_time_units().keys())
    time_units = dict(zip(time_unit_keys, args))
    
    with get_connection() as conn:
        t = conn.table(settings.form_data_table)
        filters = [
            t[settings.form_reference_number_column] == refnr,
            t[settings.formdata_fieldname_column] == field_path,
        ]
        if settings.form_reference_number_column != "refnr": # ignore time_units filter if refnr is used
            for unit, value in time_units.items():
                if value and unit in t.columns:
                    filters.append(t[unit] == value)
        res = t.filter(filters).select(settings.formdata_field_value_column_name).to_pandas()
    logger.debug(f"Returning:\n{res}") 
    # return res
    if res.empty:
        return None
    return res.iloc[0, 0]


def default_updater(
    value: Any, refnr: str, settings: CallbackSettings, field_path: str, *args: list[Any]
) -> None:
    logger.debug(f"Updating {field_path}")
    time_unit_keys = list(get_time_units().keys())
    time_units = dict(zip(time_unit_keys, args))

    if isinstance(value, list): # checkbox-handler
        value = value[0] if value else "0"

    time_filters = ""
    if settings.form_reference_number_column != "refnr": # ignore time_units filter if refnr is used
        time_filters = " ".join([
            f"AND {unit} = '{val}'" 
            for unit, val in time_units.items() 
            if val
        ])

    try:
        with (
            get_connection() as conn
        ):  
            query = f"""
                UPDATE {settings.form_data_table}
                SET {settings.formdata_field_value_column_name} = '{value}'
                WHERE {settings.form_reference_number_column} = '{refnr}' 
                AND {settings.formdata_fieldname_column} = '{field_path}'
                {time_filters}
            """
            conn.raw_sql(query)
            logger.info(query)
            return create_alert(
                f"Oppdaterte {field_path} til {value} for {refnr} i {settings.form_data_table}!",
                color="success",
                ephemeral=True,
            )
    except Exception as e:
        logger.error(e)
        return create_alert(
            f"Feil ved oppdatering av {field_path}: {e} for {refnr} i {settings.form_data_table}",
            color="danger",
            ephemeral=True,
        )


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
        return self.field_path + str(self.applies_to_tables) + str(self.applies_to_forms)

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

    def _check_guard(self, settings: CallbackSettings, *guard_values: list[Any]) -> bool:
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

        @callback(
            Output(self._id, "value", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(settings.form_reference_input_id, "value"),
            Input(self._id, "value"),
            *inputs if inputs else [],
            *states if states else [],
            *guard_states,
            State("alert_store", "data"),
            prevent_initial_call="initial_duplicate",
        )
        def populate_field(refnr: str, value: Any, *args: list[Any]):
            # Peel guard values off the end of args
            n_guard = len(guard_states)
            alert_log = args[-1]
            guard_values = args[-(n_guard + 1):-1] if n_guard else ()
            real_args = args[:-(n_guard + 1)] if n_guard else args[:-1] # exclude alert_log

            print(f"guard_values={guard_values}, passes guard={self._check_guard(settings, *guard_values)}")

            if not self._check_guard(settings, *guard_values):
                logger.debug("Preventing update")
                raise PreventUpdate

            if ctx.triggered_id == self._id:
                # field was edited by user
                alert = self.update_func(
                    value,
                    refnr,
                    settings,
                    self.field_path,
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
                    *real_args,
                    *getter_args if getter_args else [],
                )
                logger.info(f"getter returned {result!r} for {self.field_path}, refnr={refnr}")
                return result, no_update

