from ..modules.building_blocks.figuredisplay import FigureDisplay
from ..utils import TabImplementation


class FigureDisplayTab(TabImplementation, FigureDisplay):
    def __init__(self, label, inputs, states, figure_func, output, clickdata_func):
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
