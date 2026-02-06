"""Modules here are basic, flexible and mostly wrap functionality to simplify integration with the framework.

The purpose of this type of module is to enable the user to create their own customizable views, while still being easy to integrate with the rest of the framework.
"""

from .canvas import Canvas
from .canvas import CanvasTab
from .canvas import CanvasWindow
from .figuredisplay import FigureDisplay
from .figuredisplay import FigureDisplayTab
from .figuredisplay import FigureDisplayWindow
from .map_display import MapDisplay
from .map_display import MapDisplayTab
from .map_display import MapDisplayWindow
from .microlayout import MicroLayoutAIO
from .multimodule import MultiModule
from .multimodule import MultiModuleTab
from .multimodule import MultiModuleWindow
from .tables import EditingTable
from .tables import EditingTableTab
from .tables import EditingTableWindow

__all__ = [
    "Canvas",
    "CanvasTab",
    "CanvasWindow",
    "EditingTable",
    "EditingTableTab",
    "EditingTableWindow",
    "FigureDisplay",
    "FigureDisplayTab",
    "FigureDisplayWindow",
    "MapDisplay",
    "MapDisplayTab",
    "MapDisplayWindow",
    "MicroLayoutAIO",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
]
