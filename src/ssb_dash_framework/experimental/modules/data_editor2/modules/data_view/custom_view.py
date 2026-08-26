import json
import logging
from collections.abc import Callable

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import CallbackSettings
from ssb_dash_framework.experimental.modules.data_editor2.utils import EditorSettings

from ......config.yaml_parser import config_parser_yaml
from ssb_dash_framework.setup import VariableSelector
from ......utils.config_tools.set_variables import get_ident
from ......utils.config_tools.set_variables import get_refnr
from ......utils.config_tools.set_variables import get_time_units
from ......config.models import register_module
from ..microlayout.microlayout import MicroLayoutAIO
from ...utils import EditorSettings
from .base import DataEditorDataView

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
            self.variableselector.get_input(get_time_units().name),
        )
        def make_figure(selected_table, selected_form, refnr, period):
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
                dag.AgGrid(
                    id=f"{self.module_name}-{self.module_number}-table",
                    className="ag-theme-alpine ag-theme-ssb mb-2",
                ),
            ]
        )

    def module_callbacks(self) -> None:
        @callback(
            Output(f"{self.module_name}-{self.module_number}-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-table", "columnDefs"),
            Input("dataeditortableselector", "value"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input(get_refnr()),
            self.variableselector.get_input( get_time_units().name),
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



from typing import Any

from pandas import Series
from ...meta import FetcherMeta
from ......utils.config_tools.connection import get_connection
from dataclasses import dataclass
import logging
import time


from ibis import Table
import ibis
from ibis.expr.types.relations import Table
from ibis.expr.types.relations import Table

from pydantic import BaseModel
from ..microlayout.microlayout_components.editable_field_model import FieldCallbackContainer

logger = logging.getLogger(__name__)



#@register_module()
class DataViewCustom(DataEditorDataView):
    """DataView with a very flexible layout made to be tailored to specific needs."""

    _id_number = 0
    
    def __init__(
        self,
        #settings: EditorSettings,
        layout: dict,
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

        self._layout = layout
        
        

    def build_layout(self, layout: dict | list) -> list:
        """Builds the layout for the custom view."""
        components = []
        # guard against strings and other primitives
        if not isinstance(layout, (dict, list)):
            return components

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
                    converted = convert_node(
                        layout["layout"],
                        applies_to_tables=self.applies_to_tables,
                        applies_to_forms=self.applies_to_forms,
                    )
                    layout["layout"] = converted if isinstance(converted, list) else [converted]
                    logger.debug(
                        f"Done converting:\n{json.dumps(layout['layout'], indent=2, ensure_ascii=False)}"
                    )

                               
                microlayout = MicroLayoutAIO(
                    data_handler=self.fetcher,
                    settings=self.callback_setting,
                    #applies_to_tables=self.applies_to_tables,
                    #applies_to_forms=self.applies_to_forms,
                    layout=layout["layout"],
                    #getter_func=layout.get("getter_func", default_getter),
                    #update_func=layout.get("update_func", default_updater),
                    
                    
                    #inputs=[Input(f"var-{unit}", "value") for unit in get_time_units()],
                    inputs=[VariableSelector(selected_inputs=[get_refnr()], selected_states=[]).get_input(get_refnr())]
                )
                components.append(microlayout)
            else:
                raise ValueError(
                    f"Value for 'type' must be a valid component. Found type '{layout['type']}'"
                )

        return components

    def _create_layout(self) -> html.Div:
        return html.Div(
            id=self.divname, children=self.created_layout, style={"display": "none"}
        )

    def layout(self):
        """Returns the layout of the module."""
        self.applies_to_tables = self.settings.form_data_tables
        self.applies_to_forms = self.settings.form_list
        form_data_tables = self._layout.get("applies_to_tables", self.settings.form_data_tables[0])
        print(self._layout)
        if isinstance(form_data_tables, list):
            form_data_tables = form_data_tables[0]
        self.callback_setting = CallbackSettings(
            form_data_table = form_data_tables,
            form_reference_number_column = self.settings.refnr_col,
            formdata_field_value_column_name = self.settings.field_value_col,
            formdata_fieldname_column = self.settings.field_name_col,
            **self._layout
        )
        self.created_layout = self.build_layout(self._layout["layout"])
        self.module_callbacks()
        super().__init__(
            applies_to_tables=self.applies_to_tables, applies_to_forms=self.applies_to_forms
        )
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers the module callbacks."""
        pass
    
    @classmethod
    def from_yaml(cls, yaml_path):
        config = config_parser_yaml(yaml_path)
        return cls.from_dict(config[0])

    @classmethod
    def from_dict(cls, config_dict):
        logger.info(f"Initializing class '{cls.__name__}' from dict object")
        logger.debug(config_dict)

        if isinstance(config_dict, list):
            config_dict = config_dict[0]

        #settings = EditorSettings()
        return cls(
            #settings=settings,
            layout=config_dict,
            _from_config_file=True,
        )

    def __str__(self) -> str:
        lines = [
            f"DataViewCustom #{self.module_number}",
            f"  divname:            {self.divname}",
            #f"  applies_to_tables:  {self.applies_to_tables}",
            #f"  applies_to_forms:   {self.applies_to_forms}",
            #f"  components:         {len(self.created_layout)} top-level component(s)",
            "",
        ]
        #for component in self.created_layout:
        #    lines.extend(self._str_component(component, indent=2))
        return "\n".join(lines)

    def _str_component(self, component, indent: int = 0) -> list[str]:
        prefix = "  " * indent
        lines = []

        # Our own classes with rich __str__
        if isinstance(
            component,
            (MicroLayoutAIO, DataViewCustomFigure, DataViewCustomTable),
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


def convert_node(node: dict | list, applies_to_tables=None, applies_to_forms=None) -> dict | list:
    logger.debug(
        f"node: {node}\ntables: {applies_to_tables}\nforms: {applies_to_forms}"
    )
    if applies_to_tables is None:
        applies_to_tables = []
    if applies_to_forms is None:
        applies_to_forms = []

    if isinstance(node, list):
        return [
            convert_node(
                listed_node,
                applies_to_tables=applies_to_tables,
                applies_to_forms=applies_to_forms,
            )
            for listed_node in node
        ]

    if "type" in node and node["type"] == "calculated-field":
        node["applies_to_tables"] = applies_to_tables
        node["applies_to_forms"] = applies_to_forms

    #if "variable" in node:
    #    node = convert_node_build_field_settings(node, "field_path", node["variable"])
    #    popped = node.pop("variable")
    #    logger.debug(f"Removing value for 'variable' in node. Removed value: {popped}")
    #    node = convert_node_build_field_settings(
    #        node, "applies_to_tables", applies_to_tables
    #    )
    #    clean_forms = [f for f in applies_to_forms if f is not None]
    #    node = convert_node_build_field_settings(node, "applies_to_forms", clean_forms)

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
