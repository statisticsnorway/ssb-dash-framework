import logging
from abc import ABC
from abc import abstractmethod

from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ..setup.variableselector import VariableSelector
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class FigureDisplay(ABC):

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

    @abstractmethod
    def layout(self):
        pass

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

        if self.output:

            @callback(
                self.variableselector.get_output_object(variable=self.output),
                Input(f"{self.module_number}-figuredisplay", "clickData"),
                prevent_initial_call=True,
            )
            def transfer_clickdata(clickdata):
                logger.debug(clickdata)
                return self.clickdata_func(clickdata)
