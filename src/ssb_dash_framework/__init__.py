"""SSB Dash Framework."""

from .modals import AltinnControlView
from .modals import AltinnDataCapture
from .modals import Control
from .modals import HBMethod
from .modals import VisualizationBuilder

modals = [  # TODO Remove these after refactoring
    AltinnControlView,
    AltinnDataCapture,
    Control,
    HBMethod,
    VisualizationBuilder,
]

from .modules import Aarsregnskap
from .modules import FreeSearch
from .modules import SkjemadataViewer
from .modules import SkjemapdfViewer

modules = [
    Aarsregnskap,
    FreeSearch,
    SkjemadataViewer,
    SkjemapdfViewer,
]

from .setup import VariableSelector
from .setup import VariableSelectorOption
from .setup import app_setup
from .setup import main_layout

setup = [
    VariableSelector,
    VariableSelectorOption,
    app_setup,
    main_layout,
]

from .tabs import AarsregnskapTab
from .tabs import BofInformation
from .tabs import EditingTableLong
from .tabs import FreeSearchTab
from .tabs import Pimemorizer
from .tabs import SkjemapdfViewerTab

tabs = [
    AarsregnskapTab,
    BofInformation,
    FreeSearchTab,
    Pimemorizer,
    SkjemapdfViewerTab,
    EditingTableLong,
]

from .utils import AlertHandler
from .utils import DebugInspector
from .utils import _get_kostra_r
from .utils import create_alert
from .utils import hb_method
from .utils import sidebar_button
from .utils import th_error

utils = [
    AlertHandler,
    DebugInspector,
    hb_method,
    sidebar_button,
    th_error,
    _get_kostra_r,
]

from .windows import FreeSearchWindow
from .windows import SkjemapdfViewerWindow

windows = [
    FreeSearchWindow,
    SkjemapdfViewerWindow,
]

__all__ = [
    *modals,
    *modules,
    *setup,
    *tabs,
    *utils,
    *windows,
]
