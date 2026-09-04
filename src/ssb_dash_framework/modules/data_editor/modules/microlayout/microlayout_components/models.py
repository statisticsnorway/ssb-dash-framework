# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
from __future__ import annotations

import string
import uuid
from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence
from typing import Annotated
from typing import Any
from typing import Literal

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import clientside_callback
from dash import dcc
from dash import html
from klass import get_classification
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import TypeAdapter
from pydantic import computed_field
from pydantic import model_validator

from ..meta import MicrolayoutMeta
from ....utils import EditorSettings
from .dynamic_list import DynamicListEditor
from .editable_field_model import EditableField
from .editable_field_model import FieldCallbackContainer
from .timeseries_aio import TimeseriesAio


class Base(ABC):
    @abstractmethod
    def create(
        self,
        fetcher: MicrolayoutMeta,  # Fetcher is only included here for components that needs to create their own callbacks
        settings: EditorSettings,
    ) -> tuple[Any, list[FieldCallbackContainer] | FieldCallbackContainer | None]: ...


# ---------- Base + shared ----------
class BaseNode(BaseModel, Base):
    # Discriminator field
    type: str

    # Allow future/unknown keys to pass through without breaking
    model_config = ConfigDict(extra="allow", frozen=True)


class ContainerNode(BaseNode):
    # Recursive children: a list of Nodes (defined later via Union)
    children: list[Node] = Field(default_factory=list)


class ValueNode(BaseNode):
    variable: str
    variable_trigger: str = Field(default="value")
    id: str
    use_variable_as_id: bool = Field(default=True)

    @model_validator(mode="before")
    @classmethod
    def pre_init_id_creation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Mutate the raw input dictionary before validation
            if "id" not in data:
                var_as_is = data.get("use_variable_as_id", True)
                new_id = data.get("variable")
                # if var_as_is == False
                if (new_id is None) or (var_as_is == False) or isinstance(new_id, list):
                    data["id"] = str(uuid.uuid4())
                else:
                    data["id"] = new_id
        return data

    @computed_field
    @property
    def field_settings(self) -> EditableField:
        return EditableField(
            variable=self.variable, variabel_trigger=self.variable_trigger, id=self.id
        )

    @computed_field
    @property
    def callback_settings(self) -> FieldCallbackContainer:
        return FieldCallbackContainer(settings=self.field_settings, parent_id=self.id)


# ---------- Concrete node types ----------
class Row(ContainerNode):
    type: Literal["row"]

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[dbc.Row, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create(fetcher, settings)
            ids.append(_id)
            children.append(comp)
        return dbc.Row(children), ids


class Col(ContainerNode):
    type: Literal["col"]

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[dbc.Col, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create(fetcher, settings)
            ids.append(_id)
            children.append(comp)
        return dbc.Col(children), ids


class Tab(ContainerNode):
    type: Literal["tab"]
    label: str

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[dbc.Tab, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create(fetcher, settings)
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
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[dbc.Tabs, list[FieldCallbackContainer]]:
        """A method for creating the layout."""
        ids = []
        children = []
        for child in self.children:
            comp, _id = child.create(fetcher, settings)
            ids.append(_id)
            children.append(comp)
        return dbc.Tabs(children), ids


class Header(BaseNode):
    type: Literal["header"]
    label: str
    size: Literal["xs", "sm", "md", "lg"] = "md"

    def create(
        self, fetcher: MicrolayoutMeta, _settings: EditorSettings
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
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
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


class InputField(ValueNode):
    type: Literal["input"]
    label: str
    value: str | None = ""
    hidelabel: bool = False
    hidden: bool = False
    readonly: bool = False
    variabel_trigger: str = "n_blur"
    # field_settings: EditableField

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = self.callback_settings
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
                        style={
                            "width": "100%",
                            "visibility": "hidden" if self.hidden else "visible",
                        },
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


class TimeseriesView(ValueNode):
    type: Literal["timeseries"]
    label: str
    num_periods: int
    variable: list[str]
    width: int = Field(default=400)
    use_variable_as_id: bool = Field(default=False)
    switchable: bool = Field(default=True)

    def create(self, fetcher: MicrolayoutMeta, settings: EditorSettings) -> tuple:
        internal_id = str(uuid.uuid4())

        return (
            TimeseriesAio(
                self.variable,
                self.num_periods,
                settings,
                fetcher,
                _id=internal_id,
                width=self.width,
            ),
            None,
        )


class DynamicListView(ValueNode):
    type: Literal["dynamic-list"]
    label: str
    variable: str
    use_variable_as_id: bool = False
    switchable: bool = Field(default=True)

    def create(self, fetcher: MicrolayoutMeta, settings: EditorSettings) -> tuple:
        internal_id = str(uuid.uuid4())

        return (
            DynamicListEditor(fetcher, settings, self.variable, _id=internal_id),
            None,
        )


class CalculatedField(ValueNode):
    type: Literal["calculated-field"]
    label: str
    hidelabel: bool = False
    variable: str = Field(default="")
    decimals: int = 1
    applies_to_tables: list[str] = Field(default_factory=list)
    applies_to_forms: list[str] = Field(default_factory=list)
    expression: str
    ids: dict[str, str]
    # constants: dict[str, str] = Field(default_factory=dict)

    def create(self, *args, **kwargs) -> tuple[html.Div, None]:
        # self.create_callback()
        fn_template = string.Template("""
        function($inputs) {
        $conversions
            return $expression
        }
        """)
        input_list = []
        input_keys_list = []
        param_convert_str = ""
        for key, value in self.ids.items():
            input_comp = Input(value, "value")
            input_list.append(input_comp)
            input_keys_list.append(key)
            param_convert_str += f"\t {key} = Number({key});\n"

        clientside_func = fn_template.safe_substitute(
            {
                "inputs": ", ".join(input_keys_list),
                "expression": self.expression,
                "conversions": param_convert_str,
            }
        )

        clientside_callback(
            clientside_func,
            Output(self.id, "value"),
            *input_list,
            prevent_initial_call=True,
        )

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
                        id=self.id,
                        style={"width": "100%"},
                        readonly=True,
                        className="microlayout-input-readonly",
                    ),
                ],
                className="ssb-input",
            ),
            None,
        )


class DropdownComponent(ValueNode):
    """A class describing the dropdown type."""

    # field_settings: EditableField
    type: Literal["dropdown"]
    label: str
    options: list[dict]

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        self.field_settings.variabel_trigger = "value"
        callback_info = self.callback_settings

        return (
            html.Div(
                [
                    html.Label(self.label, title=self.label),
                    dcc.Dropdown(
                        options=self.options,
                        id=callback_info._id,
                        searchable=False,
                        className="ssb-dropdown",
                    ),
                ],
                className="ssb-input",
            ),
            callback_info,
        )


class ChecklistComponent(ValueNode):
    """A class describing the checklist type."""

    # field_settings: EditableField
    type: Literal["checklist"]
    label: str
    hidelabel: bool = False
    options: list[dict]
    variabel_trigger: str = "value"

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = self.callback_settings
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


class KlassDropdown(ValueNode):
    type: Literal["klass-dropdown"]
    klass_code: str
    label: str
    # field_settings: EditableField

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
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
            variable=self.variable,
            id=self.id,
        ).create(fetcher, settings)


class Textarea(ValueNode):
    type: Literal["textarea"]
    label: str
    hidelabel: bool = False
    value: str | None = ""
    readonly: bool = False
    # field_settings: EditableField

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[html.Div, FieldCallbackContainer]:
        """A method for creating the layout."""
        callback_info = self.callback_settings
        return (
            html.Div(
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
            ),
            callback_info,
        )


class KlassChecklist(ValueNode):
    type: Literal["klass-checklist"]
    klass_code: str
    label: str
    # field_settings: EditableField

    def create(
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
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
                id=self.id,
                variable=self.variable,
            ).create(fetcher, settings)
        else:
            return DropdownComponent(
                type="dropdown",
                label=self.label,
                options=options,
                id=self.id,
                variable=self.variable,
            ).create(fetcher, settings)


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
    | Tab
    | TimeseriesView
    | DynamicListView,
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
    TimeseriesView,
    DynamicListView,
):
    m.model_rebuild()

NodeListAdapter = TypeAdapter(list[Node])


def _flatten_ids(
    data: Sequence[FieldCallbackContainer | None | Sequence[FieldCallbackContainer]],
) -> Sequence[FieldCallbackContainer]:

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
        self, fetcher: MicrolayoutMeta, settings: EditorSettings
    ) -> tuple[list[Any], Sequence[FieldCallbackContainer]]:
        layout_list = []
        ids = []
        for node in self.nodes:
            layout, id_ = node.create(fetcher, settings)
            layout_list.append(layout)
            ids.append(id_)

        return layout_list, _flatten_ids(ids)
