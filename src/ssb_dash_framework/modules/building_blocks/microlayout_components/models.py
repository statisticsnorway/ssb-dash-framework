from __future__ import annotations

import uuid
from typing import Annotated
from typing import Literal

import dash_bootstrap_components as dbc
from dash import Input
from dash import State
from dash import html
from klass import get_classification
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import TypeAdapter

from .editable_field_model import CallbackSettings
from .editable_field_model import EditableField


# ---------- Base + shared ----------
class BaseNode(BaseModel):
    # Discriminator field
    type: str

    # Allow future/unknown keys to pass through without breaking
    model_config = ConfigDict(extra="allow")

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div | html.H1 | html.H2 | html.H3 | dbc.Row | dbc.Col:
        raise NotImplementedError

    def __str__(self, prefix: str = "", is_last: bool = True) -> str:
        branch = "└─ " if is_last else "├─ "
        node_name = self.type.upper()

        # Container node (has children)
        if hasattr(self, "children") and isinstance(self.children, list):
            lines = [f"{prefix}{branch}{node_name}:"]
            child_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(self.children):
                lines.append(
                    child.__str__(
                        prefix=child_prefix, is_last=(i == len(self.children) - 1)
                    )
                )
            return "\n".join(lines)

        # Leaf node — dynamically include info
        info_parts = []

        # Label if exists
        if hasattr(self, "label"):
            info_parts.append(f"{self.label}")

        # field_path for InputField or similar
        if hasattr(self, "field_settings") and hasattr(
            self.field_settings, "field_path"
        ):
            info_parts.append(f"path={self.field_settings.field_path}")

        # klass_code for KlassDropdown/KlassChecklist
        if hasattr(self, "klass_code"):
            info_parts.append(f"klass_code={self.klass_code}")

        # size for Header
        if hasattr(self, "size"):
            info_parts.append(f"size={self.size}")

        info_str = " (" + ", ".join(info_parts) + ")" if info_parts else ""
        return f"{prefix}{branch}{node_name}{info_str}"


class ContainerNode(BaseNode):
    # Recursive children: a list of Nodes (defined later via Union)
    children: list[Node] = Field(default_factory=list)

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div | html.H1 | html.H2 | html.H3 | dbc.Row | dbc.Col:
        raise NotImplementedError


# ---------- Concrete node types ----------
class Row(ContainerNode):
    type: Literal["row"]

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> dbc.Row:
        """A method for creating the layout."""
        return dbc.Row(
            [
                child.create(
                    settings,
                    inputs,
                    states,
                    getter_args,
                )
                for child in self.children
            ]
        )


class Col(ContainerNode):
    type: Literal["col"]

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> dbc.Col:
        """A method for creating the layout."""
        return dbc.Col(
            [
                child.create(
                    settings,
                    inputs,
                    states,
                    getter_args,
                )
                for child in self.children
            ]
        )


class Header(BaseNode):
    type: Literal["header"]
    label: str

    size: Literal["sm", "md", "lg"] = "md"

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.H1 | html.H2 | html.H3:
        """A method for creating the layout."""
        if self.size == "lg":
            return html.H1(self.label)
        elif self.size == "md":
            return html.H2(self.label)
        else:
            return html.H3(self.label)


class InputField(BaseNode):
    type: Literal["input"]
    label: str
    value: str | None = ""
    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        self.field_settings.create_callback(
            _id,
            settings,
            inputs,
            states,
            getter_args,
        )
        return html.Div(
            [
                dbc.Label(self.label),
                dbc.Input(style={"width": "100%"}, id=_id, debounce=True),
            ]
        )


class DropdownComponent(BaseNode):
    """A class describing the dropdown type."""

    type: Literal["dropdown"]
    label: str
    options: list[dict]
    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        self.field_settings.create_callback(
            _id,
            settings,
            inputs,
            states,
            getter_args,
        )
        return html.Div(
            [
                dbc.Label(self.label),
                dbc.Select(
                    options=self.options, id=_id, style={"width": "100%"}
                ),  # pyright: ignore
            ]
        )


class ChecklistComponent(BaseNode):
    """A class describing the checklist type."""

    type: Literal["checklist"]
    label: str
    options: list[dict]
    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        self.field_settings.create_callback(
            _id,
            settings,
            inputs,
            states,
            getter_args,
        )
        return html.Div(
            [
                dbc.Label(self.label),
                dbc.Checklist(
                    options=self.options, switch=False, id=_id
                ),  # pyright: ignore
            ],
            style={"display": "block"},
        )


class KlassDropdown(BaseNode):
    type: Literal["klass-dropdown"]
    klass_code: str
    label: str

    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        codes_dict = get_classification(self.klass_code).get_codes().to_dict()
        options = []
        for key, value in codes_dict.items():
            options.append({"label": value, "value": key})

        return DropdownComponent(
            type="dropdown",
            label=self.label,
            options=options,
            field_settings=self.field_settings,
        ).create(
            settings,
            inputs,
            states,
            getter_args,
        )


# (Optional) If you plan to use these later, keep them here for completeness
class Textarea(BaseNode):
    type: Literal["textarea"]
    label: str
    value: str | None = ""
    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        _id = str(uuid.uuid4())
        self.field_settings.create_callback(
            _id,
            settings,
            inputs,
            states,
            getter_args,
        )
        return html.Div(
            [
                dbc.Label(self.label),
                dbc.Textarea(style={"width": "100%"}, id=_id, debounce=True),
            ]
        )


class KlassChecklist(BaseNode):
    type: Literal["klass-checklist"]
    klass_code: str
    label: str
    field_settings: EditableField

    def create(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ) -> html.Div:
        """A method for creating the layout."""
        codes_dict = get_classification(self.klass_code).get_codes().to_dict()
        options = []
        for key, value in codes_dict.items():
            options.append({"label": value, "value": key})

        if self.type == "klass-checklist":
            return ChecklistComponent(
                type="checklist",
                label=self.label,
                options=options,
                field_settings=self.field_settings,
            ).create(
                settings,
                inputs,
                states,
                getter_args,
            )
        else:
            return DropdownComponent(
                type="dropdown",
                label=self.label,
                options=options,
                field_settings=self.field_settings,
            ).create(
                settings,
                inputs,
                states,
                getter_args,
            )


"""class ChecklistOption(BaseModel):
    label: str
    value: str


class Checklist(BaseNode):
    type: Literal["checklist"]
    label: str
    options: List[ChecklistOption]

"""
# ---------- Discriminated union (by 'type') ----------
Node = Annotated[
    Row
    | Col
    | Header
    | InputField
    | KlassDropdown
    | Textarea
    | KlassChecklist
    | ChecklistComponent
    | DropdownComponent,
    Field(discriminator="type"),
]

# Optional: trigger forward-ref resolution (usually not required with __future__ annotations)
for m in (
    Row,
    Col,
    Header,
    InputField,
    KlassDropdown,
    Textarea,
    KlassChecklist,
    ChecklistComponent,
    DropdownComponent,
):
    m.model_rebuild()

NodeListAdapter = TypeAdapter(list[Node])


class Layout:
    def __init__(self, data: list) -> None:
        parsed_nodes: list[Node] = NodeListAdapter.validate_python(data)
        self.nodes = parsed_nodes

    def build(
        self,
        settings: CallbackSettings,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
    ):
        layout_list = []
        for node in self.nodes:
            layout = node.create(settings, inputs, states, getter_args)
            layout_list.append(layout)
        return layout_list

    def __str__(self) -> str:
        lines = ["LAYOUT:"]
        for i, node in enumerate(self.nodes):
            lines.append(node.__str__(prefix="", is_last=(i == len(self.nodes) - 1)))
        return "\n".join(lines)
