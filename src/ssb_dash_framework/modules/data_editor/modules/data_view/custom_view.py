import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import State
from dash import Output
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from .....modules.data_editor.utils import EditorSettings
from .....config.models import register_module
from .....setup.variableselector import VariableSelector
from ..microlayout.microlayout import MicroLayoutAIO
from .base import DataEditorDataView

logger = logging.getLogger(__name__)


class DataViewCustomFigure:
    """Custom graphic figure module for displaying custom figures/graphs in custom views."""

    _id_number = 0

    def __init__(self, label, figure_func, applies_to_tables, applies_to_forms) -> None:
        """Initializes the DataViewCustomFigure module.

        Args:
            label: Visual label describing the figure.
            figure_func: Function generating and returning the Plotly figure object.
            applies_to_tables: List of applicable database tables.
            applies_to_forms: List of applicable questionnaire form IDs.
        """
        self.module_number = DataViewCustomFigure._id_number
        self.module_name = self.__class__.__name__
        DataViewCustomFigure._id_number += 1
        self.label = label
        self.figure_func = figure_func
        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms
        self.module_callbacks()

    def content(self):
        """Generates the layout content for the custom figure.

        Returns:
            A Dash Div containing the label and dcc.Graph.
        """
        return html.Div(
            children=[
                self.label,
                dcc.Graph(id=f"{self.module_name}-{self.module_number}-figure"),
            ]
        )

    def module_callbacks(self) -> None:
        """Registers callbacks to refresh the custom figure when reference state changes."""
        @callback(
            Output(f"{self.module_name}-{self.module_number}-figure", "figure"),
            Input("dataeditortableselector", "value"),
            VariableSelector.get_state("altinnskjema"),
            VariableSelector.get_refnr(Input),
            VariableSelector.get_timevar(Input),
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
    """Custom tabular reference module for displaying custom AgGrids in custom views."""

    def __init__(self, label, table_func, applies_to_tables, applies_to_forms) -> None:
        """Initializes the DataViewCustomTable module.

        Args:
            label: Visual label describing the reference table.
            table_func: Function returning a pandas DataFrame to show.
            applies_to_tables: List of applicable database tables.
            applies_to_forms: List of applicable questionnaire form IDs.
        """
        self.module_number = DataViewCustomFigure._id_number
        self.module_name = self.__class__.__name__
        DataViewCustomFigure._id_number += 1
        self.label = label
        self.table_func = table_func
        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms
        self.module_callbacks()

    def content(self):
        """Generates the layout content for the custom reference table.

        Returns:
            A Dash Div containing the label and dag.AgGrid.
        """
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
        """Registers callbacks to refresh and load AgGrid records on context changes."""
        @callback(
            Output(f"{self.module_name}-{self.module_number}-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-table", "columnDefs"),
            Input("dataeditortableselector", "value"),
            VariableSelector.get_state("altinnskjema"),
            VariableSelector.get_refnr(Input),
            VariableSelector.get_timevar(Input),
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


import logging

logger = logging.getLogger(__name__)


@register_module()
class DataViewCustom(DataEditorDataView):
    """DataView with a very flexible layout made to be tailored to specific needs."""

    _id_number = 0

    def __init__(
        self,
        layout: list,
        _from_config_file: bool = False,
        **kwargs,
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
        self._extra_args = kwargs
        self._layout = layout
        self._from_config_file = _from_config_file

    def build_layout(self, layout: dict | list) -> list:
        """Builds the visual layout components from config nodes.

        Args:
            layout: A layout node dictionary or list of nodes.

        Returns:
            A list of instantiated Dash components.

        Raises:
            ValueError: If node type is not a row, col, microlayout, or DataViewCustom.
        """
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
                # Updates the global settings object with entries that the yaml file overwrites
                # Useful for when you need to get data from a different table than in the rest of the app.
                settings_entries = self.settings.model_dump()
                settings_entries.update(layout)
                updates_settings = EditorSettings.model_validate(
                    settings_entries, extra="allow"
                )

                inputs = []
                layout_inputs = layout.get("inputs", [])
                assert isinstance(layout_inputs, list)
                for item in layout_inputs:
                    inputs.extend(VariableSelector.get_input(item))

                if len(inputs) == 0:
                    inputs.append(VariableSelector.get_refnr(Input))

                microlayout = MicroLayoutAIO(
                    data_handler=self.fetcher,
                    settings=updates_settings,
                    layout=layout,
                    instance_id=self.instance_id,
                    inputs=inputs,
                )
                components.append(microlayout)
            elif layout["type"] == "DataViewCustom":
                internal_layout = layout["layout"]
                for item in internal_layout:
                    components.extend(self.build_layout(item))
            else:
                raise ValueError(
                    f"Value for 'type' must be a valid component. Found type '{layout['type']}'"
                )

        return components

    def layout(self) -> html.Div:
        """Returns the layout of the module.

        Returns:
            A Dash Div element.

        Raises:
            ValueError: If layout is not a list.
        """
        if isinstance(self._layout, list) is False:
            raise ValueError(
                f"Layout for DataViewCustom is expected to be a list, recieved: {type(self._layout)} - {self._layout}"
            )

        tables = self._extra_args.get(
            "applies_to_tables", [self.settings.form_data_table]
        )
        forms = self._extra_args.get("applies_to_forms", self.settings.form_list)
        assert isinstance(tables, list)
        assert isinstance(forms, list)

        created_layout = []
        for item in self._layout:
            created_layout.extend(self.build_layout(item))

        super().__init__(
            applies_to_tables=tables,
            applies_to_forms=forms,
        )
        return html.Div(
            id=self.divname, children=created_layout, style={"display": "none"}
        )

    def module_callbacks(self) -> None:
        """Registers the module callbacks."""
        pass

    @classmethod
    def from_yaml(cls, *args, **kwargs):
        """Configures and instantiates the custom view dynamically from configuration dictionary properties.

        Args:
            *args: Positional arguments.
            **kwargs: Configuration dictionary properties.

        Returns:
            An instance of DataViewCustom.
        """
        return cls(*args, _from_config_file=True, **kwargs)

    @classmethod
    def from_dict(cls, config_dict):
        """Configures and instantiates the custom view dynamically from a configuration dictionary.

        Args:
            config_dict: Dictionary representing the layout configuration.

        Returns:
            An instance of DataViewCustom.
        """
        logger.info(f"Initializing class '{cls.__name__}' from dict object")
        logger.debug(config_dict)

        if isinstance(config_dict, list):
            config_dict = config_dict[0]

        return cls(
            layout=config_dict,
            _from_config_file=True,
        )

    def __str__(self) -> str:
        lines = [
            f"DataViewCustom #{self.module_number}",
            f"  divname:            {self.divname}",
            f"  applies_to_tables:  {self.applies_to_tables}",
            f"  applies_to_forms:   {self.applies_to_forms}",
            # f"  components:         {len(self.created_layout)} top-level component(s)",
            "",
        ]
        # for component in self.created_layout:
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


def convert_node(
    node: dict | list, applies_to_tables=None, applies_to_forms=None
) -> dict | list:
    """Recursively converts or updates properties within a layout node config tree.

    Args:
        node: Target dictionary or list node.
        applies_to_tables: List of applicable tables.
        applies_to_forms: List of applicable forms.

    Returns:
        The converted node structure.
    """
    logger.debug(
        f"node: {node}\ntables: {applies_to_tables}\nforms: {applies_to_forms}"
    )

    if isinstance(node, list):
        return [
            convert_node(
                listed_node,
                applies_to_tables=applies_to_tables,
                applies_to_forms=applies_to_forms,
            )
            for listed_node in node
        ]

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
