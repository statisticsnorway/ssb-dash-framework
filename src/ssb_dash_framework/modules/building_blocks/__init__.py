"""Modules here are basic, flexible and mostly wrap functionality to simplify integration with the framework.

The purpose of this type of module is to enable the user to create their own customizable views, while still being easy to integrate with the rest of the framework.
"""

from .figuredisplay import FigureDisplay
from .figuredisplay import MultiFigure
from .tables import EditingTable
from .tables import MultiTable

__all__ = [
    "EditingTable",
    "FigureDisplay",
    "MultiFigure",
    "MultiTable",
]
