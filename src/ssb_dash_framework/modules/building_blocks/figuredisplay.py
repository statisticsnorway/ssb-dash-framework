import logging
from collections.abc import Callable
from typing import Any

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...setup.variableselector import VariableSelector
from ...utils.base_classes import AsType
from ...utils.base_classes import ModuleBase

logger = logging.getLogger(__name__)


class FigureDisplay(ModuleBase):
    """This module is used to display a plotly figure in the editing framework.

    It simplifies connecting a figure to the variable selector and allows for any figure to be used as long as it works in Dash.
    It also allows for click data to be processed and passed to the variable selector.
    """

    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
        as_type: AsType | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the FigureDisplay module.

        Args:
            label: The label for the module.
            figure_func: A function that returns a plotly figure. It should accept the dynamic states as arguments.
            inputs: A list of input variable names to be used in the figure function.
            states: A list of state variable names to be used in the figure function. Defaults to None.
            output: The name of the output variable to which the click data will be sent.
                If provided, the click data will be processed and sent to this variable.
                If None, no click data will be processed. Defaults to None.
            clickdata_func: A function to process the click data.
                It should accept the click data as an argument and return a value to be sent to the output variable.
                If None, no click data will be processed. Defaults to None.
            as_type: Whether the module is implemented as a "Tab" or a "Window".
                If None, it is inferred from which list the module is placed in when passed to `main_layout`.
            **kwargs: Additional keyword arguments passed to `ModuleBase`.

        Note:
            - The clickdata_func needs to process the click data and return a string value that will be sent to the output variable specified in the output argument.
            - clickdata is a dictionary with the structure:
                {
                    "points": [
                        {
                        "curveNumber": 1,
                        "pointNumber": 0,
                        "pointIndex": 0,
                        "x": 1,
                        "y": 3,
                        "bbox": {
                            "x0": 189.35,
                            "x1": 209.35,
                            "y0": 1057.72,
                            "y1": 1077.72
                        },
                        "customdata": [
                            3
                        ]
                        }
                    ]
                }
        """
        self.label = label
        self.icon = "📈"

        if states is None:
            states = []

        self.inputs = inputs
        self.states = states
        self.figure_func = figure_func
        self.output = output
        self.clickdata_func = clickdata_func

        super().__init__(as_type=as_type, **kwargs)

    def _create_layout(self) -> html.Div:
        layout = html.Div(
            dcc.Graph(
                id=f"{self.module_id}-figuredisplay",
                className="figuredisplay-graph",
            ),
            className="figuredisplay",
        )
        logger.debug("Generated layout.")
        return layout

    def module_callbacks(self) -> None:
        """Define the callbacks for the module."""
        dynamic_states = []
        for _input in self.inputs:
            dynamic_states.append(VariableSelector.get_input(_input))
        for _state in self.states:
            dynamic_states.append(VariableSelector.get_state(_state))

        @callback(  # type: ignore[misc]
            Output(f"{self.module_id}-figuredisplay", "figure"), *dynamic_states
        )
        def display_figure(
            *dynamic_states: list[str],
        ) -> Any:  # Should be a figure, might need a more specific type hint.
            logger.debug(
                "Args:\n"
                + "\n".join(
                    [
                        f"dynamic_state_{i}: {state}"
                        for i, state in enumerate(dynamic_states)
                    ]
                )
            )
            return self.figure_func(*dynamic_states)

        if (
            self.output
        ):  # TODO Fix known limitation of only having a single output to the variable selector. Should be possible to return a list/tuple

            @callback(  # type: ignore[misc]
                VariableSelector.get_output_object(variable=self.output),
                Input(f"{self.module_id}-figuredisplay", "clickData"),
                prevent_initial_call=True,
            )
            def transfer_clickdata(
                clickdata: dict[str, list[dict[str, str | int | float | bool]]],
            ) -> str:
                logger.debug(f"Args:\nclickdata: {clickdata}")
                if self.clickdata_func is None:
                    logger.warning(
                        "No clickdata_func provided, click data will not be processed."
                    )
                    return "No clickdata_func provided"
                return str(self.clickdata_func(clickdata))

