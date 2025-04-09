"""SSB Dash Framework."""
from .setup import app_setup
from .setup import main_layout
from .setup import VariableSelectorOption
from .modules import FreeSearch
from .tabs import FreeSearchTab
from .windows import FreeSearchWindow
from .modules import RateModel
from .windows import RateModelWindow

for_setup = [
    "VariableSelectorOption"
]



ratemodel = [
    "RateModel",
    "RateModelWindow"
]

freesearch = [
    "FreeSearch",
    "FreeSearchTab",
    "FreeSearchWindow"
]


# Defines top level if used in wildcard import
__all__ = [*for_setup, *ratemodel, *freesearch]