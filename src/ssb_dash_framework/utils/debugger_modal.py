from collections.abc import Callable
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import callback_context
from dash import html

from ..setup.variableselector import VariableSelector
from ..utils.functions import sidebar_button


class DebugInspector:
    """DebugInspector is a class that creates a modal for debugging purposes.

    It displays the inputs and states passed to the class, as well as the
    arguments passed to the function. It also provides a toggle button to
    open and close the modal.
    """

    def default_func(*args: Any) -> html.Plaintext:
        """Default function to be called when the debugger is triggered.

        It simply returns the arguments passed to it as a Plaintext object.
        """
        return html.Plaintext(f"{args!s}")

    def __init__(
        self,
        inputs: list[str],
        states: list[str],
        func: Callable[..., Any] = default_func,
    ) -> None:
        """Initialize the DebugInspector class.

        Args:
            inputs (list[str]): List of input IDs to be monitored.
            states (list[str]): List of state IDs to be monitored.
            func (Callable[..., Any], optional): Function to be called when the debugger is triggered. Defaults to default_func.
        """
        self.func = func
        self.inputs = inputs
        self.states = states
        self.variableselector = VariableSelector(inputs, states)
        self.callbacks()

    def layout(self) -> html.Div:
        """Create the layout for the DebugInspector modal.

        Returns:
            html.Div: The layout for the DebugInspector modal.
        """
        return html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("DebugInspector")),
                        dbc.ModalBody(
                            [
                                dbc.Row(id="debuggerhelper_output"),
                                dbc.Row(
                                    "Below is the output from the function passed to the debugger"
                                ),
                                dbc.Row(html.Div(id="debuggerhelper_func_output")),
                            ]
                        ),
                    ],
                    id="debugger_modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("🦗", "Debugger", "sidebar-debugger-button"),
            ]
        )

    def callbacks(self) -> None:
        """Set up the callbacks for the DebugInspector modal.

        It includes a toggle button to open and close the modal,
        and a function to display the inputs and states passed to the class.
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("debugger_modal", "is_open"),
            Input("sidebar-debugger-button", "n_clicks"),
            State("debugger_modal", "is_open"),
        )
        def debugger_toggle(n: int, is_open: bool) -> bool:
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc],
            Output("debuggerhelper_output", "children"), *dynamic_states
        )
        def debuggerhelper_dynamic_states(*args: Any) -> html.Div:
            ctx = callback_context  # Get callback context

            if not ctx.triggered:
                return html.Div("No input yet.")

            return html.Div(
                [
                    dbc.Row(html.Plaintext("Arguments sent into the class")),
                    dbc.Row(html.Plaintext(f"Inputs: {self.inputs}")),
                    dbc.Row(html.Plaintext(f"States: {self.states}")),
                    dbc.Row(
                        html.Plaintext(
                            "Information about the callback Inputs and States."
                        )
                    ),
                    dbc.Row(html.Plaintext(f"Inputs: {ctx.inputs}")),
                    dbc.Row(html.Plaintext(f"States: {ctx.states}")),
                    dbc.Row(html.Plaintext("Args from *dynamic_states:")),
                    dbc.Row(html.Plaintext(f"{args}")),
                    dbc.Row([html.Plaintext(f"{x!s}, {type(x)}") for x in args]),
                ]
            )

        @callback(  # type: ignore[misc],
            Output("debuggerhelper_func_output", "children"), *dynamic_states
        )
        def debuggerhelper_func(*args: Any) -> Any:
            return self.func(args)
