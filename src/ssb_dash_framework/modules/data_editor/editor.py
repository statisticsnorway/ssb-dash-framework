from logging import getLogger
from typing import Any, Type
from typing import cast
import uuid

import dash_bootstrap_components as dbc
from dash import html
from dash import callback, Input, Output

from ...config.models import get_from_module_registry
from ...config.models import register_module

from .meta import ContextABC
from .meta import FetcherMeta
from .meta import ModuleABC
from .modules.inforow.info_row import DataEditorInfoRow
from .utils import EditorSettings
from ...setup.variableselector import VariableSelector
from ...utils.base_classes import ModuleBase

logger = getLogger(__name__)


def _parse_module[OutType](
    out_type: Type[OutType], module_type: Any | None, **kwargs
) -> OutType:
    if module_type is None:
        raise AttributeError("Yaml component needs to specify the type")
    module = get_from_module_registry(module_type)
    loaded_module = module.type.from_yaml(**kwargs)
    if issubclass(type(loaded_module), out_type) is False:
        raise ValueError(f"Loaded module {type(loaded_module)} is not a subclass of {out_type} which is exptected")
    return cast(OutType, loaded_module)


@register_module(as_tab="DataEditor")
class DataEditor(ModuleBase):
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

        instance_id = str(uuid.uuid4())

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
                module.set_settings(data_handler, settings, instance_id)
                buttons_list.append(dbc.Col(module.layout()))  # pyright: ignore
        self.helper_row = dbc.Row(buttons_list)  # pyright: ignore

        sidebar_list = []
        if sidebar is not None:
            for module in sidebar:
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
                view.set_settings(data_handler, settings, instance_id)
                dataview_list.append(view.layout())
        
        self.dataview_layouts = {}
        if dataview is not None:
            for view, layout_div in zip(dataview, dataview_list):
                tables = (
                    getattr(view, "applies_to_tables")
                    if hasattr(view, "applies_to_tables")
                    else [settings.form_data_table]
                )
                forms = (
                    getattr(view, "applies_to_forms")
                    if hasattr(view, "applies_to_forms")
                    else settings.form_list
                )
                for t in tables:
                    for f in forms:
                        self.dataview_layouts[(t, f)] = layout_div

        initial_children = []
        if dataview_list:
            starting_form = settings.form_list[0] if settings.form_list else None
            starting_layout = None
            if starting_form:
                starting_layout = self.dataview_layouts.get(
                    (settings.starting_table, starting_form)
                )
            if starting_layout is None:
                starting_layout = dataview_list[0]
            initial_children = [starting_layout]

        if initial_children:
            setattr(initial_children[0], "style", {"display": "block"})

        self.main_view = html.Div(
            id=f"{self.module_name}-div",
            children=initial_children,
        )

        super().__init__(as_type="Tab")

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

    @classmethod
    def from_yaml(cls, *args: Any, **kwargs: dict | list | str | int):
        import pprint

        pprint.pprint(kwargs)

        handler_name = kwargs.get("data_handler")
        data_handler_verified = _parse_module(
                FetcherMeta, handler_name
            )

        settings = kwargs.get("settings")
        settings_model = EditorSettings.model_validate(settings)

        inforow = kwargs.get("inforow", {})

        buttons: list[dict[str, Any]] | Any = kwargs.get("buttons", [])
        assert isinstance(buttons, list)

        parsed_buttons = []
        for button in buttons:
            button_type = button.get("type")
            button_args = {k: v for k, v in button.items() if k != "type"}
            button_item_verified = _parse_module(
                ContextABC, button_type, **button_args
            )
            parsed_buttons.append(button_item_verified)
        
        sidebar: list[dict[str, Any]] | Any = kwargs.get("sidebar", [])
        assert isinstance(sidebar, list)

        sidebar_items = []
        for item in sidebar:
            item_type = item.get("type")
            item_args = {k: v for k, v in item.items() if k != "type"}
            item_verified = _parse_module(
                ContextABC, item_type, **item_args
            )
            sidebar_items.append(item_verified)

        dataview: list[dict[str, Any]] | Any = kwargs.get("dataview", [])
        assert isinstance(dataview, list)

        dataview_items = []
        for item in dataview:
            item_type = item.get("type")
            item_args = {k: v for k, v in item.items() if k != "type"}
            item_verified = _parse_module(
                ContextABC, item_type, **item_args
            )
            dataview_items.append(item_verified)


        return cls(
            data_handler=data_handler_verified,
            settings=settings_model,
            inforow=inforow,
            buttons=parsed_buttons,
            sidebar=sidebar_items,
            dataview=dataview_items
        )

    def module_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor."""

        if not self.dataview or not self.main_view:
            return

        @callback(
            Output(f"{self.module_name}-div", "children"),
            Input("dataeditortableselector", "value"),
            VariableSelector.get_input("altinnskjema"),
            prevent_initial_call=True,
        )
        def toggle_view_visibility(selected_table, selected_form):
            if isinstance(selected_table, list):
                selected_table = selected_table[0] if len(selected_table) > 0 else None
            if isinstance(selected_form, list):
                selected_form = selected_form[0] if len(selected_form) > 0 else None

            logger.info(
                f"toggle_view_visibility: selected_table={selected_table}, selected_form={selected_form}"
            )
            if not selected_table or not selected_form:
                return []
            layout_div = self.dataview_layouts.get((selected_table, selected_form))
            if layout_div is not None:
                layout_div.style = {"display": "block"}
                return [layout_div]
            return []
