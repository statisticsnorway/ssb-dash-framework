"""Tabs for use in the application."""

from .aarsregnskap_tab import AarsregnskapTab
from .bofregistry_tab import BofInformationTab
from .freesearch_tab import FreeSearchTab
from .pi_memorizer import Pimemorizer
from .skjemapdfviewer_tab import SkjemapdfViewerTab
from .tables_tab import EditingTableTab
from .tables_tab import MultitableTab

__all__ = [
    "AarsregnskapTab",
    "BofInformationTab",
    "EditingTableTab",
    "FreeSearchTab",
    "MultitableTab",
    "Pimemorizer",
    "SkjemapdfViewerTab",
]
