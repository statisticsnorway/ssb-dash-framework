import logging
from abc import ABC
from abc import abstractmethod

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...setup.variableselector import VariableSelector
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class FigureDisplay:

    _id_number = 0

    def __init__(self, label, inputs, states, figure_func, output, clickdata_func):
        self.module_number = FigureDisplay._id_number
        self.module_name = self.__class__.__name__
        FigureDisplay._id_number += 1

        self.label = label
        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.figure_func = figure_func
        self.output = output
        self.clickdata_func = clickdata_func

        self.module_layout = self._create_layout()
        self.module_callbacks()

        module_validator(self)

    def _create_layout(self):
        layout = html.Div(
            dcc.Graph(
                id=f"{self.module_number}-figuredisplay",
                className="figuredisplay-graph",
            ),
            className="figuredisplay",
        )
        return layout

    def layout(self):
        return self.module_layout

    def module_callbacks(self):
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(
            Output(f"{self.module_number}-figuredisplay", "figure"), *dynamic_states
        )
        def display_figure(*dynamic_states):
            return self.figure_func(*dynamic_states)

        if (
            self.output
        ):  # TODO Fix known limitation of only having a single output to the variable selector. Should be possible to return a list/tuple

            @callback(
                self.variableselector.get_output_object(variable=self.output),
                Input(f"{self.module_number}-figuredisplay", "clickData"),
                prevent_initial_call=True,
            )
            def transfer_clickdata(clickdata):
                logger.debug(clickdata)
                return self.clickdata_func(clickdata)


class MultiFigure(ABC):

    _id_number = 0

    def __init__(self, label, figure_list):
        self.module_number = FigureDisplay._id_number
        self.module_name = self.__class__.__name__
        FigureDisplay._id_number += 1

        self.label = label
        self.figure_list = figure_list
        self.module_layout = self._create_layout()
        self.module_callbacks()

        module_validator(self)

    def _create_layout(self):
        figure_divs = [
            html.Div(
                figure.module_layout,
                className="multifigure-content",
                id=f"{self.module_number}-multifigure-figure-{i}",
                style={  # Needs to be inline so that the callback logic is clearer
                    "display": "block" if i == 0 else "none",
                },
            )
            for i, figure in enumerate(self.figure_list)
        ]

        layout = html.Div(
            [
                dcc.Dropdown(
                    id=f"{self.module_number}-multifigure-dropdown",
                    options=[
                        {"label": figure.label, "value": i}
                        for i, figure in enumerate(self.figure_list)
                    ],
                    value=0,
                    clearable=False,
                ),
                html.Div(
                    children=figure_divs,
                    className="multifigure-content",
                    id=f"{self.module_number}-multifigure-content",
                ),
            ],
            className="multifigure",
        )
        return layout

    @abstractmethod
    def layout(self):
        pass

    def module_callbacks(self):
        """Register Dash callbacks for the MultiFigure component."""

        @callback(
            [
                Output(f"{self.module_number}-multifigure-figure-{i}", "style")
                for i in range(len(self.figure_list))
            ],
            Input(f"{self.module_number}-multifigure-dropdown", "value"),
        )
        def show_selected_figure(selected_index: int):
            """This callback is used for showing/hiding figures, so that all of them exists at the same time but only the one selected is shown.

            This method of showing/hiding makes it more responsive and reduces unnecessary 'id not found' type errors in the application.
            Easier to understand if styles is defined inline.
            """
            return [
                {"display": "block"} if i == selected_index else {"display": "none"}
                for i in range(len(self.figure_list))
            ]
