import logging
from typing import Any
import uuid
from dash import Input, callback, ctx
from dash import State
from dash import html
from dash.exceptions import PreventUpdate

from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_ident, get_refnr
from ssb_dash_framework.utils.core_models import UpdateSkjemadata, UpdateSkjemamottak

from .microlayout_components.models import Layout
from ...meta import FetcherMeta
from ...utils import EditorSettings
logger = logging.getLogger(__name__)


class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    def __init__(
        self,
        layout: list[dict] | dict | Layout,
        settings: EditorSettings,
        data_handler: FetcherMeta,
        inputs: list[Input] | dict[Any, Input] | None = None,
        states: list[State] | None = None,
        aio_id: str | None = None,
        horizontal: bool = False,
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )
        # The below is just for the __str__ dunder
        self.settings = settings
        self._horizontal = horizontal
        inputs = [] if inputs is None else inputs
        # The above is just for the __str__ dunder
        self.variableselector = VariableSelector([], [])
        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        elif isinstance(layout, dict):
            print("MicrolayoutAio", layout)
            #self.settings.form_data_tables
            model = Layout(layout["layout"])
        else:
            model = Layout(layout)
        self._model = model  # Just for __str__ dunder

        styles = {}

        if horizontal:
            styles["display"] = "flex"

        layout, ids = model.build(data_handler, settings)
        super().__init__(
            layout, id=f"{self.aio_id}-klass", style=styles  # pyright: ignore
        )

        callback_ctx = {item._id: item for item in ids}
        if len(ids):
            if isinstance(inputs, list):
                input_states = [
                    State(_input.component_id, "value") for _input in inputs
                ]
            elif isinstance(inputs, dict):
                input_states = {
                    key: State(_input.component_id, "value")
                    for key, _input in inputs.items()
                }

            @callback(
                inputs={
                    "fields": {item._id: item.get_input() for item in ids},
                    "refnr": self.variableselector.get_state(get_refnr()),
                    "ident": self.variableselector.get_state(get_ident()),
                    "custom_inputs": input_states,
                },
                prevent_initial_call=True,
            )
            def handle_field_value_change(
                fields: dict[str, Any],
                refnr: str | None,
                ident: str | None,
                custom_inputs: list | None,
            ):
                if not refnr or not ident or not custom_inputs:
                    raise PreventUpdate

                if ctx.triggered_id:
                    custom_ctx = callback_ctx.get(ctx.triggered_id)
                    value = fields.get(ctx.triggered_id)
                    if not custom_ctx or not value:
                        logger.debug(
                            "Skippping form value update since triggered id was none or it didn't match any fields"
                        )
                        raise PreventUpdate

                    old_value = data_handler.get_field(
                        self.settings, custom_ctx, custom_inputs
                    )
                    long = settings.field_name_col == "variabel"

                    update_form = UpdateSkjemadata(
                        table=self.settings.form_data_table,
                        identifier_column=self.settings.refnr_col,
                        refnr=refnr,
                        ident=ident,
                        column=self.settings.field_value_col,
                        value=value,
                        old_value=old_value,
                        variable=custom_ctx.settings.variable,
                        long=long,
                        mapping_table=settings.mapping_table,
                        mapping_match_column=settings.mapping_match_column,
                        mapping_result_column=settings.mapping_result_column,
                    )

                    update_skjemamottak = UpdateSkjemamottak(
                        refnr=refnr,
                        column="status",
                        value="Under arbeid",
                        on_skjemadata_update=True,
                    )

            # updated_value = fields[ctx.triggered_id]

        @callback(
            output={item._id: item.get_output() for item in ids},
            inputs={
                "custom_inputs": inputs,
            },
        )
        def handle_variable_selector_change(custom_inputs):
            # print("hei", custom_inputs, variable_selector)
            field_values = {}
            # print("custom_inputs", custom_inputs)
            for id_, field in callback_ctx.items():
                field_val = data_handler.get_field(self.settings, field, custom_inputs)
                field_values[id_] = field_val
            return field_values
