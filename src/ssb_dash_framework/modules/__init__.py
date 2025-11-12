"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .aarsregnskap import AarsregnskapTab
from .aarsregnskap import AarsregnskapWindow
from .agg_dist_plotter import AggDistPlotter
from .agg_dist_plotter import AggDistPlotterTab
from .agg_dist_plotter import AggDistPlotterWindow
from .altinn_control_view import AltinnControlView
from .altinn_control_view import AltinnControlViewWindow
from .altinn_data_capture import AltinnDataCapture
from .altinn_data_capture import AltinnDataCaptureTab
from .altinn_data_capture import AltinnDataCaptureWindow
from .altinn_editor import AltinnSkjemadataEditor
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
from .building_blocks import MapDisplay
from .building_blocks import MapDisplayTab
from .building_blocks import MapDisplayWindow
from .building_blocks import MultiModule
from .building_blocks import MultiModuleTab
from .building_blocks import MultiModuleWindow
from .control import Control
from .control import ControlWindow
from .freesearch import FreeSearch
from .freesearch import FreeSearchTab
from .freesearch import FreeSearchWindow
from .hb_method import HBMethod
from .hb_method import HBMethodWindow
from .pi_memorizer import PimemorizerTab
from .skjemapdfviewer import SkjemapdfViewer
from .skjemapdfviewer import SkjemapdfViewerTab
from .skjemapdfviewer import SkjemapdfViewerWindow
from .visualizationbuilder import VisualizationBuilder
from .visualizationbuilder import VisualizationBuilderWindow

__all__ = [
    "Aarsregnskap",
    "AarsregnskapTab",
    "AarsregnskapWindow",
    "AggDistPlotter",
    "AggDistPlotterTab",
    "AggDistPlotterWindow",
    "AltinnControlView",
    "AltinnControlViewWindow",
    "AltinnDataCapture",
    "AltinnDataCaptureTab",
    "AltinnDataCaptureWindow",
    "AltinnSkjemadataEditor",
    "BofInformation",
    "BofInformationTab",
    "BofInformationWindow",
    "Canvas",
    "CanvasTab",
    "CanvasWindow",
    "Control",
    "ControlWindow",
    "EditingTable",
    "EditingTableTab",
    "EditingTableWindow",
    "FigureDisplay",
    "FigureDisplayTab",
    "FigureDisplayWindow",
    "FreeSearch",
    "FreeSearchTab",
    "FreeSearchWindow",
    "HBMethod",
    "HBMethodWindow",
    "MapDisplay",
    "MapDisplayTab",
    "MapDisplayWindow",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
    "PimemorizerTab",
    "SkjemapdfViewer",
    "SkjemapdfViewerTab",
    "SkjemapdfViewerWindow",
    "VisualizationBuilder",
    "VisualizationBuilderWindow",
]
