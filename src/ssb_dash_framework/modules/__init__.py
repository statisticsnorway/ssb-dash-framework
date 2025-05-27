"""Modules for use in the application, directly or implmented as a view (tab/window)."""

from .aarsregnskap import Aarsregnskap
from .freesearch import FreeSearch
from .skjemadataviewer import SkjemadataViewer
from .skjemapdfviewer import SkjemapdfViewer
from .tables import EditingTable
from .tables import Multitable

__all__ = [
    "Aarsregnskap",
    "EditingTable",
    "FreeSearch",
    "Multitable",
    "SkjemadataViewer",
    "SkjemapdfViewer",
]
