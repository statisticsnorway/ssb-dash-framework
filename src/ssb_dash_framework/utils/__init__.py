"""Module containing utility and helper functions shared between components in the framework."""

import importlib
import os
import pkgutil
from collections.abc import Iterator
from typing import Any

from .functions import _get_kostra_r

current_dir = os.path.dirname(__file__)
__all__: list[str] = []

module_iter: Iterator[tuple[Any, str, bool]] = pkgutil.iter_modules([current_dir])

for _module_finder, module_name, _is_pkg in module_iter:
    module = importlib.import_module(f".{module_name}", package=__name__)
    for attr_name in dir(module):
        if not attr_name.startswith("_"):
            globals()[attr_name] = getattr(module, attr_name)
            __all__.append(attr_name)
