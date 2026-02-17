import logging
import uuid
from collections.abc import Callable
from typing import Any
from typing import Literal

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import html
from dash.exceptions import PreventUpdate
from klass import get_classification  # Import the utility-function
from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class InputField(BaseModel):
    """A class describing the input type."""

    type_: Literal["input"] = Field(alias="type")
    label: str

    # value: str
    def create(self) -> tuple[html.Div, str]:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        return (
            html.Div(
                [
                    dbc.Label(self.label),
                    dbc.Input(style={"width": "100%"}, id=_id, debounce=True),
                ]
            ),
            _id,
        )


class TextArea(BaseModel):
    """A class describing the textarea type."""

    type_: Literal["textarea"] = Field(alias="type")
    label: str
    # value: str

    def create(self) -> tuple[html.Div, str]:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        return (
            html.Div(
                [
                    dbc.Label(self.label),
                    dbc.Textarea(style={"width": "100%"}, id=_id, debounce=True),
                ]
            ),
            _id,
        )


class Heading(BaseModel):
    """A class describing the header type."""

    type_: Literal["header"] = Field(alias="type")
    label: str
    size: Literal["sm", "md", "lg"] = "md"

    def create(
        self,
    ) -> tuple[html.H1, None] | tuple[html.H2, None] | tuple[html.H3, None]:
        """A method for creating the layout."""
        if self.size == "lg":
            return html.H1(self.label), None
        elif self.size == "md":
            return html.H2(self.label), None
        else:
            return html.H3(self.label), None


class DropdownComponent(BaseModel):
    """A class describing the dropdown type."""

    type_: Literal["dropdown"] = Field(alias="type")
    label: str
    options: list[dict]

    def create(self) -> tuple[html.Div, str]:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        return (
            html.Div(
                [
                    dbc.Label(self.label),
                    dbc.Select(
                        options=self.options, id=_id, style={"width": "100%"}
                    ),  # pyright: ignore
                ]
            ),
            _id,
        )


class ChecklistComponent(BaseModel):
    """A class describing the checklist type."""

    type_: Literal["checklist"] = Field(alias="type")
    label: str
    options: list[dict]

    def create(self) -> tuple[html.Div, str]:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        return (
            html.Div(
                [
                    dbc.Label(self.label),
                    dbc.Checklist(
                        options=self.options, switch=False, id=_id
                    ),  # pyright: ignore
                ],
                style={"display": "block"},
            ),
            _id,
        )


class KlassCode(BaseModel):
    """A class describing the base class for klass-dropdown and klass-checklist."""

    type_: Literal["klass-dropdown", "klass-checklist"] = Field(alias="type")
    label: str
    klass_code: str

    def create(self) -> tuple[html.Div, str]:
        """A method for creating the layout."""
        codes_dict = get_classification(self.klass_code).get_codes().to_dict()
        options = []
        for key, value in codes_dict.items():
            options.append({"label": value, "value": key})

        if self.type_ == "klass-checklist":
            return ChecklistComponent(
                type="checklist", label=self.label, options=options
            ).create()
        else:
            return DropdownComponent(
                type="dropdown", label=self.label, options=options
            ).create()


class Layout(BaseModel):
    """A class for validating the layout."""

    layout: list[
        InputField
        | TextArea
        | KlassCode
        | ChecklistComponent
        | DropdownComponent
        | Heading
    ]


def create_html_layout(
    layout: Layout,
) -> tuple[list[html.Div | html.H1 | html.H2 | html.H3], list[str | None]]:
    """A utility function for iterating through the layout and creating the components and ids."""
    layout_list = []
    layout_ids = []
    for item in layout.layout:
        html_item, _id = item.create()
        layout_list.append(html_item)
        layout_ids.append(_id)
    return layout_list, layout_ids


class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    class Ids:
        """Internal class for handling ID-creation."""

        @staticmethod
        def input_entry() -> dict[str, str]:
            """Method for creating id for input entries."""
            return {
                "component": "LayoutAIO",
            }

    ids = Ids

    def __init__(
        self,
        layout: list[dict] | Layout,
        getter_func: Callable[..., tuple],
        update_func: Callable[..., tuple | None],
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
        aio_id: str | None = None,
        horizontal: bool = False,
    ) -> None:
        """Below is a comprehensive example of how the class should be used.

        Example:
            ```
            editing_layout = [
                {"type": "header", "label": "input"},
                {"type": "textarea", "label": "area", "value": ""},
                {"type": "input", "label": "entry", "value": ""},
                {"type": "klass-dropdown", "klass_code": "689", "label": "dropdown"},
                {"type": "klass-checklist", "klass_code": "689", "label": "checklist"},
                {
                    "type": "checklist",
                    "label": "eposter",
                    "options": [
                        {"label": "tusenfeil", "value": "tusenfeil"},
                        {"label": "orgnrfeil", "value": "orgnrfeil"},
                    ],
                },
            ]

            def getter_func(variable_1: str):
                return area, entry, dropdown, checklist

            def update_func(
                    area: str,
                    entry: str,
                    dropdown: str,
                    checklist: list,
                    eposter: list,
                    selected_input: str
                ):
                pass

            MicroLayoutAIO(
                editing_layout,
                getter_func=getter_func,
                update_func=update_func,
                inputs=[Input("dropdown-id-2", "value")],
                states=[],
            )
            ```

        Args:
            layout: Description of `param1`.
            getter_func: This argument is function that is expected to accept all inputs from `inputs`,
                states from `states` and extra `getter_args` in the order that they are supplied.
            update_func: This argument is function that is expected to accept inputs provided in the
                layout (excluding headers), callback inputs provided in `inputs`, states in `states`,
                extra arguments from `getter_args` in the order that they are supplied.
            inputs: A list of the inputs that are supposed to be used by the `update_func` and `getter_func`.
                The inputs are expected to be supplied by VariableSelector.
                The inputs my be an accepted argument in both the `update_func` and `getter_func`
            states: A list of the states that are supposed to be used by the `update_func` and `getter_func`.
                The states are expected to be supplied by VariableSelector.
                The states my be an accepted argument in both the `update_func` and `getter_func`
            getter_args: Extra arguments that are supplied to both the `getter_func` and `update_func` as
                the last n arguments
            aio_id: Explicitly set an id for the component. This id must be unique
            horizontal: Should be True if sub elements should stack horizontally instead of vertically

        """
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )
        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        else:
            model = Layout.model_validate({"layout": layout})

        html_layout, ids = create_html_layout(model)
        html_inputs = [Input(x, "value") for x in ids if x is not None]
        html_outputs = [Output(x, "value") for x in ids if x is not None]

        if getter_args:
            extra_args = getter_args
        else:
            extra_args = []

        styles = {}

        if horizontal:
            styles["display"] = "flex"

        super().__init__(html_layout, id=f"{self.aio_id}-klass", style=styles)

        @callback(
            *html_outputs,
            *html_inputs,
            *inputs if inputs else [],
            *states if states else [],
            prevent_initial_call=True,
        )
        def handle_update(*args: tuple[Any, ...]):
            if ctx.triggered_id in ids:
                update_func(*args, *extra_args)
                raise PreventUpdate()
            else:
                return getter_func(*args[len(html_inputs) :], *extra_args)

        # These attributes are only used for testing and should not be accessed externally
        self._callback_func = handle_update
        self._html_inputs = html_inputs
