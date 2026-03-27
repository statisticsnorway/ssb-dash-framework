import logging
from collections.abc import Callable

from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash.exceptions import PreventUpdate
from pydantic import BaseModel, ConfigDict
from pydantic import Field
from ssb_dash_framework import get_connection
from ibis import _

logger = logging.getLogger(__name__)


class CallbackSettings(BaseModel):
    form_data_table: str
    form_reference_input_id: str
    form_reference_number_column: str
    formdata_field_value_column_name: str
    formdata_fieldname_column: str


def defult_getter(refnr: str, settings: CallbackSettings, field_path: str, *args):
    with get_connection() as conn:
        t = conn.table(settings.form_data_table)
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
    return res


def default_updater(value, refnr: str, settings: CallbackSettings, field_path: str, *args):
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
    getter_func: Callable = Field(default=defult_getter)
    update_func: Callable = Field(default=default_updater)

    def create_callback(
        self,
        id: str,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ):

        @callback(
            Output(id, "value", allow_duplicate=True),
            Input(settings.form_reference_input_id, "value"),
            *inputs if inputs else [],
            *states if states else [],
            prevent_initial_call="duplicate",
        )
        def populate_field(refnr, *args):
            return self.getter_func(
                refnr,
                settings,
                self.field_path,
                *args,
                *getter_args if getter_args else [],
            )

        inputs_valid = inputs if inputs else []
        inputs_as_state = [
            State(input.component_id, input.component_property)
            for input in inputs_valid
        ]

        @callback(
            Output(id, "value", allow_duplicate=True),
            Input(id, "value"),
            State(settings.form_reference_input_id, "value"),
            *inputs_as_state,
            *states if states else [],
            prevent_initial_call="duplicate",
        )
        def update_field(value, refnr, *args):
            if ctx.triggered_id != id:
                raise PreventUpdate
            self.update_func(
                value,
                refnr,
                settings,
                self.field_path,
                *args,
                *getter_args if getter_args else [],
            )
            raise PreventUpdate

