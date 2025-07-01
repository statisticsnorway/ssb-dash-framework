"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .altinn_data_capture import AltinnDataCapture
from .altinn_data_capture import AltinnDataCaptureTab
from .altinn_data_capture import AltinnDataCaptureWindow
from .bofregistry import BofInformation
from .building_blocks import Canvas
from .building_blocks import CanvasTab
from .building_blocks import CanvasWindow
from .building_blocks import EditingTable
from .building_blocks import FigureDisplay
from .building_blocks import MultiModule
from .building_blocks import MultiModuleTab
from .building_blocks import MultiModuleWindow
from .freesearch import FreeSearch
from .skjemapdfviewer import SkjemapdfViewer

__all__ = [
    "Aarsregnskap",
    "AltinnDataCapture",
    "AltinnDataCaptureTab",
    "AltinnDataCaptureWindow",
    "BofInformation",
    "Canvas",
    "CanvasTab",
    "CanvasWindow",
    "EditingTable",
    "FigureDisplay",
    "FreeSearch",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
    "SkjemapdfViewer",
]
