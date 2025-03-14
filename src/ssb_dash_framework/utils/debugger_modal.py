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

    def default_func(*args):
        return html.Plaintext(f"{args!s}")

    def __init__(self, inputs, states, func=default_func):
        self.func = func
        self.inputs = inputs
        self.states = states
        self.variableselector = VariableSelector(inputs, states)
        self.callbacks()

    def layout(self):
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
                sidebar_button("🥼", "Debugger", "sidebar-debugger-button"),
            ]
        )

    def callbacks(self):

        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("debugger_modal", "is_open"),
            Input("sidebar-debugger-button", "n_clicks"),
            State("debugger_modal", "is_open"),
        )
        def debugger_toggle(n, is_open):
            if n:
                return not is_open
            return is_open

        @callback(Output("debuggerhelper_output", "children"), *dynamic_states)
        def debuggerhelper_dynamic_states(*args):
            ctx = callback_context  # Get callback context

            if not ctx.triggered:
                return "No input yet."

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

        @callback(Output("debuggerhelper_func_output", "children"), *dynamic_states)
        def debuggerhelper_func(*args):
            return self.func(args)
