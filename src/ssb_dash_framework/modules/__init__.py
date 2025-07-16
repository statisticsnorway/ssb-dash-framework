"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .aarsregnskap import AarsregnskapTab
from .aarsregnskap import AarsregnskapWindow
from .altinn_data_capture import AltinnDataCapture
from .altinn_data_capture import AltinnDataCaptureTab
from .altinn_data_capture import AltinnDataCaptureWindow
from .bofregistry import BofInformation
from .bofregistry import BofInformationTab
from .bofregistry import BofInformationWindow
from .building_blocks import Canvas
from .building_blocks import CanvasTab
from .building_blocks import CanvasWindow
from .building_blocks import EditingTable
from .building_blocks import EditingTableTab
from .building_blocks import EditingTableWindow
from .building_blocks import FigureDisplay
from .building_blocks import FigureDisplayTab
from .building_blocks import FigureDisplayWindow
from .building_blocks import MultiModule
from .building_blocks import MultiModuleTab
from .building_blocks import MultiModuleWindow
from .freesearch import FreeSearch
from .freesearch import FreeSearchTab
from .freesearch import FreeSearchWindow
from .skjemapdfviewer import SkjemapdfViewer
from .skjemapdfviewer import SkjemapdfViewerTab
from .skjemapdfviewer import SkjemapdfViewerWindow

__all__ = [
    "Aarsregnskap",
    "AarsregnskapTab",
    "AarsregnskapWindow",
    "AltinnDataCapture",
    "AltinnDataCaptureTab",
    "AltinnDataCaptureWindow",
    "BofInformation",
    "BofInformationTab",
    "BofInformationWindow",
    "Canvas",
    "CanvasTab",
    "CanvasWindow",
    "EditingTable",
    "EditingTableTab",
    "EditingTableWindow",
    "FigureDisplay",
    "FigureDisplayTab",
    "FigureDisplayWindow",
    "FreeSearch",
    "FreeSearchTab",
    "FreeSearchWindow",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
    "SkjemapdfViewer",
    "SkjemapdfViewerTab",
    "SkjemapdfViewerWindow",
]
