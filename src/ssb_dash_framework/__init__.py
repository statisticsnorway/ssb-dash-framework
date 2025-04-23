"""SSB Dash Framework."""

from .modals import Control
from .modals import HBMethod
from .modals import VisualizationBuilder
from .modules import FreeSearch
#from .modules import RateModel
from .modules import SkjemadataViewer
from .setup import VariableSelectorOption
from .setup import app_setup
from .setup import main_layout
from .tabs import Aarsregnskap
from .tabs import BofInformation
from .tabs import EditingTableLong
from .tabs import FreeSearchTab
from .windows import FreeSearchWindow
#from .windows import RateModelWindow

for_setup = ["VariableSelectorOption"]

#ratemodel = ["RateModel", "RateModelWindow"]

freesearch = ["FreeSearch", "FreeSearchTab", "FreeSearchWindow"]

hb_method = ["HBMethod"]

# Defines top level if used in wildcard import
__all__ = [
    *for_setup, 
    #*ratemodel,
    *freesearch,
    *hb_method
]
