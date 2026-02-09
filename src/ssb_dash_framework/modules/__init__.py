"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .aarsregnskap import AarsregnskapTab
from .aarsregnskap import AarsregnskapWindow
from .agg_dist_plotter import AggDistPlotter
from .agg_dist_plotter import AggDistPlotterTab
from .agg_dist_plotter import AggDistPlotterWindow
from .altinn_control_view import AltinnControlViewTab
from .altinn_control_view import AltinnControlViewWindow
from .altinn_control_view import ControlView
from .altinn_control_view import ControlViewTab
from .altinn_control_view import ControlViewWindow
from .altinn_data_capture import AltinnDataCapture
from .altinn_data_capture import AltinnDataCaptureTab
from .altinn_data_capture import AltinnDataCaptureWindow
from .altinn_editor import AltinnSkjemadataEditor
from .altinn_editor import AltinnSupportTable
from .bedriftstabell import Bedriftstabell
from .bedriftstabell import BedriftstabellTab
from .bedriftstabell import BedriftstabellWindow
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
from .building_blocks import MicroLayoutAIO
from .building_blocks import MultiModule
from .building_blocks import MultiModuleTab
from .building_blocks import MultiModuleWindow
from .freesearch import FreeSearch
from .freesearch import FreeSearchTab
from .freesearch import FreeSearchWindow
from .hb_method import HBMethod
from .hb_method import HBMethodWindow
from .macro_module import MacroModule
from .macro_module import MacroModuleTab
from .macro_module import MacroModuleWindow
from .nspek import Naeringsspesifikasjon
from .nspek import NaeringsspesifikasjonTab
from .nspek import NaeringsspesifikasjonWindow
from .parquet_editor import ParquetEditor
from .parquet_editor import ParquetEditorChangelog
from .parquet_editor import apply_edits
from .parquet_editor import export_from_parqueteditor
from .parquet_editor import get_export_log_path
from .parquet_editor import get_log_path
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
    "AltinnControlViewTab",
    "AltinnControlViewWindow",
    "AltinnDataCapture",
    "AltinnDataCaptureTab",
    "AltinnDataCaptureWindow",
    "AltinnSkjemadataEditor",
    "AltinnSupportTable",
    "Bedriftstabell",
    "BedriftstabellTab",
    "BedriftstabellWindow",
    "BofInformation",
    "BofInformationTab",
    "BofInformationWindow",
    "Canvas",
    "CanvasTab",
    "CanvasWindow",
    "ControlView",
    "ControlViewTab",
    "ControlViewWindow",
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
    "MacroModule",
    "MacroModuleTab",
    "MacroModuleWindow",
    "MapDisplay",
    "MapDisplayTab",
    "MapDisplayWindow",
    "MicroLayoutAIO",
    "MultiModule",
    "MultiModuleTab",
    "MultiModuleWindow",
    "Naeringsspesifikasjon",
    "NaeringsspesifikasjonTab",
    "NaeringsspesifikasjonWindow",
    "ParquetEditor",
    "ParquetEditorChangelog",
    "PimemorizerTab",
    "SkjemapdfViewer",
    "SkjemapdfViewerTab",
    "SkjemapdfViewerWindow",
    "VisualizationBuilder",
    "VisualizationBuilderWindow",
    "apply_edits",
    "export_from_parqueteditor",
    "get_export_log_path",
    "get_log_path",
]
