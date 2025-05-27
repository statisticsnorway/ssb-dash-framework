"""Windows for use in the application."""

from .freesearch_window import FreeSearchWindow
from .skjemapdfviewer_window import SkjemapdfViewerWindow
from .tables_window import EditingTableWindow
from .tables_window import MultiTableWindow

__all__ = [
    "EditingTableWindow",
    "FreeSearchWindow",
    "MultiTableWindow",
    "SkjemapdfViewerWindow",
]
