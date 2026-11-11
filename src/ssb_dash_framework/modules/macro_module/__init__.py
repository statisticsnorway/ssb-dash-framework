"""A generic macro module for drilling down from aggregated values to observations.

Experimental: import it from `ssb_dash_framework.experimental`.
"""

from .altinn_data_handler import AltinnMacroModuleDataHandler
from .data_handler import MacroModuleDataHandler
from .macro_module import MacroModule

__all__ = [
    "AltinnMacroModuleDataHandler",
    "MacroModule",
    "MacroModuleDataHandler",
]
