"""Needs to define models for:
- infopanel
- helpertab
- helpersidebar
- dataview
"""

import logging
from abc import ABC
from abc import abstractmethod

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import html

from ....utils.config_tools.connection import get_connection
from .registry import DataEditorRegistry

logger = logging.getLogger(__name__)


class DataEditor:

    _id_number = 0

    def __init__(
        self, enable_table_selector=True, starting_table="skjemadata_hoved"
    ) -> None:
        if DataEditor._id_number != 0:
            raise NotImplementedError(
                "Currently DataEditor can only be initialized once in your layout.\nMultiple of the module cannot exist in the same app."
            )
        self.module_number = DataEditor._id_number
        self.module_name = self.__class__.__name__
        DataEditor._id_number += 1

        if enable_table_selector:
            self.enable_table_selector = True
            DataEditorTableSelector(starting_table=starting_table)
        else:
            self.enable_table_selector = False

        self.icon = "🗊"
        self.label = "Data editor"

        self.gather_components()
        self.module_callbacks()

    def gather_components(self):
        self.info_row = html.Div()
        self.helper_row = html.Div()
        self.sidebar = html.Div(
            [module.layout() for module in DataEditorRegistry.sidebar_modules]
        )
        self.main_view = html.Div(
            id=f"{self.module_number}",
            children=[
                *{
                    value["instance"].layout()
                    for key, value in DataEditorRegistry.main_views.items()
                }
            ],
        )

    def _create_layout(self):

        return dbc.Container(
            [
                dbc.Row(self.info_row),
                dbc.Row(self.helper_row),
                dbc.Row([dbc.Col(self.sidebar, width=2), dbc.Col(self.main_view)]),
            ],
            fluid=True,
        )

    def layout(self):
        """Generates the layout for the Data Editor tab."""
        return self._create_layout()

    def module_callbacks(self):
        @callback(
            *[
                Output(
                    DataEditorRegistry.main_views_tables[main_view]["divname"], "style"
                )
                for main_view in DataEditorRegistry.main_views_tables
            ],
            Input("dataeditortableselector", "value"),
        )
        def update_main_view(selected_table):
            # Maybe more efficient to create all and then hide-unused?
            logger.debug(f"Selected table: {selected_table}")


class DataEditorTableSelector:

    _id_number = 0

    def __init__(self, starting_table: str = "skjemadata_hoved") -> None:
        if DataEditorTableSelector._id_number != 0:
            raise NotImplementedError(
                "Currently DataEditorTableSelector can only be initialized once in your layout.\nMultiple of the module cannot exist in the same app."
            )
        self.module_number = DataEditorTableSelector._id_number
        self.module_name = self.__class__.__name__
        DataEditorTableSelector._id_number += 1

        self.starting_table = starting_table

        DataEditorRegistry.sidebar_modules.append(self)

    def _create_layout(self):
        with get_connection() as conn:
            skjemadata_tables = [
                table for table in conn.list_tables() if table.startswith("skjemadata_")
            ]
            if self.starting_table not in skjemadata_tables:
                raise ValueError(
                    f"Selected starting table not found in data source.\nExpected one of: '{skjemadata_tables}'.\nReceived: '{self.starting_table}'"
                )
            table_options = [
                {"label": item, "value": item} for item in skjemadata_tables
            ]

        return html.Div(
            [
                dbc.Label("Tabellvelger"),
                dcc.Dropdown(
                    id="dataeditortableselector",
                    options=table_options,
                    value=self.starting_table,
                ),
            ]
        )

    def layout(self):
        return self._create_layout()

    def module_callbacks(
        self,
    ):  # TODO Add a way to connect selected table to variable selector?
        pass


class DataEditorInfoRow: ...


class DataEditorHelperButton: ...


class DataEditorHelperSidebar(ABC):

    def __init__(self) -> None:
        DataEditorRegistry.sidebar_modules.append(self)

    @abstractmethod
    def _create_layout(self):
        pass

    def layout(self):
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self):
        pass


class DataEditorDataView(ABC):

    def __init__(
        self, applies_to_tables: str | list[str], applies_to_forms: str | list[str]
    ) -> None:
        if isinstance(applies_to_tables, str):
            applies_to_tables = [applies_to_tables]
        self.applies_to_tables = applies_to_tables
        if isinstance(applies_to_forms, str):
            applies_to_forms = [applies_to_forms]
        self.applies_to_forms = applies_to_forms

        for table in self.applies_to_tables:
            DataEditorRegistry.main_views_tables.update(
                {
                    table: {
                        "divname": self.divname,
                        "name": self.module_name,
                        "number": self.module_number,
                        "instance": self,
                    }
                }
            )
        for form in self.applies_to_forms:
            DataEditorRegistry.main_views_forms.update(
                {
                    form: {
                        "divname": self.divname,
                        "name": self.module_name,
                        "number": self.module_number,
                        "instance": self,
                    }
                }
            )

    @abstractmethod
    def _create_layout(self):
        pass

    def layout(self):
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self):
        pass


class DefaultDataEditorDataView:

    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def get_data(self):
        with get_connection() as conn:
            data = conn.table(self.table_name).to_pandas()
        columndefs = [
            {
                "headerName": col,
                "field": col,
                "hide": col
                in [
                    "row_id",
                    "row_ids",
                    "skjema",
                    "refnr",
                ],
                "flex": 2 if col == "variabel" else 1,
            }
            for col in data.columns
        ]
        return data.to_dict("records"), columndefs
