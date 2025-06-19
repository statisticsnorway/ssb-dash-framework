from ..modules.building_blocks.figuredisplay import FigureDisplay
from ..modules.building_blocks.figuredisplay import MultiFigure
from ..utils import WindowImplementation


class FigureDisplayWindow(WindowImplementation, FigureDisplay):
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
        WindowImplementation.__init__(self)


class MultiFigureWindow(WindowImplementation, MultiFigure):
    def __init__(self, label, figure_list):
        MultiFigure.__init__(
            self,
            label=label,
            figure_list=figure_list,
        )
        WindowImplementation.__init__(self)
