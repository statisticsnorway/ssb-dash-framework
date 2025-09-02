"""SSB Dash Framework."""

from .control import ControlFrameworkBase
from .modules import Aarsregnskap
from .modules import AarsregnskapTab
from .modules import AarsregnskapWindow
from .modules import AggDistPlotter
from .modules import AggDistPlotterTab
from .modules import AggDistPlotterWindow
from .modules import AltinnControlView
from .modules import AltinnControlViewWindow
from .modules import AltinnDataCapture
from .modules import AltinnDataCaptureTab
from .modules import AltinnDataCaptureWindow
from .modules import AltinnSkjemadataEditor
from .modules import BofInformation
from .modules import BofInformationTab
from .modules import BofInformationWindow
from .modules import Canvas
from .modules import CanvasTab
from .modules import CanvasWindow
from .modules import Control
from .modules import ControlWindow
from .modules import EditingTable
from .modules import EditingTableTab
from .modules import EditingTableWindow
from .modules import FigureDisplay
from .modules import FigureDisplayTab
from .modules import FigureDisplayWindow
from .modules import FreeSearch
from .modules import FreeSearchTab
from .modules import FreeSearchWindow
from .modules import MapDisplay
from .modules import MapDisplayTab
from .modules import MapDisplayWindow
from .modules import MultiModule
from .modules import MultiModuleTab
from .modules import MultiModuleWindow
from .modules import PimemorizerTab
from .modules import SkjemapdfViewer
from .modules import SkjemapdfViewerTab
from .modules import SkjemapdfViewerWindow
from .modules import VisualizationBuilder
from .modules import VisualizationBuilderWindow
from .setup import VariableSelector
from .setup import VariableSelectorOption
from .setup import app_setup
from .setup import main_layout
from .setup import set_variables
from .utils import AlertHandler
from .utils import DatabaseBuilderAltinnEimerdb
from .utils import DebugInspector
from .utils import TabImplementation
from .utils import WindowImplementation
from .utils import create_alert
from .utils import enable_app_logging
from .utils import module_validator
from .utils import sidebar_button

# from .modals import HBMethod
# from .utils import _get_kostra_r
# from .utils import hb_method
# from .utils import th_error

__all__ = [
    "Aarsregnskap",
    "AarsregnskapTab",
    "AarsregnskapWindow",
    "AggDistPlotter",
    "AggDistPlotterTab",
    "AggDistPlotterWindow",
    "AlertHandler",
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
    "ControlFrameworkBase",
    "ControlWindow",
    "DatabaseBuilderAltinnEimerdb",
    "DebugInspector",
    "EditingTable",
    "EditingTableTab",
    "EditingTableWindow",
    "FigureDisplay",
    "FigureDisplayTab",
    "FigureDisplayWindow",
    "FreeSearch",
    "FreeSearchTab",
    "FreeSearchWindow",
    # "HBMethod",
    # "HBMethodWindow",
    "MapDisplay",
    "MapDisplayTab",
    "MapDisplayWindow",
    "MultiModule",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleTab",
    "MultiModuleWindow",
    "MultiModuleWindow",
    "MultiModuleWindow",
    "PimemorizerTab",
    "SkjemapdfViewer",
    "SkjemapdfViewerTab",
    "SkjemapdfViewerWindow",
    "TabImplementation",
    "VariableSelector",
    "VariableSelectorOption",
    "VisualizationBuilder",
    "VisualizationBuilderWindow",
    "WindowImplementation",
    "app_setup",
    "create_alert",
    "enable_app_logging",
    "main_layout",
    "module_validator",
    "set_variables",
    "sidebar_button",
    #    "hb_method",
    #    "_get_kostra_r",
    #    "th_error",
]
