"""SSB Dash Framework."""

from .modals import Control
from .modals import HBMethod
from .modals import VisualizationBuilder

# from .windows import RateModelWindow
from .modules import Aarsregnskap
from .modules import FreeSearch

# from .modules import RateModel
from .modules import SkjemadataViewer
from .modules import SkjemapdfViewer
from .setup import VariableSelectorOption
from .setup import app_setup
from .setup import main_layout
from .tabs import AarsregnskapTab
from .tabs import BofInformation
from .tabs import FreeSearchTab
from .tabs import SkjemapdfViewerTab
from .tabs import EditingTable # TODO: Clean up and make into module
from .windows import FreeSearchWindow

aarsregnskap = ["Aarsregnskap", "AarsregnskapTab"]

for_setup = ["app_setup", "main_layout", "VariableSelectorOption"]

# ratemodel = ["RateModel", "RateModelWindow"]

table = [
    "EditingTable"
]

freesearch = ["FreeSearch", "FreeSearchTab", "FreeSearchWindow"]

hb_method = ["HBMethod"]

# Defines top level if used in wildcard import
__all__ = [
    *for_setup,
    # *ratemodel,
    *table,
    *freesearch,
    *hb_method,
    *aarsregnskap,
]
