from __future__ import annotations

from typing import Annotated, Any
from typing import Literal
from typing import Sequence
import uuid
import dash_bootstrap_components as dbc
from dash import dcc
from dash import Input
from dash import State
from dash import Output
from dash import html
from dash import callback
from klass import get_classification
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import TypeAdapter
from pydantic import computed_field

from .editable_field_model import EditableField

from abc import ABC, abstractmethod

class FieldCallbackContainer(BaseModel):
    settings: EditableField
    parent_hash: str

    def get_state(self):
        return State(self._id, "value")

    def get_input(self):
        return Input(self._id, self.settings.variabel_trigger)

    def get_output(self):
        return Output(self._id, "value")

    @computed_field
    @property
    def _id(self) -> str:
        return self.settings.field_path + "_" + self.parent_hash


class Base(ABC):
    @abstractmethod
    def create(self) -> tuple[Any, list[FieldCallbackContainer] | FieldCallbackContainer | None]: ...


# ---------- Base + shared ----------
class BaseNode(BaseModel, Base):
    # Discriminator field
    type: str

    # Allow future/unknown keys to pass through without breaking
    model_config = ConfigDict(extra="allow", frozen=True)


class ContainerNode(BaseNode):
    # Recursive children: a list of Nodes (defined later via Union)
    children: list[Node] = Field(default_factory=list)


# ---------- Concrete node types ----------
class Row(ContainerNode):
    type: Literal["row"]

    def create(
        self,
    ) -> tuple[dbc.Row, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create()
            ids.append(_id)
            children.append(comp)
        return dbc.Row(children), ids


class Col(ContainerNode):
    type: Literal["col"]

    def create(
        self,
    ) -> tuple[dbc.Col, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create()
            ids.append(_id)
            children.append(comp)
        return dbc.Col(children), ids


class Tab(ContainerNode):
    type: Literal["tab"]
    label: str

    def create(
        self,
    ) -> tuple[dbc.Tab, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create()
            ids.append(_id)
            children.append(comp)
        return (
            dbc.Tab(
                children,
                label=self.label,
            ),
            ids,
        )


class Tabs(ContainerNode):
    type: Literal["tabs"]
    tabs: list[Tab]

    def create(
        self,
    ) -> tuple[dbc.Tabs, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create()
            ids.append(_id)
            children.append(comp)
        return dbc.Tabs(children), ids


class Header(BaseNode):
    type: Literal["header"]
    label: str
    size: Literal["xs", "sm", "md", "lg"] = "md"

    def create(
        self,
    ) -> tuple[html.H1 | html.H2 | html.H3 | html.H4, None]:
        """A method for creating the layout."""
        if self.size == "lg":
            return html.H1(self.label), None
        elif self.size == "md":
            return html.H2(self.label), None
        elif self.size == "sm":
            return html.H3(self.label), None
        else:
            return html.H4(self.label), None


class Label(BaseNode):
    type: Literal["label"]
    label: str = ""  # acts as a placeholder if not specified
    bold: bool = False

    def create(
        self,
    ) -> tuple[html.Div, None]:
        return (
            html.Div(
                html.Label(
                    self.label if self.label else "\u00a0",
                    style={"fontWeight": "bold" if self.bold else "normal"},
                ),
                className="microlayout-label",
            ),
            None,
        )


class InputField(BaseNode):
    type: Literal["input"]
    label: str
    value: str | None = ""
    hidelabel: bool = False
    readonly: bool = False
    field_settings: EditableField

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = FieldCallbackContainer(settings=self.field_settings, parent_hash=str(uuid.uuid4()))
        return (
            html.Div(
                [
                    html.Label(
                        self.label,
                        title=self.label,
                        style={
                            "visibility": "hidden" if self.hidelabel else "visible",
                        },
                    ),
                    dbc.Input(
                        style={"width": "100%"},
                        id=callback_info._id,
                        debounce=True,
                        readonly=self.readonly,
                        className="microlayout-input-field"
                        + (" microlayout-input-readonly" if self.readonly else ""),
                    ),
                ],
                className="ssb-input",
            ),
            callback_info,
        )


class CalculatedField(BaseNode):
    type: Literal["calculated-field"]
    field_settings: EditableField
    label: str
    hidelabel: bool = False
    decimals: int = 1
    applies_to_tables: list[str] = Field(default_factory=list)
    applies_to_forms: list[str] = Field(default_factory=list)
    exponents: list[str | InputField | int | float] = Field(default_factory=list)
    multiplication: list[str | InputField | int | float] = Field(default_factory=list)
    division: list[str | InputField | int | float] = Field(default_factory=list)
    addition: list[str | InputField | int | float] = Field(default_factory=list)
    subtraction: list[str | InputField | int | float] = Field(default_factory=list)

    @computed_field
    @property
    def _id(self) -> str:
        return self.label + str(self.applies_to_tables) + str(self.applies_to_forms)

    def _get_all_ids(self) -> list[tuple[str, str]]:
        """
        Returns (operation, _id) pairs for all entries, resolving InputField to its _id.
        Numeric entries are returned as-is (float), others as string IDs.
        """
        result = []
        for op, fields in [
            ("exponent", self.exponents),
            ("multiplication", self.multiplication),
            ("division", self.division),
            ("addition", self.addition),
            ("subtraction", self.subtraction),
        ]:
            for f in fields:
                if isinstance(f, (int, float)):
                    result.append((op, float(f)))  # literal number
                elif isinstance(f, InputField):
                    result.append((op, f.field_settings._id))
                else:
                    result.append(
                        (
                            op,
                            f
                            + str(self.applies_to_tables)
                            + str(self.applies_to_forms),
                        )
                    )
        return result

    def _calculate(
        self, op_id_pairs: Sequence[tuple[str, str]], values: list[float | int | None]
    ) -> float:
        """Applies operations in order: exponents → multiply → divide → add → subtract."""
        op_values: dict[str, list[float]] = {
            "exponent": [],
            "multiplication": [],
            "division": [],
            "addition": [],
            "subtraction": [],
        }
        incomplete_multiplicative = (
            False  # handles missing -> 0 for multiplication & division
        )

        for (op, _), value in zip(op_id_pairs, values):
            if value is not None and str(value).strip() != "":
                fval = float(value)
                if op == "division" and fval == 0:
                    incomplete_multiplicative = True
                else:
                    op_values[op].append(fval)
            elif op in ("multiplication", "division", "exponent"):
                incomplete_multiplicative = True

        if incomplete_multiplicative:
            return 0.0

        if op_values["multiplication"] or op_values["division"]:
            result = 1.0
            for val in op_values["multiplication"]:
                result *= val
            for val in op_values["division"]:
                result /= val
            # apply addition/subtraction on top
            for val in op_values["addition"]:
                result += val
            for val in op_values["subtraction"]:
                result -= val
        else:
            result = 0.0
            for val in op_values["addition"]:
                result += val
            for val in op_values["subtraction"]:
                result -= val

        return result

    def create_callback(self) -> None:
        op_id_pairs = self._get_all_ids()
        if not op_id_pairs:
            return

        dynamic_pairs = [(op, id_) for op, id_ in op_id_pairs if isinstance(id_, str)]
        inputs = [Input(id_, "value") for _, id_ in dynamic_pairs]

        @callback(
            Output(self._id, "value"),
            inputs,
        )
        def calculated_callback(*values):
            try:
                if all(v is None for v in values):
                    return f"{0:.{self.decimals}f}"

                value_iter = iter(values)
                resolved: Sequence[tuple[str, float | None]] = []
                for op, id_ in op_id_pairs:
                    if isinstance(id_, float):
                        resolved.append((op, id_))
                    else:
                        resolved.append((op, next(value_iter)))
                result = self._calculate(resolved, [v for _, v in resolved])
                return f"{result:.{self.decimals}f}"
            except Exception as e:
                return f"Error: {e}"

    def create(self, *args, **kwargs) -> html.Div:
        self.create_callback()
        return html.Div(
            [
                html.Label(
                    self.label,
                    title=", ".join(str(id_) for _, id_ in self._get_all_ids()),
                    style={
                        "visibility": "hidden" if self.hidelabel else "visible",
                    },
                ),
                dbc.Input(
                    id=self._id,
                    style={"width": "100%"},
                    readonly=True,
                    className="microlayout-input-readonly",
                ),
            ],
            className="ssb-input",
        )

    def __str__(self, prefix: str = "", is_last: bool = True) -> str:
        branch = "└─ " if is_last else "├─ "
        node_name = self.type.upper()

        def fmt(fields):
            return [
                f.field_settings._id if isinstance(f, InputField) else str(f)
                for f in fields
            ]

        parts = []
        if self.exponents:
            parts.append(f"exp({', '.join(fmt(self.exponents))})")
        if self.multiplication:
            parts.append(" * ".join(fmt(self.multiplication)))
        if self.division:
            parts.append(" / ".join(fmt(self.division)))
        if self.addition:
            parts.append(" + ".join(fmt(self.addition)))
        if self.subtraction:
            parts.append(" - ".join(fmt(self.subtraction)))

        formula = " ".join(parts) if parts else "∅"

        print(
            f"{prefix}{branch}{node_name} ({self.label}, formula={formula}, id={self._id})"
        )
        return f"{prefix}{branch}{node_name} ({self.label}, formula={formula}, id={self._id})"


class DropdownComponent(BaseNode):
    """A class describing the dropdown type."""

    field_settings: EditableField
    type: Literal["dropdown"]
    label: str
    options: list[dict]

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = FieldCallbackContainer(settings=self.field_settings, parent_hash=str(uuid.uuid4()))

        return (
            html.Div(
                [
                    html.Label(self.label, title=self.label),
                    dcc.Dropdown(
                        options=self.options,
                        id=callback_info._id,
                        searchable=False,
                        className="ssb-dropdown",
                    ),  # pyright: ignore
                ],
                className="ssb-input",
            ),
            callback_info,
        )


class ChecklistComponent(BaseNode):
    """A class describing the checklist type."""

    field_settings: EditableField
    type: Literal["checklist"]
    label: str
    hidelabel: bool = False
    options: list[dict]

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = FieldCallbackContainer(settings=self.field_settings, parent_hash=str(uuid.uuid4()))
        if len(self.options) == 1:
            children = [
                dcc.Checklist(
                    options=[{**opt, "label": ""} for opt in self.options],
                    id=callback_info._id,
                ),
                html.Label(
                    self.options[0].get("label", ""),
                    className="mb-1 ms-2",
                ),
            ]
        else:
            children = [
                dcc.Checklist(
                    options=self.options,
                    id=callback_info._id,
                ),
            ]

        return (
            html.Div(
                [
                    html.Label(
                        self.label,
                        title=self.label,
                        style={"visibility": "hidden" if self.hidelabel else "visible"},
                    ),
                    html.Div(
                        className="ssb-checkbox d-flex align-items-center",
                        children=children,
                        style={"height": "44px"},  # to match ssb-input
                    ),
                ],
                className="ssb-input",
            ),
            callback_info,
        )


class KlassDropdown(BaseNode):
    type: Literal["klass-dropdown"]
    klass_code: str
    label: str
    field_settings: EditableField

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
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
        ).create()


# (Optional) If you plan to use these later, keep them here for completeness
class Textarea(BaseNode):
    type: Literal["textarea"]
    label: str
    hidelabel: bool = False
    value: str | None = ""
    readonly: bool = False
    field_settings: EditableField

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = FieldCallbackContainer(settings=self.field_settings, parent_hash=str(uuid.uuid4()))
        return html.Div(
            [
                html.Label(
                    self.label,
                    title=self.label,
                    style={
                        "visibility": "hidden" if self.hidelabel else "visible",
                    },
                    className="ssb-input",
                ),
                dbc.Textarea(
                    style={"width": "100%"},
                    id=callback_info._id,
                    debounce=True,
                    readonly=self.readonly,
                    className="microlayout-textarea-field"
                    + (" microlayout-textarea-readonly" if self.readonly else ""),
                ),
            ],
            className="microlayout-textarea",
        ), callback_info


class KlassChecklist(BaseNode):
    type: Literal["klass-checklist"]
    klass_code: str
    label: str
    field_settings: EditableField

    def create(
        self,
    ) -> tuple[html.Div, FieldCallbackContainer]:
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
            ).create()
        else:
            return DropdownComponent(
                type="dropdown",
                label=self.label,
                options=options,
                field_settings=self.field_settings,
            ).create()


# ---------- Discriminated union (by 'type') ----------
Node = Annotated[
    Row
    | Col
    | Header
    | Label
    | InputField
    | CalculatedField
    | KlassDropdown
    | Textarea
    | KlassChecklist
    | ChecklistComponent
    | DropdownComponent
    | Tabs
    | Tab,
    Field(discriminator="type"),
]

# Optional: trigger forward-ref resolution (usually not required with __future__ annotations)
for m in (
    Row,
    Col,
    Header,
    Label,
    InputField,
    KlassDropdown,
    Textarea,
    KlassChecklist,
    ChecklistComponent,
    DropdownComponent,
    Tabs,
    Tab,
):
    m.model_rebuild()

NodeListAdapter = TypeAdapter(list[Node])

def _flatten_ids(data: Sequence[FieldCallbackContainer | None | Sequence[FieldCallbackContainer]]) -> Sequence[FieldCallbackContainer]:

    return_data = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                return_data += _flatten_ids(item)
            elif item is not None:
                return_data.append(item)
            
        return return_data
    elif data is not None:
        return_data.append(data)
    
    return return_data

class Layout:
    def __init__(self, data: list) -> None:
        parsed_nodes: list[Node] = NodeListAdapter.validate_python(data)
        self.nodes = parsed_nodes

    def build(
        self,
    ) -> tuple[list[Any], Sequence[FieldCallbackContainer]]:
        layout_list = []
        ids = []
        for node in self.nodes:
            layout, id_ = node.create()
            layout_list.append(layout)
            ids.append(id_)
        
        return layout_list, _flatten_ids(ids)
