"""SSB Dash Framework."""

# TODO remove this import after refactoring into module as tab/window design.
from .modals import AltinnControlView
from .modals import AltinnDataCapture
from .modals import Control
from .modals import HBMethod
from .modals import VisualizationBuilder
from .modules import aarsregnskap
from .modules import freesearch
from .modules import skjemadataviewer
from .modules import skjemapdfviewer
from .setup import app_setup
from .setup import main_layout
from .setup import variableselector
from .tabs import aarsregnskap_tab
from .tabs import bofregistry
from .tabs import freesearch_tab
from .tabs import generic
from .tabs import pi_memorizer
from .windows import FreeSearchWindow
from .windows import SkjemapdfViewerWindow

__all__ = [
    "AltinnControlView",
    "AltinnDataCapture",
    "Control",
    "FreeSearchWindow",
    "HBMethod",
    "SkjemapdfViewerWindow",
    "VisualizationBuilder",
    "aarsregnskap",
    "aarsregnskap_tab",
    "app_setup",
    "bofregistry",
    "freesearch",
    "freesearch_tab",
    "generic",
    "main_layout",
    "pi_memorizer",
    "skjemadataviewer",
    "skjemapdfviewer",
    "variableselector",
]
