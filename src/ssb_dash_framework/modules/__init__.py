"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .bofregistry import BofInformation
from .building_blocks import EditingTable
from .building_blocks import FigureDisplay
from .building_blocks import MultiModule
from .freesearch import FreeSearch
from .skjemapdfviewer import SkjemapdfViewer
from .building_blocks import MultiModule, MultiModuleTab, MultiModuleWindow

__all__ = [
    "Aarsregnskap",
    "BofInformation",
    "EditingTable",
    "FigureDisplay",
    "FreeSearch",
    "MultiModule",
    "MultiModule",
    "SkjemapdfViewer",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
]
