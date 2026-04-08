import logging
from typing import Callable

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input, State
from dash import Output
from dash import callback
from dash import callback_context as ctx
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from ibis import _

from ssb_dash_framework import get_connection
from ssb_dash_framework.setup import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from .....modules.building_blocks.microlayout import MicroLayoutAIO
from .....modules.building_blocks.microlayout_components.models import Layout
from .....modules.building_blocks.microlayout_components.editable_field_model import defult_getter, default_updater

from .....utils.core_models import UpdateSkjemadata
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
        layout: list[dict] | Layout | None= None,
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
                raise ValueError("When 'layout_yaml_path' is defined, 'layout' must be None")
            layout = self.from_yaml(layout_yaml_path)

        super().__init__(
            applies_to_tables=applies_to_tables,
            applies_to_forms=applies_to_forms,
            layout = layout,
            getter_func=getter_func,
            update_func= update_func,
            form_reference_input_id= form_reference_input_id if form_reference_input_id else "var-refnr",
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
    

    def convert_node(self, node: dict) -> dict:

        if "label" in node:
            node["label"] = node["label"]

        if "variable" in node:
            node["field_settings"] = {"field_path": node["variable"]}

        if "children" in node:
            node["children"] = [self.convert_node(child) for child in node["children"]]

        return node


    def from_yaml(self, yaml_path: str) -> list[dict]:
        import yaml
        with open(yaml_path) as f:
            yaml_layout = yaml.safe_load(f)["layout"]
        layout_from_yaml = Layout([self.convert_node(node) for node in yaml_layout])
        logger.debug(layout_from_yaml)
        return layout_from_yaml

class DataViewCustom(DataEditorDataView):
    """DataView with a very flexible layout made to be tailored to specific needs."""

    _id_number = 0

    def __init__(
        self,
        applies_to_tables: str | list[str],
        applies_to_forms: str | list[str],
        layout,
    ) -> None:
        """Initializes and registers the custom data view for selected tables and forms.

        Args:
            applies_to_tables: A list of tables that the module should apply to.
            applies_to_forms: A list of forms that the module should apply to.
        """
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
        
        for key, value in layout.items():
            print("key: ", key)
            print("value: ", value)
            if key == "kwargs":
                continue
            if isinstance(value, dict):
                kwargs = value.get("kwargs", None)
            else:
                kwargs = None

            if key == "row":
                children = self.build_layout(value)
                components.append(dbc.Row(children, **kwargs if kwargs else {}))

            elif key == "col":
                children = self.build_layout(value)
                components.append(dbc.Col(children, **kwargs if kwargs else {}))

            elif key == "figure":
                figure = DataViewCustomFigure(
                    label=value["label"],
                    figure_func=value["figure_func"],
                    applies_to_tables=self.applies_to_tables,
                    applies_to_forms=self.applies_to_forms,
                )
                components.append(figure.content())
            elif key == "table":
                table = DataViewCustomTable(
                    label=value["label"],
                    table_func=value["table_func"],
                    applies_to_tables=self.applies_to_tables,
                    applies_to_forms=self.applies_to_forms,
                )
                components.append(table.content())
            elif key == "microlayout":
                microlayout = DataViewCustomMicroLayout(
                    applies_to_tables=self.applies_to_tables,
                    applies_to_forms=self.applies_to_forms,
                    layout=value["layout"],
                    getter_func=value.get("getter_func", defult_getter),
                    update_func=value.get("update_func", default_updater),
                    form_data_table = value.get("form_data_table"),
                    form_data_field_name_column = value.get("form_data_field_name_column")
                )
                components.append(microlayout)
            else:
                components.extend(self.build_layout(value))

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
    def convert_typed_to_keyed(cls, node):
        if isinstance(node, list):
            return [cls.convert_typed_to_keyed(item) for item in node]

        if isinstance(node, dict):
            if node.get("type") == "microlayout":
                inner = {k: v for k, v in node.items() if k != "type"}
                if "layout" in inner:
                    inner["layout"] = [
                        convert_node(child)
                        for child in cls.convert_typed_to_keyed(inner["layout"])
                    ]
                if "children" in inner:
                    inner["children"] = cls.convert_typed_to_keyed(inner["children"])
                return {"microlayout": inner}

            return {k: cls.convert_typed_to_keyed(v) for k, v in node.items()}

        return node

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "DataViewCustom":
        import yaml
        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        # Handle both a top-level dict and a single-item list
        if isinstance(config, list):
            config = config[0]
        
        print(config["layout"])

        config["layout"] = cls.convert_typed_to_keyed(config["layout"])


        return cls(
            applies_to_tables=config["applies_to_tables"],
            applies_to_forms=config["applies_to_forms"],
            layout=config["layout"],
        )

def convert_node(node: dict) -> dict:

    if "label" in node:
        node["label"] = node["label"]

    if "variable" in node:
        node["field_settings"] = {"field_path": node["variable"]}

    if "children" in node:
        node["children"] = [convert_node(child) for child in node["children"]]

    return node