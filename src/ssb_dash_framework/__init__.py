"""SSB Dash Framework."""

from . import control
from . import modals
from . import setup
from . import tabs

# Re-import functions and classes from submodules explicitly for top-level access
from .setup import main_layout
from .utils.alert_handler import create_alert

# Defines top level if used in wildcard import
__all__ = ["control", "create_alert", "main_layout", "modals", "setup", "tabs"]
