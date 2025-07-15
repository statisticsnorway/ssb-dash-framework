"""Modals for use in the application."""

from .agg_dist_plotter import AggDistPlotter
from .agg_dist_plotter import AggDistPlotterTab
from .agg_dist_plotter import AggDistPlotterWindow
from .altinn_control_view import AltinnControlView
from .control import Control
from .visualizationbuilder import VisualizationBuilder

# from .hb_method import HBMethod

__all__ = [
    "AggDistPlotter",
    "AggDistPlotterTab",
    "AggDistPlotterWindow",
    "AltinnControlView",
    "Control",
    #    "HBMethod",
    "VisualizationBuilder",
]
