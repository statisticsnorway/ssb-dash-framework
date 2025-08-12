import logging
from collections.abc import Callable
from typing import Any

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class FigureDisplay:
    """This module is used to display a plotly figure in the editing framework.

    It simplifies connecting a figure to the variable selector and allows for any figure to be used as long as it works in Dash.
    It also allows for click data to be processed and passed to the variable selector.
    """

    _id_number: int = 0

    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
    ) -> None:
        """Initialize the FigureDisplay module.

        Args:
            label (str): The label for the module.
            figure_func (Callable[..., Any]): A function that returns a plotly figure. It should accept the dynamic states as arguments.
            inputs (list[str]): A list of input variable names to be used in the figure function.
            states (list[str] | None, optional): A list of state variable names to be used in the figure function. Defaults to None.
            output (str | None, optional): The name of the output variable to which the click data will be sent.
                If provided, the click data will be processed and sent to this variable.
                If None, no click data will be processed. Defaults to None.
            clickdata_func (Callable[..., Any] | None, optional): A function to process the click data.
                It should accept the click data as an argument and return a value to be sent to the output variable.
                If None, no click data will be processed. Defaults to None.

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
        self.module_number = FigureDisplay._id_number
        self.module_name = self.__class__.__name__
        FigureDisplay._id_number += 1
        self.icon = "📈"

        self.label = label
        if states is None:
            states = []
        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.figure_func = figure_func
        self.output = output
        self.clickdata_func = clickdata_func

        self.module_layout = self._create_layout()
        self.module_callbacks()

        module_validator(self)

    def _create_layout(self) -> html.Div:
        layout = html.Div(
            dcc.Graph(
                id=f"{self.module_number}-figuredisplay",
                className="figuredisplay-graph",
            ),
            className="figuredisplay",
        )
        logger.debug("Generated layout.")
        return layout

    def layout(self) -> html.Div:
        """Define the layout for the FigureDisplay module.

        Because this module can be used as a a component in other modules, it needs to have a layout method that is not abstract.
        For implementations as tab or window, this method should still be overridden.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module to be displayed directly.
        """
        return self.module_layout

    def module_callbacks(self) -> None:
        """Define the callbacks for the module."""
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-figuredisplay", "figure"), *dynamic_states
        )
        def display_figure(
            *dynamic_states: list[str],
        ) -> Any:  # Should be a figure, might need a more specific type hint.
            return self.figure_func(*dynamic_states)

        if (
            self.output
        ):  # TODO Fix known limitation of only having a single output to the variable selector. Should be possible to return a list/tuple

            @callback(  # type: ignore[misc]
                self.variableselector.get_output_object(variable=self.output),
                Input(f"{self.module_number}-figuredisplay", "clickData"),
                prevent_initial_call=True,
            )
            def transfer_clickdata(
                clickdata: dict[str, list[dict[str, str | int | float | bool]]],
            ) -> str:
                logger.debug(clickdata)
                if self.clickdata_func is None:
                    logger.warning(
                        "No clickdata_func provided, click data will not be processed."
                    )
                    return "No clickdata_func provided"
                return str(self.clickdata_func(clickdata))


class FigureDisplayTab(TabImplementation, FigureDisplay):
    """FigureDisplay implemented as a tab."""

    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
    ) -> None:
        """Initializes FigureDisplayTab."""
        FigureDisplay.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            figure_func=figure_func,
            output=output,
            clickdata_func=clickdata_func,
        )
        TabImplementation.__init__(self)


class FigureDisplayWindow(WindowImplementation, FigureDisplay):
    """FigureDisplay implemented as a window."""

    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
    ) -> None:
        """Initializes FigureDisplayWindow."""
        FigureDisplay.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            figure_func=figure_func,
            output=output,
            clickdata_func=clickdata_func,
        )
        WindowImplementation.__init__(self)
