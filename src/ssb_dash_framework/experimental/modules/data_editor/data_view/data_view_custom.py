import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
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

from .....modules.building_blocks.microlayout import Layout
from .....modules.building_blocks.microlayout import create_html_layout
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


class DataViewCustomMicroLayout:
    _id_number = 0

    def __init__(
        self,
        label,
        microlayout,
        get_data_func,
        update_func,
        applies_to_tables,
        applies_to_forms,
    ) -> None:
        self.module_number = DataViewCustomMicroLayout._id_number
        self.module_name = self.__class__.__name__
        DataViewCustomMicroLayout._id_number += 1
        self.variableselector = VariableSelector([], [])
        self.label = label

        self.layout_model = Layout(layout=microlayout)
        self.get_data_func = get_data_func
        self.update_func = update_func
        self.build_html_layout()

        self.applies_to_tables = applies_to_tables
        self.applies_to_forms = applies_to_forms

        self.module_callbacks()

    @staticmethod
    def make_default_get_data_func(layout: list):
        _vars = [item["variable"] for item in layout]

        def populate_microlayout(table, form, refnr, *args, **kwargs):
            logger.debug(f"Trying to populate microlayout. Args:\ntable: {table}\nform: {form}\nrefnr: {refnr}\nArgs: {args}\n Kwargs: {kwargs}")
            with get_connection() as conn:
                t = conn.table(table)
                data = t.filter(_.skjema == form).filter(_.refnr == refnr).to_pandas()
                print(data)
            

            return tuple(_safe_get(data, v) for v in _vars)

        return populate_microlayout

    @staticmethod
    def make_default_update_data_func(layout: list):
        _vars = [item["variable"] for item in layout]

        def update_microlayout(
            table, form, refnr, triggered_id, ids, new_values, *args, **kwargs
        ):
            triggered_index = ids.index(triggered_id)
            triggered_var = _vars[triggered_index]
            new_value = new_values[triggered_index]

            with get_connection() as conn:
                t = conn.table(table)
                data = t.filter(_.skjema == form).filter(_.refnr == refnr).to_pandas()

            old_value = _safe_get(data, triggered_var)

            return UpdateSkjemadata(
                table=table,
                ident=form,
                refnr=refnr,
                column=triggered_var,
                variable=triggered_var,
                value=new_value,
                old_value=old_value,
                long=True,
            )

        return update_microlayout

    def build_html_layout(self):
        self.layout, self.ids = create_html_layout(self.layout_model)

    def content(self):
        return html.Div(self.layout)

    def module_callbacks(self):
        @callback(
            *[Output(x, "value") for x in self.ids if x is not None],
            Input("dataeditortableselector", "value"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input("refnr"),
            *[Input(x, "value") for x in self.ids if x is not None],
        )
        def handle_update(selected_table, selected_form, refnr, *args):
            if (
                selected_table not in self.applies_to_tables
                or selected_form not in self.applies_to_forms
            ):
                logger.info("Preventing update.")
                raise PreventUpdate
            logger.debug(
                f"selected_table: {selected_table}\nselected_form: {selected_form}\nrefnr: {refnr}\nargs: {args}"
            )
            if ctx.triggered_id in self.ids:
                logger.debug("Updating value.")
                self.update_func(
                    *args
                )
                logger.info("Raising PreventUpdate after running update_func.")
                raise PreventUpdate
            to_return = self.get_data_func(selected_table, selected_form, refnr, args)
            logger.debug(f"to_return:\{to_return}")
            return to_return


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
        print(layout)

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
                    label=value["label"],
                    microlayout=value["layout"],
                    get_data_func=(
                        value["get_data_func"]
                        if value["get_data_func"] != "default"
                        else DataViewCustomMicroLayout.make_default_get_data_func(
                            value["layout"]
                        )
                    ),
                    update_func=(
                        value["update_func"]
                        if value["update_func"] != "default"
                        else DataViewCustomMicroLayout.make_default_update_data_func(
                            value["layout"]
                        )
                    ),
                    applies_to_tables=self.applies_to_tables,
                    applies_to_forms=self.applies_to_forms,
                )
                components.append(microlayout.content())
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
