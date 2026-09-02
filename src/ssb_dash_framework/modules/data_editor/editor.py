# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
from logging import getLogger

import dash_bootstrap_components as dbc
from dash import html

from ...config.models import register_module
from ...setup.variableselector import VariableSelector
from ...utils.config_tools.set_variables import get_time_units
from .meta import ContextABC
from .meta import FetcherMeta
from .meta import ModuleABC
from .modules.inforow.info_row import DataEditorInfoRow
from .utils import EditorSettings

logger = getLogger(__name__)


@register_module(as_tab="DataEditor")
class DataEditor:
    _module_count = 0

    def __init__(
        self,
        settings: EditorSettings,
        data_handler: FetcherMeta,
        inforow: dict | None = None,
        buttons: list[ModuleABC | ContextABC] | None = None,
        sidebar: list[ModuleABC | ContextABC] | None = None,
        dataview: list[ModuleABC] | None = None,
        enable_table_selector: bool = True,
    ) -> None:
        if DataEditor._module_count:
            raise RuntimeError("Only one DataEditor can be created")
        DataEditor._module_count += 1
        self.module_name = self.__class__.__name__

        self.icon = "🗊"
        self.label = "Data editor"

        inforow_list = {} if inforow is None else inforow

        self.info_view_row = DataEditorInfoRow(inforow_list)
        self.info_view_row.set_settings(data_handler, settings)

        self.info_view = html.Div(
            self.info_view_row.layout(),  # pyright: ignore
        )

        buttons_list = []
        if buttons is not None:
            for module in buttons:
                module.set_settings(data_handler, settings)
                buttons_list.append(dbc.Col(module.layout()))  # pyright: ignore
        self.helper_row = dbc.Row(buttons_list)  # pyright: ignore

        sidebar_list = []
        if sidebar is not None:
            for module in sidebar:
                module.set_settings(data_handler, settings)
                sidebar_list.append(
                    dbc.Card(dbc.CardBody(module.layout()))  # pyright: ignore
                )
        self.sidebar = html.Div(
            sidebar_list,
            className=f"{self.module_name}-sidebar-modules",
        )

        dataview_list: list[html.Div] = []
        if dataview is not None:
            for view in dataview:
                view.set_settings(data_handler, settings)
                dataview_list.append(view.layout())

        # Make default view
        if len(dataview_list):
            dataview_list[0].style = {"display": "block"}  # pyright: ignore

        self.main_view = html.Div(
            id=f"{self.module_name}-div",
            children=dataview_list,
        )

    def _create_layout(self) -> dbc.Container:  # pyright: ignore
        """Creates the layout for the DataEditor module."""
        return dbc.Container(
            [
                dbc.Row(
                    html.H1(
                        id=f"{self.module_name}-header",
                        className=f"{self.module_name}-header",
                    )
                ),
                dbc.Row(self.info_view),
                dbc.Row(
                    [
                        dbc.Col(self.sidebar, className=f"{self.module_name}-sidebar"),
                        dbc.Col(
                            [
                                dbc.Row(
                                    dbc.Card(
                                        dbc.CardBody(self.helper_row),
                                        className=f"{self.module_name}-helper-row",
                                    )
                                ),
                                dbc.Row(
                                    dbc.Card(
                                        dbc.CardBody(self.main_view),
                                        className=f"{self.module_name}-main-view",
                                    )
                                ),
                            ],
                        ),
                    ]
                ),
            ],
            fluid=True,
        )

    def layout(self) -> dbc.Container:  # pyright: ignore
        """Generates the layout for the DataEditor."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor."""
        variableselector = VariableSelector(
            selected_inputs=[get_time_units().name],
            selected_states=[],
        )
