import logging
from typing import Any

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class MultiModule:
    """Generic class for switching between modules with a label and module_layout."""

    _id_number = 0

    def __init__(self, label: str, module_list: list[Any]) -> None:
        """Initialize the MultiModule.

        Args:
            label (str): The label for the MultiModule.
            module_list (list[Any]): A list of modules to switch between. Each module should have
                a `label` and `module_layout` attribute.

        Notes:
            - The module requires some attributes to be present in each module in the `module_list`:
                - `label`: A string representing the label of the module.
                - `module_layout`: A Dash HTML Div component representing the layout of the module.
              The module can be validated using the module_validator function.
        """
        self.label = label
        self.module_list = module_list
        self.module_number = MultiModule._id_number
        self.module_name = self.__class__.__name__
        MultiModule._id_number += 1

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

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

    def _create_layout(self) -> html.Div:
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
            className="dbc multimodule",
        )
        logger.debug("Generated layout.")
        return layout

    def layout(self) -> html.Div:
        """Define the layout for the MultiModule module.

        Because this module can be used as a a component in other modules, it needs to have a layout method that is not abstract.
        For implementations as tab or window, this method should still be overridden.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module to be displayed directly.
        """
        return self.module_layout

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
            return [
                {"display": "block"} if i == selected_index else {"display": "none"}
                for i in range(len(self.module_list))
            ]


class MultiModuleTab(TabImplementation, MultiModule):
    """MultiModule implemented as a Tab."""

    def __init__(self, label: str, module_list: list[Any]) -> None:
        """Initialize the MultiModuleTab.

        Args:
            label (str): The label for the MultiModuleTab.
            module_list (list[Any]): A list of modules to switch between. Each module should have
        """
        MultiModule.__init__(self, label=label, module_list=module_list)
        TabImplementation.__init__(
            self,
        )


class MultiModuleWindow(WindowImplementation, MultiModule):
    """MultiModule implemented as a Window."""

    def __init__(self, label: str, module_list: list[Any]) -> None:
        """Initialize the MultiModuleWindow.

        Args:
            label (str): The label for the MultiModuleWindow.
            module_list (list[Any]): A list of modules to switch between. Each module should have
        """
        MultiModule.__init__(self, label=label, module_list=module_list)
        WindowImplementation.__init__(self)
