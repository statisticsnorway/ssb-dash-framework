"""Functionality for setting up an application based on tabs and modals."""

from .app_setup import app_setup
from .main_layout import main_layout
from .variableselector import VariableSelector
from .variableselector import VariableSelectorOption
from .variableselector import set_variables
from .variableselector import VariableSelectorConfig

__all__ = [
    "VariableSelector",
    "VariableSelectorOption",
    "VariableSelectorConfig",
    "app_setup",
    "main_layout",
    "set_variables",
]
