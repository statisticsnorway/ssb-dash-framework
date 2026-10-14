"""Modules for use in the application, implmented as a view (tab/window) or directly with a custom layout implementation."""

from .aarsregnskap import Aarsregnskap
from .altinn_control_view import ControlView
from .bofregistry import BofInformation
from .building_blocks import Canvas
from .building_blocks import EditingTable
from .building_blocks import FigureDisplay
from .building_blocks import MapDisplay
from .building_blocks import MultiModule
from .data_editor import DataEditor
from .data_editor import DataEditorHistory
from .data_editor import DataEditorContactInfo
from .data_editor import DataEditorInfoRow
from .data_editor import DataEditorSidebarComment
from .data_editor import DataEditorSidebarEditingStatus
from .data_editor import DataEditorSupportTable
from .data_editor import DataEditorSupportTables
from .data_editor import DataEditorTable
from .data_editor import DataEditorTableSelector
from .data_editor import DataViewCustom
from .data_editor import EditorSettings
from .data_editor import StandardDataHandler
from .nspek import Naeringsspesifikasjon
from .nspek import NaeringsspesifikasjonTab
from .nspek import NaeringsspesifikasjonWindow
from .nspek import NspekControls
from .nspek import NspekControlViewTab
from .nspek import NspekControlViewWindow
from .nspek import NspekDashboard
from .nspek import NspekDashboardTab
from .nspek import NspekDashboardWindow
from .parquet_editor import ParquetEditor
from .parquet_editor import ParquetEditorChangelog
from .parquet_editor import apply_edits
from .parquet_editor import export_from_parqueteditor
from .parquet_editor import get_export_log_path
from .parquet_editor import get_log_path
from .pi_memorizer import PimemorizerTab
from .skjemapdfviewer import SkjemapdfViewer

__all__ = [
    "Aarsregnskap",
    "BofInformation",
    "Canvas",
    "ControlView",
    "DataEditor",
    "DataEditorHistory",
    "DataEditorContactInfo",
    "DataEditorInfoRow",
    "DataEditorSidebarComment",
    "DataEditorSidebarEditingStatus",
    "DataEditorSupportTable",
    "DataEditorSupportTables",
    "DataEditorTable",
    "DataEditorTableSelector",
    "DataViewCustom",
    "EditingTable",
    "EditorSettings",
    "FigureDisplay",
    "MapDisplay",
    "MultiModule",
    "Naeringsspesifikasjon",
    "NaeringsspesifikasjonTab",
    "NaeringsspesifikasjonWindow",
    "NspekControlViewTab",
    "NspekControlViewWindow",
    "NspekControls",
    "NspekDashboard",
    "NspekDashboardTab",
    "NspekDashboardWindow",
    "ParquetEditor",
    "ParquetEditorChangelog",
    "PimemorizerTab",
    "SkjemapdfViewer",
    "StandardDataHandler",
    "apply_edits",
    "export_from_parqueteditor",
    "get_export_log_path",
    "get_log_path",
]
