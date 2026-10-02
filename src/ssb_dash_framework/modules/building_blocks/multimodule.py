import logging
from typing import Any

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...config.models import register_module
from ...utils import ModuleBase

logger = logging.getLogger(__name__)


@register_module()
class MultiModule(ModuleBase):
    """Generic class for switching between modules with a label and module_layout.

    If you have several modules, for an example several tables or figures, and you want them to take up less tabs/window button spaces, you can use this module.
    They keep the same functionality, but can be contained inside a single module instead of taking up extra space.
    """


    def __init__(self, label: str, module_list: list[Any]) -> None:
        """Initialize the MultiModule.

        Args:
            label: The label for the MultiModule.
            module_list: A list of modules to switch between. Each module should have
                a `label` and `module_layout` attribute.

        Notes:
            - The module requires some attributes to be present in each module in the `module_list`:
                - `label`: A string representing the label of the module.
                - `module_layout`: A Dash HTML Div component representing the layout of the module.
        """
        self.icon = "📚"
        self.label = label
        self.module_list = module_list

        self._is_valid()

    def _is_valid(self) -> None:
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

    def layout(self) -> html.Div:
        module_divs = [
            html.Div(
                self.module_layout,
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
                    searchable=False,
                    value=0,
                    clearable=False,
                ),
                html.Div(
                    className="multimodule-content",
                    children=module_divs,
                    id=f"{self.module_number}-multimodule-content",
                ),
            ],
            className="dbc multimodule",
        )
        logger.debug("Generated layout.")
        return layout


    def module_callbacks(self) -> None:
        """Define the callbacks for the MultiModule module."""

        @callback(  # type: ignore[misc]
            [
                Output(f"{self.module_number}-multimodule-module-{i}", "style")
                for i in range(len(self.module_list))
            ],
            Input(f"{self.module_number}-multimodule-dropdown", "value"),
        )
        def show_selected_module(selected_index: int) -> list[dict[str, str]]:
            logger.debug(f"Args:\nselected_index: {selected_index}\n")
            return [
                {"display": "block"} if i == selected_index else {"display": "none"}
                for i in range(len(self.module_list))
            ]

