"""Tabs for use in the application."""

from .aarsregnskap_tab import AarsregnskapTab
from .bofregistry import BofInformation
from .freesearch_tab import FreeSearchTab
from .pi_memorizer import Pimemorizer
from .skjemapdfviewer_tab import SkjemapdfViewerTab
from .tables_tab import EditingTableTab

__all__ = [
    "AarsregnskapTab",
    "BofInformation",
    "EditingTableTab",
    "FreeSearchTab",
    "Pimemorizer",
    "SkjemapdfViewerTab",
]
