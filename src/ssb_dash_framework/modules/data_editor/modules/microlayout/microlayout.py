import logging
import uuid
from typing import Any

from dash import Input
from dash import State
from dash import Output
from dash import callback
from dash import ctx
from dash import html
from dash.exceptions import PreventUpdate

from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.utils.alert_handler import AlertHandler

from .meta import MicrolayoutMeta
from ...utils import EditorSettings
from ...utils import EDITING_CODE_DROPDOWN
from dash import no_update
from .microlayout_components.models import Layout

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
        data_handler: MicrolayoutMeta,
        instance_id: str | None,
        inputs: list[Input] | dict[Any, Input] | None = None,
        states: list[State] | None = None,
        aio_id: str | None = None,
        horizontal: bool = False,
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )

        if isinstance(layout, dict):
            override_kwargs = {}
            for key in [
                "form_data_table",
                "field_name_col",
                "refnr_col",
                "ident_col",
                "field_value_col",
                "period_col",
            ]:
                if key in layout:
                    override_kwargs[key] = layout[key]

            if override_kwargs:
                settings = settings.model_copy(update=override_kwargs)

        # The below is just for the __str__ dunder
        self.settings = settings
        self._horizontal = horizontal
        inputs = [] if inputs is None else inputs
        # The above is just for the __str__ dunder
        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        elif isinstance(layout, dict):
            model = Layout(layout["layout"], self.aio_id)
        else:
            model = Layout(layout, self.aio_id)
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
                output={
                    item._id: Output(
                        {"comp_id": item._id, "aio": self.aio_id},
                        "value",
                        allow_duplicate=True,
                    )
                    for item in ids
                },
                inputs={
                    "fields": {item._id: item.get_input(self.aio_id) for item in ids},
                    "refnr": VariableSelector.get_refnr(Input),
                    "skjema": VariableSelector.get_state("altinnskjema"),
                    "ident": VariableSelector.get_ident(State),
                    "period": VariableSelector.get_timevar(State),
                    "custom_inputs": input_states,
                    "editing_code": Input(
                        EDITING_CODE_DROPDOWN(instance_id), "value", allow_optional=True
                    ),
                },
                prevent_initial_call=True,
            )
            def handle_field_value_change(
                fields: dict[str, Any],
                refnr: str | None,
                skjema: str | None,
                ident: str | None,
                period: str,
                custom_inputs: list | None,
                editing_code: str | None = None,
            ):
                if not refnr or not ident or not custom_inputs:
                    raise PreventUpdate

                if isinstance(skjema, list):
                    skjema = skjema[0]
                logger.debug(f"refnr: {refnr}")
                logger.debug(f"ident: {ident}")
                logger.debug(f"skjema: {skjema}")

                if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
                    custom_ctx = callback_ctx.get(ctx.triggered_id["comp_id"])
                    value = fields.get(ctx.triggered_id["comp_id"])

                    if custom_ctx is None or value is None:
                        logger.debug(
                            "Skipping form value update since triggered id was none or it didn't match any fields"
                        )
                        raise PreventUpdate
                    
                    old_value = None
                    try:
                        old_value = data_handler.get_field(
                            self.settings, custom_ctx, custom_inputs
                        )
                        logger.debug(
                            f"Old value in handle_field_value_change: {old_value}"
                        )
                        logger.debug(f"New value in handle_field_value_change: {value}")
                        print(f"old value: {old_value}")
                        print(f"new value: {value}")
                        if old_value != value:
                            data_handler.update_field_value(
                                refnr,
                                skjema,
                                ident,
                                period=period,
                                value=value,
                                old_value=old_value,
                                settings=self.settings,
                                container=custom_ctx,
                                inputs=custom_inputs,
                                editing_code=editing_code,
                            )
                            if self.settings.form_data_table.startswith("skjemadata"): # eller if refnr eller if skjema?
                                data_handler.update_form_status(refnr, "Under arbeid")
                        else:
                            print(
                                "Skipping form value update since value was same as previous value"
                            )
                    except PreventUpdate:
                        raise PreventUpdate
                    except Exception as e:
                        msg = f"Updating field value and updating form status for form field {custom_ctx.settings.variable} failed with error: {e}"
                        logger.error(msg)
                        # AlertHandler.warning(msg)
                        triggered_id = ctx.triggered_id["comp_id"]
                        return {
                            id_: old_value if id_ == triggered_id else no_update
                            for id_ in {item._id for item in ids}
                        }  # return old value if edit fails
                    return {item._id: no_update for item in ids}

        @callback(
            output={item._id: item.get_output(self.aio_id) for item in ids},
            inputs={"custom_inputs": inputs},
        )
        def handle_variable_selector_change(custom_inputs, style: dict | None = None):

            field_values = {}
            for id_, field in callback_ctx.items():
                try:
                    field_val = data_handler.get_field(
                        self.settings, field, custom_inputs
                    )
                    field_values[id_] = field_val
                except Exception as e:
                    msg = f"Getting data for form field {field} failed with error: {e}"
                    logger.warning(msg)
                    AlertHandler.warning(msg)
                    # field_values[id_] = no_update

            return field_values
