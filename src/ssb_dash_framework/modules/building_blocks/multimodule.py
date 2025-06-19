import logging

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...utils import WindowImplementation, TabImplementation

logger = logging.getLogger(__name__)


class MultiModule:
    """Generic class for switching between modules with a label and module_layout."""

    _id_number = 0

    def __init__(self, label, module_list):
        self.label = label
        self.module_list = module_list
        self.module_number = MultiModule._id_number
        self.module_name = self.__class__.__name__
        MultiModule._id_number += 1

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()

    def _is_valid(self):
        if not isinstance(self.label, str):
            raise TypeError(
                f"label {self.label} is not a string, is type {type(self.label)}"
            )
        if not isinstance(self.module_list, list):
            raise TypeError(
                f"module_list {self.module_list} is not a list, is type {type(self.module_list)}"
            )
        for module in self.module_list:
            if not hasattr(module, "label") or not hasattr(module, "module_layout"):
                raise ValueError(
                    f"Module {module} must have 'label' and 'module_layout' attributes"
                )

    def _create_layout(self):
        module_divs = [
            html.Div(
                module.module_layout,
                className="multimodule-content",
                id=f"{self.module_number}-multimodule-module-{i}",
                style={"display": "block" if i == 0 else "none"},
            )
            for i, module in enumerate(self.module_list)
        ]
        layout = html.Div(
            [
                dcc.Dropdown(
                    id=f"{self.module_number}-multimodule-dropdown",
                    options=[
                        {"label": module.label, "value": i}
                        for i, module in enumerate(self.module_list)
                    ],
                    value=0,
                    clearable=False,
                ),
                html.Div(
                    className="multimodule-content",
                    children=module_divs,
                    id=f"{self.module_number}-multimodule-content",
                ),
            ],
            className="multimodule",
        )
        logger.debug("Generated layout with all modules rendered")
        return layout

    def layout(self):
        return self.module_layout

    def module_callbacks(self):
        @callback(
            [
                Output(f"{self.module_number}-multimodule-module-{i}", "style")
                for i in range(len(self.module_list))
            ],
            Input(f"{self.module_number}-multimodule-dropdown", "value"),
        )
        def show_selected_module(selected_index: int):
            return [
                {"display": "block"} if i == selected_index else {"display": "none"}
                for i in range(len(self.module_list))
            ]

class MultiModuleTab(TabImplementation, MultiModule):
    def __init__(self, label, module_list):
        MultiModule.__init__(self, label = label, module_list=module_list)
        TabImplementation.__init__(
            self,
        )

class MultiModuleWindow(WindowImplementation,MultiModule):
    def __init__(self, label, module_list):
        MultiModule.__init__(self, label = label, module_list=module_list)
        WindowImplementation.__init__(self)
        





    