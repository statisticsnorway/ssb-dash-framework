from logging import getLogger
import uuid

import dash_bootstrap_components as dbc
from dash import html

from ...config.loader import instantiate_module
from ...config.models import ModuleConfig
from ...config.models import register_module

from .meta import ContextABC
from .meta import FetcherMeta
from .meta import ModuleABC
from .modules.inforow.info_row import DataEditorInfoRow
from .utils import EditorSettings
from ...setup.variableselector import VariableSelector
from dash import callback, Input, Output, State

logger = getLogger(__name__)


@register_module(as_tab="DataEditor")
class DataEditor:
    _module_count = 0

    def __init__(
        self,
        settings: EditorSettings | dict[str, list[str] | str | None],
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
        instance_id = str(uuid.uuid4())
        if isinstance(data_handler, str):
            import importlib
            library = importlib.import_module("ssb_dash_framework")
            cls = getattr(library, data_handler, None)
            if cls is not None:
                data_handler = cls()
            else:
                raise ValueError("The specified data handler is not supported")
        if isinstance(settings, dict):
            settings = EditorSettings.model_validate(settings)
        if not isinstance(settings, EditorSettings):
            raise TypeError(
                "Argument 'settings' must be either an EditorSettings instance or a dict that can validate to one."
            )
        self.icon = "🗊"
        self.label = "Data editor"

        inforow_list = {} if inforow is None else inforow

        self.info_view_row = DataEditorInfoRow(inforow_list)
        self.info_view_row.set_settings(data_handler, settings, instance_id)

        self.info_view = html.Div(
            self.info_view_row.layout(),  # pyright: ignore
        )

        buttons_list = []
        if buttons is not None:
            for module in buttons:
                if isinstance(module, dict):
                    module = instantiate_module(
                        ModuleConfig(**module), type="component", strict=False
                    )
                module.set_settings(data_handler, settings, instance_id)
                buttons_list.append(dbc.Col(module.layout()))  # pyright: ignore
        self.helper_row = dbc.Row(buttons_list)  # pyright: ignore

        sidebar_list = []
        if sidebar is not None:
            for module in sidebar:
                if isinstance(module, dict):
                    module = instantiate_module(
                        ModuleConfig(**module), type="component", strict=False
                    )
                module.set_settings(data_handler, settings, instance_id)
                sidebar_list.append(
                    dbc.Card(dbc.CardBody(module.layout()))  # pyright: ignore
                )
        self.sidebar = html.Div(
            sidebar_list,
            className=f"{self.module_name}-sidebar-modules",
        )

        self.dataview = dataview
        dataview_list: list[html.Div] = []
        if dataview is not None:
            for view in dataview:
                if isinstance(view, dict):
                    view = instantiate_module(
                        ModuleConfig(**view), type="component", strict=False
                    )
                view.set_settings(data_handler, settings, instance_id)
                dataview_list.append(view.layout())

        self.dataview_layouts = {}
        if dataview is not None:
            for view, layout_div in zip(dataview, dataview_list):
                tables = getattr(view, "applies_to_tables") if hasattr(view, "applies_to_tables") else [settings.form_data_table]
                # if not tables and hasattr(view, "applies_to_table"):
                #     tables = view.applies_to_table if isinstance(view.applies_to_table, list) else [view.applies_to_table]
                
                forms = getattr(view, "applies_to_forms") if hasattr(view, "applies_to_forms") else settings.form_list

                for t in tables:
                    for f in forms:
                        self.dataview_layouts[(t, f)] = layout_div

        initial_children = [dataview_list[0]] if len(dataview_list) else []
        if initial_children:
            setattr(initial_children[0], "style", {"display": "block"})

        self.main_view = html.Div(
            id=f"{self.module_name}-div",
            children=initial_children,
        )
        self.module_callbacks()

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
        
        if not self.dataview or not self.main_view:
            return
            
        @callback(
            Output(f"{self.module_name}-div", "children"),
            State("dataeditortableselector", "value"),
            VariableSelector.get_input("altinnskjema"),
            prevent_initial_call=True
        )
        def toggle_view_visibility(selected_table, selected_form):
            if not selected_table or not selected_form:
                return []
            layout_div = self.dataview_layouts.get((selected_table, selected_form))
            if layout_div is not None:
                layout_div.style = {"display": "block"}
                return [layout_div]
            return []
