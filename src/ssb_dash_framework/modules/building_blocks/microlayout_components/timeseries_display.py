from typing import Any
from typing import Callable

import logging
import uuid

import dash_bootstrap_components as dbc
from dash_bootstrap_components import Tab, Tabs
from dash import html
from dash import callback
from dash import Input
from dash import State
from dash import Output
from dash import MATCH

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from ssb_dash_framework.setup import VariableSelector

from .editable_field_model import CallbackSettings

logger = logging.getLogger(__name__)


def default_getter(
    refnr: str,
    settings: CallbackSettings,
    field_path: str,
    time_units: dict,
    *args: list[Any],
) -> Any:
    logger.debug(f"Getting {field_path} for refnr: {refnr}")

class TimeseriesField(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    field_path: str
    getter_func: Callable[..., Any] = Field(default=default_getter)
    # update_func: Callable[..., None] = Field(default=default_updater)
    # applies_to_... is used for compatibility with DataEditorDataViewCustom
    applies_to_tables: list[str] = Field(default_factory=list)
    applies_to_forms: list[str] = Field(default_factory=list)
    variabel_trigger: str = "n_blur"

    @computed_field
    @property
    def _id(self) -> str:
        return (
            "timeseries" + self.field_path + str(self.applies_to_tables) + str(self.applies_to_forms)
        )

    def __str__(self) -> str:
        parts = [f"TimeseriesField(path='{self.field_path}')"]
        parts.append(f"id={self._id}")

        # Functions
        parts.append(
           f"getter={getattr(self.getter_func, '__name__', str(self.getter_func))}"
        )
        # parts.append(
        #    f"updater={getattr(self.update_func, '__name__', str(self.update_func))}"
        # )

        # Guards
        if self.applies_to_tables or self.applies_to_forms:
            parts.append(f"applies to tables={self.applies_to_tables}")
            parts.append(f"applies to forms={self.applies_to_forms}")

        return " | ".join(parts)
        

class TimeSeriesDisplay(html.Div):
    class Ids:
        tabs_id = lambda x: {"aio_id": x, "component": "tabs"}
        graph_view = lambda x: {"aio_id": x, "component": "graph_container"}
        table_view = lambda x: {"aio_id": x, "component": "table_container"}
    
    ids = Ids

    def __init__(
        self,
        settings: CallbackSettings,
        field_settings: TimeseriesField,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list[Any] = None,
        aio_id: str | None = None
    ):
        if aio_id is None:
            aio_id = str(uuid.uuid4())
        graph_view = dbc.Tab( # pyright: ignore[reportCallIssue]
            [],
            label="Graf",
            style={"display": "inline"},
            id=self.ids.graph_view(aio_id)
        )
        table_view = dbc.Tab( # pyright: ignore[reportCallIssue]
            [],
            label="Tabell",
            style={"display": "none"},
            id=self.ids.table_view(aio_id)
        )
        layout = dbc.Tabs([graph_view, table_view], id=self.ids.tabs_id(aio_id)) # pyright: ignore[reportCallIssue]

        super().__init__(children=[layout])

    
        #@callback(Output(self.ids.graph_view(MATCH), "style"), Output(self.ids.table_view(MATCH), "style"), Input())
        variableselector = VariableSelector(
            selected_inputs=[], selected_states=["ident", "altinnskjema"]
        )

        @callback(
            Output(self.ids.graph_view(aio_id), "children", allow_duplicate=True),
            Output(self.ids.table_view(aio_id), "children", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input(settings.form_reference_input_id, component_property="value"),
            variableselector.get_state("ident"),
            variableselector.get_state("altinnskjema"),
            #Input(self._id, "value"),
            *inputs if inputs else [],
            *states if states else [],
            *getter_args if getter_args else [],
            #*guard_states,
            State("alert_store", "data"),
            prevent_initial_call="initial_duplicate",
        )
        def populate_field(
            refnr: str, ident: str, skjema: str, value: Any, *args: list[Any]
        ):
            field_settings.getter_func()
            print("timeseries", refnr, ident, skjema, value)