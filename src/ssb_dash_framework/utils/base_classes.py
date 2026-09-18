"""Contains the common base class defining the interface shared by all modules."""

import logging
from abc import ABC
from abc import abstractmethod
from typing import Literal

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from .functions import sidebar_button

logger = logging.getLogger(__name__)

AsType = Literal["Tab", "Window"]


class ModuleBase(ABC):
    """Base class defining the interface all modules in the framework must implement.

    A module is implemented either as a tab or as a window (modal). The implementation
    can be set with the `as_type` argument when the module is instantiated, or be
    inferred by `main_layout` from whether the module is passed in `tab_list` or in
    `window_list`. `layout` returns the layout matching the chosen implementation.

    Attributes:
        _number: Class variable counting instantiated modules. Used to give each module a unique `module_id`.
        label: The label shown in the tab or on the sidebar button of the window.
        module_name: The name of the module, defaults to the class name.
        module_number: The value of `_number` at the time the module was instantiated.
        module_id: Unique id for the module, combining `module_name` and `module_number`.
        module_layout: The layout of the module itself, without tab/window wrapping.
        implemented_as: Either "Tab", "Window" or None if it has not been decided yet.
        icon: Optional icon shown next to the label.

    Note:
        Subclasses must set `label`, and any other attribute needed by `_create_layout`
        and `module_callbacks`, before calling `ModuleBase.__init__`. Ids used inside the
        module layout and its callbacks should be prefixed with `self.module_id` to keep
        them unique across modules.
    """

    _number: int = 0

    label: str
    module_name: str
    module_number: int
    module_id: str
    module_layout: html.Div
    icon: str | Component

    def __init__(
        self,
        as_type: AsType | None = None,
        window_scrollable: bool = True,
    ) -> None:
        """Initialize the module, create its layout and register its callbacks.

        Args:
            as_type: Whether the module is implemented as a "Tab" or as a "Window".
                If None, the implementation is inferred by `main_layout` based on whether
                the module is passed in `tab_list` or in `window_list`.
            window_scrollable: Whether the modal body is scrollable. Only used when implemented as a window.

        Raises:
            AttributeError: If `label` is not set before calling this method.
        """
        self.implemented_as: AsType | None = None
        self.window_scrollable = window_scrollable

        if not hasattr(self, "module_name"):
            self.module_name = self.__class__.__name__
        self.module_number = ModuleBase._number
        ModuleBase._number += 1
        self.module_id = f"{self.module_name}-{self.module_number}"

        if not hasattr(self, "label"):
            raise AttributeError(
                f"Class {self.__class__.__name__} must set a 'label' attribute before calling ModuleBase.__init__."
            )
        if not hasattr(self, "icon"):
            self.icon = ""

        if not hasattr(self, "module_layout"):
            self.module_layout = self._create_layout()
        self.module_callbacks()

        if as_type is not None:
            self.set_implementation(as_type)

    def set_implementation(self, as_type: AsType) -> None:
        """Decide whether the module is implemented as a tab or as a window.

        Called by `main_layout` for modules that were instantiated without `as_type`.

        Args:
            as_type: Whether the module is implemented as a "Tab" or as a "Window".

        Raises:
            ValueError: If `as_type` is not "Tab" or "Window", or if the module is already implemented as the other type.
        """
        if as_type not in ("Tab", "Window"):
            raise ValueError(
                f"'as_type' must be either 'Tab' or 'Window'. Received: '{as_type}'"
            )
        if self.implemented_as == as_type:
            return
        if self.implemented_as is not None:
            raise ValueError(
                f"{self.module_id} is already implemented as '{self.implemented_as}' and cannot also be implemented as '{as_type}'."
            )
        self.implemented_as = as_type
        if as_type == "Window":
            self._window_callbacks()
        logger.debug(f"Implementing {self.module_id} as {as_type}.")

    @abstractmethod
    def _create_layout(self) -> html.Div:
        """Create the layout of the module itself, without tab/window wrapping."""

    @abstractmethod
    def module_callbacks(self) -> None:
        """Define the callbacks belonging to the module itself."""

    def layout(self) -> dbc.Tab | html.Div:
        """Generate the layout for the module in the chosen implementation.

        Returns:
            A `dbc.Tab` if implemented as a tab, a `html.Div` containing the modal and its
            sidebar button if implemented as a window, or the module layout itself if the
            module is used as a building block inside another module.
        """
        if self.implemented_as == "Tab":
            return self._tab_layout()
        if self.implemented_as == "Window":
            return self._window_layout()
        return self.get_module_layout()

    def get_module_layout(self) -> html.Div:
        """Get the layout of the module.

        Works as is, but can be overridden if needed.

        Returns:
            The layout of the module itself.
        """
        return self.module_layout

    def _tab_layout(self) -> dbc.Tab:
        """Generate the layout for the module as a tab.

        Returns:
            The tab containing the module layout.
        """
        if self.icon:
            label_content: list[Component | str] | str = (
                [self.icon, " ", self.label]
                if isinstance(self.icon, str)
                else [self.icon, html.Span(self.label, className="ms-2")]
            )
        else:
            label_content = self.label
        layout = dbc.Tab(
            html.Div(
                className="tab-implementation",
                children=self.get_module_layout(),
            ),
            label=label_content,
        )
        logger.debug(f"Generated {self.module_id} - {self.label} tab layout")
        return layout

    def _window_layout(self) -> html.Div:
        """Generate the layout for the module as a modal window.

        Returns:
            The layout containing the modal and the sidebar button toggling it.
        """
        layout = html.Div(
            children=[
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Span(
                                                self.icon,
                                                className="modal-title-icon",
                                            ),
                                            html.Span(
                                                self.label,
                                                className="modal-title-text",
                                            ),
                                        ],
                                        className="window-implementation-modal-title",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            DashIconify(
                                                icon="feather:maximize-2",
                                                width=18,
                                            ),
                                            id=f"{self.module_id}-modal-fullscreen",
                                            className="ssb-modal-icon-button",
                                            title="Maksimer vindu",
                                        ),
                                        width="auto",
                                        className="ms-auto",
                                    ),
                                ],
                                align="center",
                                className="w-100 flex-nowrap",
                            ),
                            close_button=True,
                        ),
                        dbc.ModalBody(
                            html.Div(
                                className="window-implementation-modal-body dbc dbc-ag-grid",
                                children=self.get_module_layout(),
                            )
                        ),
                    ],
                    id=f"{self.module_id}-modal",
                    className="ssb-modal",
                    size="xl",
                    fullscreen="xxl-down",
                    scrollable=self.window_scrollable,
                ),
                sidebar_button(
                    self.icon,
                    self.label,
                    f"sidebar-{self.module_id}-modal-button",
                ),
            ]
        )
        logger.debug(f"Generated {self.module_id} - {self.label} window layout")
        return layout

    def _window_callbacks(self) -> None:
        """Define the callbacks needed to open, close and resize the modal window."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_id}-modal", "is_open"),
            Input(f"sidebar-{self.module_id}-modal-button", "n_clicks"),
            State(f"{self.module_id}-modal", "is_open"),
        )
        def _modal_toggle(n: int, is_open: bool) -> bool:
            """Toggle the state of the modal window.

            Args:
                n: Number of clicks on the toggle button.
                is_open: Current state of the modal (open/closed).

            Returns:
                The new state of the modal (open/closed).
            """
            logger.info("Toggle modal")
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            Output(f"{self.module_id}-modal", "fullscreen"),
            Output(f"{self.module_id}-modal-fullscreen", "children"),
            Output(f"{self.module_id}-modal-fullscreen", "title"),
            Input(f"{self.module_id}-modal-fullscreen", "n_clicks"),
            State(f"{self.module_id}-modal", "fullscreen"),
        )
        def _toggle_fullscreen_modal(
            n_clicks: int,
            fullscreen_state: str | bool,
        ) -> tuple[str | bool, DashIconify, str]:
            """Toggle the modal between fullscreen and its default size.

            Args:
                n_clicks: Number of clicks on the fullscreen button.
                fullscreen_state: Current fullscreen state of the modal.

            Returns:
                The new fullscreen state, the icon and the title of the button.

            Raises:
                PreventUpdate: If the button has not been clicked.
            """
            if not n_clicks:
                raise PreventUpdate

            if fullscreen_state is True:
                return (
                    "xxl-down",
                    DashIconify(icon="feather:maximize-2", width=18),
                    "Maksimer vindu",
                )

            return (
                True,
                DashIconify(icon="feather:minimize-2", width=18),
                "Minimer vindu",
            )
    
    

    