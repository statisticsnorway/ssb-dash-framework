import logging
from typing import Any
import uuid
from dash import Input, callback, ctx
from dash import State
from dash import html
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import CallbackSettings
from ...utils import EditorSettings

from .microlayout_components.models import Layout
from ...meta import FetcherMeta

logger = logging.getLogger(__name__)


class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    def __init__(
        self,
        layout: list[dict] | Layout,
        settings: CallbackSettings,
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

        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        else:
            model = Layout(layout)
        self._model = model  # Just for __str__ dunder

        styles = {}

        if horizontal:
            styles["display"] = "flex"

        layout, ids = model.build()
        super().__init__(
            layout, id=f"{self.aio_id}-klass", style=styles  # pyright: ignore
        )

        callback_ctx = {item._id: item for item in ids}
        if len(ids):
            @callback(
                # output=dict(),
                inputs=dict(fields=dict({item._id: item.get_input() for item in ids})),
                states=dict(),
            )
            def handle_field_value_change(fields: dict[str, Any]):
                print("update", fields)
               # updated_value = fields[ctx.triggered_id]

        @callback(
            output={item._id: item.get_output() for item in ids},
            inputs=dict(
                custom_inputs=inputs,
            ),
            states=dict(),
        )
        def handle_variable_selector_change(custom_inputs):
            # print("hei", custom_inputs, variable_selector)
            field_values = {}
            for id_, field in callback_ctx.items():
                field_val = data_handler.get_field(self.settings, field, custom_inputs)
                field_values[id_] = field_val
            return field_values
