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
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ssb_dash_framework import VariableSelector

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
        self.helper_row = html.Div(
            [module.layout() for module in DataEditorRegistry.helper_modules]
        )
        self.sidebar = html.Div(
            [
                dbc.Card(dbc.CardBody(module.layout()))
                for module in DataEditorRegistry.sidebar_modules
            ]
        )
        _existing_views = []
        main_views = []
        for divname, info in DataEditorRegistry.main_views.items():
            logger.debug(
                f"Adding '{divname}' to main_views. Applies to:\ntables: '{info["tables"]}'\nforms: {info["forms"]}"
            )
            try:
                if divname not in _existing_views:
                    main_views.append(info["instance"].layout())
                    _existing_views.append(divname)
                    logger.debug(f"Added '{divname}' to main_views.")
                else:
                    logger.debug(
                        f"Not adding {divname} due to it already existing. Existing views: {_existing_views}"
                    )
            except Exception as e:
                logger.error(
                    f"Encountered error '{e}' when adding main_view '{divname}' with configuration:\n{info}",
                    exc_info=True,
                )
                raise e

        self.main_view = html.Div(
            id=f"{self.module_number}",
            children=[view for view in main_views],
        )

    def _create_layout(self):

        return dbc.Container(
            [
                dbc.Row(self.info_row),
                dbc.Row(
                    [
                        dbc.Col(self.sidebar, width=2),
                        dbc.Col([dbc.Row(self.helper_row), dbc.Row(self.main_view)]),
                    ]
                ),
            ],
            fluid=True,
        )

    def layout(self):
        """Generates the layout for the Data Editor tab."""
        return self._create_layout()

    def module_callbacks(self):
        @callback(
            *[
                Output(main_view, "style")
                for main_view in DataEditorRegistry.main_views
            ],
            Input("dataeditortableselector", "value"),
            VariableSelector([], []).get_input("altinnskjema"),
        )
        def update_main_view(selected_table, selected_form):
            # Maybe more efficient to create all and then hide-unused?
            logger.debug(f"Selected table: {selected_table}")
            styles = []
            for divname in DataEditorRegistry.main_views:
                if (
                    selected_table in DataEditorRegistry.main_views[divname]["tables"]
                    and selected_form in DataEditorRegistry.main_views[divname]["forms"]
                ):
                    styles.append({"display": "block"})
                else:
                    styles.append({"display": "none"})
            if all(style == {"display": "none"} for style in styles):
                message = f"No main_view defined for {selected_table} - {selected_form}"
                logger.error(message)
                raise ValueError(message)
            if len(DataEditorRegistry.main_views) == 1:
                logger.debug(
                    "Returning a single dict due to only one main_view being defined"
                )
                styles = styles[
                    0
                ]  # Dash expects a single value when there is just one output.
            return styles


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

        DataEditorRegistry.sidebar_modules.insert(0, self)

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


class DataEditorHelperButton(ABC):
    _id_number = 0

    def __init__(self, label) -> None:
        self.module_number = DataEditorHelperButton._id_number
        self.module_name = self.__class__.__name__
        DataEditorHelperButton._id_number += 1
        self.label = label
        self.button_callbacks()
        DataEditorRegistry.helper_modules.append(self)

    def layout(self):
        if not hasattr(self, "modal_body"):
            raise AttributeError("Lacking 'modal_body' attribute.")
        return html.Div(
            [
                dbc.Button(
                    self.label, id=f"{self.module_name}-{self.module_number}-button"
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(self.label)),
                        dbc.ModalBody(self.modal_body),
                    ],
                    id=f"{self.module_name}-{self.module_number}-modal",
                    is_open=False,
                    className="dataeditor-helper-button-modal",
                ),
            ]
        )

    def button_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor Support Tables module."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_name}-{self.module_number}-modal", "is_open"),
            Input(f"{self.module_name}-{self.module_number}-button", "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-modal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False


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

        DataEditorRegistry.main_views.update(
            {
                self.divname: {
                    "tables": self.applies_to_tables,
                    "forms": self.applies_to_forms,
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
