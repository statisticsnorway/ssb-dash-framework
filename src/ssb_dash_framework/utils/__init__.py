"""Module containing utility and helper functions shared between components in the framework."""

from .alert_handler import AlertHandler
from .alert_handler import create_alert
from .app_logger import enable_app_logging
from .config import IDENT_VAR
from .datahelper import DatabaseBuilderAltinnEimerdb
from .datahelper import DemoDataCreator
from .datahelper import create_database
from .datahelper import create_database_engine
from .debugger_modal import DebugInspector

# from .r_helpers import _get_kostra_r
# from .r_helpers import hb_method
# from .r_helpers import th_error
from .functions import sidebar_button
from .implementations import TabImplementation
from .implementations import WindowImplementation
from .module_validation import module_validator

__all__ = [
    "IDENT_VAR",
    "AlertHandler",
    "DatabaseBuilderAltinnEimerdb",
    "DebugInspector",
    "DemoDataCreator",
    "TabImplementation",
    "WindowImplementation",
    "create_alert",
    "create_database",
    "create_database_engine",
    "enable_app_logging",
    "module_validator",
    "sidebar_button",
    # "_get_kostra_r",
    # "hb_method",
    # "th_error",
]
