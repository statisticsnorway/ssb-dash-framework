"""Functionality for setting up an application based on tabs and modals."""

import importlib
import os
import pkgutil
from collections.abc import Iterator
from typing import Any

current_dir = os.path.dirname(__file__)
__all__: list[str] = []

module_iter: Iterator[tuple[Any, str, bool]] = pkgutil.iter_modules([current_dir])

for _module_finder, module_name, _is_pkg in module_iter:
    module = importlib.import_module(f".{module_name}", package=__name__)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # Check if the attribute has a __module__ attribute and filter based on package name
        if (
            not attr_name.startswith("_")
            and hasattr(attr, "__module__")  # Ensure __module__ exists
            and attr.__module__.startswith(
                __name__
            )  # Only include attributes from your package
        ):
            globals()[attr_name] = attr
            __all__.append(attr_name)
