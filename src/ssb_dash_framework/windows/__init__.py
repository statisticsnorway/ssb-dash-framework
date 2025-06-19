"""Windows for use in the application."""

from .bofregistry_window import BofInformationWindow
from .figuredisplay_window import FigureDisplayWindow
from .freesearch_window import FreeSearchWindow
from .skjemapdfviewer_window import SkjemapdfViewerWindow
from .tables_window import EditingTableWindow

__all__ = [
    "BofInformationWindow",
    "EditingTableWindow",
    "FigureDisplayWindow",
    "FreeSearchWindow",
    "SkjemapdfViewerWindow",
]
