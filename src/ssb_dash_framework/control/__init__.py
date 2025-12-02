"""Utilities for creating and running controls and quality checks on your data."""

from .control_framework_base import ControlFrameworkBase
from .control_framework_base import register_control

__all__ = ["ControlFrameworkBase", "register_control"]
