import logging
from typing import Any
import uuid
from collections.abc import Callable
from abc import abstractmethod, ABC
from dash import Input, callback
from dash import State
from dash import html

from ...utils.config_tools.set_variables import get_ident, get_refnr

# from ssb_dash_framework import VariableSelector
from ...setup.variableselector import VariableSelector

# from .microlayout_components.editable_field_model import CallbackSettings
from .microlayout_components.models import FieldCallbackContainer, Layout

logger = logging.getLogger(__name__)


class FetcherMeta(ABC):
    @abstractmethod
    def get_field(
        self,
        container: FieldCallbackContainer,
        custom_inputs: list[Any],
        variable_selector: list[Any],
    ) -> Any: ...
    
    #@abstractmethod
    #def update_field(self) -> Any:
    #    ...

    #@abstractmethod
    #def get_field_history(self) -> Any:
    #    ...

    #@abstractmethod
    #def get_field_list(self) -> Any:
    #    ...


class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    def __init__(
        self,
        layout: list[dict] | Layout,
        data_handler: FetcherMeta,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        aio_id: str | None = None,
        horizontal: bool = False,
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )
        # The below is just for the __str__ dunder

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
        self.variableselector = VariableSelector([get_ident(), get_refnr()], [])

        layout, ids = model.build()
        super().__init__(
            layout, id=f"{self.aio_id}-klass", style=styles  # pyright: ignore
        )

        callback_ctx = {item._id: item for item in ids}

        @callback(
            # output=dict(),
            inputs=dict(fields=dict({item._id: item.get_input() for item in ids})),
            states=dict(),
        )
        def handle_field_value_change(fields: dict[str, Any]):
            print("update", fields)
            pass

        @callback(
            output={item._id: item.get_output() for item in ids},
            inputs=dict(
                custom_inputs=inputs,
                variable_selector=self.variableselector.get_all_inputs(),
            ),
            states=dict(),
        )
        def handle_variable_selector_change(custom_inputs, variable_selector):
            # print("hei", custom_inputs, variable_selector)
            field_values = {}
            for id_, field in callback_ctx.items():
                field_val = data_handler.get_field(
                    field, custom_inputs, variable_selector
                )
                field_values[id_] = field_val
            return field_values
