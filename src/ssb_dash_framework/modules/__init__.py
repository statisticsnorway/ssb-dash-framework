"""Modules for use in the application, directly or implmented as a view (tab/window)."""

from .aarsregnskap import Aarsregnskap
from .bofregistry import BofInformation
from .freesearch import FreeSearch
from .skjemapdfviewer import SkjemapdfViewer
from .tables import EditingTable
from .tables import MultiTable

__all__ = [
    "Aarsregnskap",
    "BofInformation",
    "EditingTable",
    "FreeSearch",
    "MultiTable",
    "SkjemapdfViewer",
]
