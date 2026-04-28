import logging
from collections.abc import Callable
import json

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ssb_dash_framework.setup import VariableSelector
from ssb_dash_framework.utils.config_tools.config_file_handler import config_parser_yaml
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from .....modules.building_blocks.microlayout import MicroLayoutAIO
from .....modules.building_blocks.microlayout_components.editable_field_model import (
    default_updater,
)
from .....modules.building_blocks.microlayout_components.editable_field_model import (
    defult_getter,
)
from .....modules.building_blocks.microlayout_components.models import (
    CalculatedField,
    Layout,
)
from ..core import DataEditorDataView

logger = logging.getLogger(__name__)


class DataViewCustomFigure:
    _id_number = 0

    def __init__(self, label, figure_func, applies_to_tables, applies_to_forms) -> None:
        self.module_number = DataViewCustomFigure._id_number
        self.module_name = self.__class__.__name__
        DataViewCustomFigure._id_number += 1
        self.variableselector = VariableSelector([], [])
        self.label = label
        self.figure_func = figure_func
        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms
        self.module_callbacks()

    def content(self):
        return html.Div(
            children=[
                self.label,
                dcc.Graph(id=f"{self.module_name}-{self.module_number}-figure"),
            ]
        )

    def module_callbacks(self) -> None:
        @callback(
            Output(f"{self.module_name}-{self.module_number}-figure", "figure"),
            Input("dataeditortableselector", "value"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input(get_refnr()),
            *[self.variableselector.get_input(unit) for unit in get_time_units()],
        )
        def make_figure(selected_table, selected_form, refnr, *args):
            if (
                selected_table not in self.applies_to_tables
                or selected_form not in self.applies_to_forms
            ):
                logger.info("Preventing update.")
                raise PreventUpdate
            return self.figure_func()

    def __str__(self) -> str:
        lines = [
            f"DataViewCustomFigure #{self.module_number}",
            f"  label:              {self.label}",
            f"  figure_func:        {self.figure_func.__name__}",
            f"  applies_to_tables:  {self.applies_to_tables}",
            f"  applies_to_forms:   {self.applies_to_forms}",
        ]
        return "\n".join(lines)


class DataViewCustomTable:

    def __init__(self, label, table_func, applies_to_tables, applies_to_forms) -> None:
        self.module_number = DataViewCustomFigure._id_number
        self.module_name = self.__class__.__name__
        DataViewCustomFigure._id_number += 1
        self.variableselector = VariableSelector([], [])
        self.label = label
        self.table_func = table_func
        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms
        self.module_callbacks()

    def content(self):
        return html.Div(
            [
                self.label,
                dag.AgGrid(id=f"{self.module_name}-{self.module_number}-table"),
            ]
        )

    def module_callbacks(self) -> None:
        @callback(
            Output(f"{self.module_name}-{self.module_number}-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-table", "columnDefs"),
            Input("dataeditortableselector", "value"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input(get_refnr()),
            *[self.variableselector.get_input(unit) for unit in get_time_units()],
        )
        def make_figure(selected_table, selected_form, refnr, *args):
            if (
                selected_table not in self.applies_to_tables
                or selected_form not in self.applies_to_forms
            ):
                logger.info("Preventing update.")
                raise PreventUpdate

            data = self.table_func(selected_table, selected_form, refnr, *args)
            return data.to_dict("records"), [{"field": x} for x in data.columns]

    def __str__(self) -> str:
        lines = [
            f"DataViewCustomTable #{self.module_number}",
            f"  label:              {self.label}",
            f"  table_func:         {self.table_func.__name__}",
            f"  applies_to_tables:  {self.applies_to_tables}",
            f"  applies_to_forms:   {self.applies_to_forms}",
        ]
        return "\n".join(lines)


def _safe_get(data, v):
    rows = data.loc[data["variabel"] == v]["verdi"]
    return rows.item() if not rows.empty else None


class DataViewCustomMicroLayout(MicroLayoutAIO):
    _id_number = 0

    def __init__(
        self,
        applies_to_tables: list[str],
        applies_to_forms: list[str],
        getter_func: Callable[..., tuple],
        update_func: Callable[..., tuple | None],
        layout: list[dict] | Layout | None = None,
        layout_yaml_path: str | None = None,
        form_reference_input_id: str | None = None,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
        aio_id: str | None = None,
        horizontal: bool = False,
        form_data_table: str = "skjemadata",
        form_reference_number_column: str = "refnr",
        form_data_field_name_column: str = "feltnavn",
        formdata_field_value_column_name: str = "verdi",
        table_selector_id: str | None = "dataeditortableselector",
        form_selector_id: str | None = "var-altinnskjema",
    ) -> None:
        if not layout and not layout_yaml_path:
            raise ValueError("Either 'layout' or 'layout_yaml_path' must be defined.")
        if layout_yaml_path:
            if layout:
                raise ValueError(
                    "When 'layout_yaml_path' is defined, 'layout' must be None"
                )
            layout = self.from_yaml(layout_yaml_path)

        super().__init__(
            applies_to_tables=applies_to_tables,
            applies_to_forms=applies_to_forms,
            layout=layout,
            getter_func=getter_func,
            update_func=update_func,
            form_reference_input_id=(
                form_reference_input_id if form_reference_input_id else "var-refnr"
            ),
            inputs=inputs,
            states=states,
            getter_args=getter_args,
            aio_id=aio_id,
            horizontal=horizontal,
            form_data_table=form_data_table,
            form_reference_number_column=form_reference_number_column,
            form_data_field_name_column=form_data_field_name_column,
            formdata_field_value_column_name=formdata_field_value_column_name,
            table_selector_id=table_selector_id,
            form_selector_id=form_selector_id,
        )

    def __str__(self) -> str:
        base = super().__str__()
        lines = [
            base,
            f"  applies_to_tables:  {self._applies_to_tables}",
            f"  applies_to_forms:   {self._applies_to_forms}",
        ]
        return "\n".join(lines)


class DataViewCustom(DataEditorDataView):
    """DataView with a very flexible layout made to be tailored to specific needs."""

    _id_number = 0

    def __init__(
        self,
        applies_to_tables: str | list[str],
        applies_to_forms: str | list[str],
        layout,
        _from_config_file=False,
    ) -> None:
        """Initializes and registers the custom data view for selected tables and forms.

        Args:
            applies_to_tables: A list of tables that the module should apply to.
            applies_to_forms: A list of forms that the module should apply to.
        """
        self._from_config_file = _from_config_file
        self.module_number = DataViewCustom._id_number
        self.module_name = self.__class__.__name__
        DataViewCustom._id_number += 1
        self.divname = f"{self.module_name}-{self.module_number}"

        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms

        self.created_layout = self.build_layout(layout)
        self.module_callbacks()
        super().__init__(
            applies_to_tables=applies_to_tables, applies_to_forms=applies_to_forms
        )

    def build_layout(self, layout: dict | list) -> list:
        """Builds the layout for the custom view."""
        components = []

        if isinstance(layout, list):
            for item in layout:
                components.extend(self.build_layout(item))
            return components


        if isinstance(layout, dict):
            if layout["type"] == "row":                
                components.append(dbc.Row(self.build_layout(layout["children"])))
            elif layout["type"] == "col":                
                components.append(dbc.Col(self.build_layout(layout["children"])))

            elif layout["type"] == "microlayout":
                if self._from_config_file:
                    logger.debug(
                        "Converting 'layout' from config file structure to Microlayout compatible Layout object."
                    )
                    layout["layout"] = [convert_node( # Wraps in a list to work properly with Layout from microlayout models.
                        layout["layout"],
                        applies_to_tables=self.applies_to_tables,
                        applies_to_forms=self.applies_to_forms,
                    )]
                    logger.debug(
                        f"Done converting:\n{json.dumps(layout["layout"], indent=2, ensure_ascii=False)}"
                    )
                microlayout = DataViewCustomMicroLayout(
                    applies_to_tables=self.applies_to_tables,
                    applies_to_forms=self.applies_to_forms,
                    layout=layout["layout"],
                    getter_func=layout.get("getter_func", defult_getter),
                    update_func=layout.get("update_func", default_updater),
                    form_data_table=layout.get("form_data_table"),
                    form_data_field_name_column=layout.get(
                        "form_data_field_name_column"
                    ),
                )
                components.append(microlayout)
            else:
                raise ValueError(f"Value for 'type' must be a valid component. Found type '{layout["type"]}'")

        return components

    def _create_layout(self) -> html.Div:
        return html.Div(id=self.divname, children=self.created_layout)

    def layout(self):
        """Returns the layout of the module."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers the module callbacks."""
        pass

    @classmethod
    def from_dict(cls, config_dict):
        logger.info(f"Initializing class '{cls.__name__}' from dict object")
        logger.debug(config_dict)

        if isinstance(config_dict, list):
            config_dict = config_dict[0]

        return cls(
            applies_to_tables=config_dict["applies_to_tables"],
            applies_to_forms=config_dict["applies_to_forms"],
            layout=config_dict["layout"],
            _from_config_file=True,
        )

    def __str__(self) -> str:
        lines = [
            f"DataViewCustom #{self.module_number}",
            f"  divname:            {self.divname}",
            f"  applies_to_tables:  {self.applies_to_tables}",
            f"  applies_to_forms:   {self.applies_to_forms}",
            f"  components:         {len(self.created_layout)} top-level component(s)",
            "",
        ]
        for component in self.created_layout:
            lines.extend(self._str_component(component, indent=2))
        return "\n".join(lines)

    def _str_component(self, component, indent: int = 0) -> list[str]:
        prefix = "  " * indent
        lines = []

        # Our own classes with rich __str__
        if isinstance(
            component,
            (DataViewCustomMicroLayout, DataViewCustomFigure, DataViewCustomTable),
        ):
            for line in str(component).splitlines():
                lines.append(f"{prefix}{line}")
            return lines

        # Generic Dash component — show type and recurse into children
        lines.append(f"{prefix}{type(component).__name__}")
        children = getattr(component, "children", None)
        if children is None:
            pass
        elif isinstance(children, list):
            for child in children:
                lines.extend(self._str_component(child, indent=indent + 1))
        else:
            lines.extend(self._str_component(children, indent=indent + 1))

        return lines


def convert_node_build_field_settings(node, attribute, value):
    logger.debug(f"node: {node}\nattribute: {attribute}\nvalue: {value}")
    if "field_settings" not in node:
        node["field_settings"] = {}
    node["field_settings"].update({attribute: value})
    logger.debug(node, attribute, value)
    return node


def convert_node(node: dict, applies_to_tables=None, applies_to_forms=None) -> dict:
    logger.debug(
        f"node: {node}\ntables: {applies_to_tables}\nforms: {applies_to_forms}"
    )

    if applies_to_tables is None:
        applies_to_tables = []
    if applies_to_forms is None:
        applies_to_forms = []

    if isinstance(node, list):
        for listed_node in node:
            node = convert_node(listed_node, applies_to_tables = applies_to_tables, applies_to_forms = applies_to_forms)

    if "type" in node and node["type"] == "calculated-field":
        node["applies_to_tables"] = applies_to_tables
        node["applies_to_forms"] = applies_to_forms

    if "variable" in node:
        node = convert_node_build_field_settings(node, "field_path", node["variable"])
        popped = node.pop("variable")
        logger.debug(f"Removing value for 'variable' in node. Removed value: {popped}")
        node = convert_node_build_field_settings(
            node, "applies_to_tables", applies_to_tables
        )
        node = convert_node_build_field_settings(
            node, "applies_to_forms", applies_to_forms
        )

    if "children" in node:
        node["children"] = [
            convert_node(
                child,
                applies_to_tables=applies_to_tables,
                applies_to_forms=applies_to_forms,
            )
            for child in node["children"]
        ]

    return node
