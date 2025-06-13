"""Functionality for setting up an application based on tabs and windows.

This module provides the fundamental building blocks for using our framework.

Note that some modules are possible to use without using the framework itself, but that is a more advanced use case.
"""

from .app_setup import app_setup
from .main_layout import main_layout
from .variableselector import VariableSelector
from .variableselector import VariableSelectorOption
from .variableselector import set_variables

__all__ = [
    "VariableSelector",
    "VariableSelectorOption",
    "app_setup",
    "main_layout",
    "set_variables",
]
