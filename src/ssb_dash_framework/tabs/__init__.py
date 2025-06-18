"""Tabs for use in the application."""

from .aarsregnskap_tab import AarsregnskapTab
from .altinn_editor import AltinnSkjemadataEditor
from .bofregistry_tab import BofInformationTab
from .figuredisplay_tab import FigureDisplayTab
from .freesearch_tab import FreeSearchTab
from .pi_memorizer import Pimemorizer
from .skjemapdfviewer_tab import SkjemapdfViewerTab
from .tables_tab import EditingTableTab
from .tables_tab import MultiTableTab

__all__ = [
    "AarsregnskapTab",
    "AltinnSkjemadataEditor",
    "BofInformationTab",
    "EditingTableTab",
    "FigureDisplayTab",
    "FreeSearchTab",
    "MultiTableTab",
    "Pimemorizer",
    "SkjemapdfViewerTab",
]
