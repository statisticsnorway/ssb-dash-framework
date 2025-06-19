"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .bofregistry import BofInformation
from .building_blocks import EditingTable
from .building_blocks import FigureDisplay
from .building_blocks import MultiFigure
from .building_blocks import MultiTable
from .freesearch import FreeSearch
from .skjemapdfviewer import SkjemapdfViewer

__all__ = [
    "Aarsregnskap",
    "BofInformation",
    "EditingTable",
    "FigureDisplay",
    "FreeSearch",
    "MultiFigure",
    "MultiTable",
    "SkjemapdfViewer",
]
