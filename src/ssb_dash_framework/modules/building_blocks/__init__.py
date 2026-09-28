"""Modules here are basic, flexible and mostly wrap functionality to simplify integration with the framework.

The purpose of this type of module is to enable the user to create their own customizable views, while still being easy to integrate with the rest of the framework.
"""

from .canvas import Canvas
from .figuredisplay import FigureDisplay
from .map_display import MapDisplay
from .multimodule import MultiModule
from .tables import EditingTable


__all__ = [
    "Canvas",
    "EditingTable",
    "FigureDisplay",
    "MapDisplay",
    "MultiModule",
]
