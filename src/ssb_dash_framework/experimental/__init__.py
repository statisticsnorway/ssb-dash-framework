"""Experimental modules that may change without notice. Import them from here explicitly."""

from typing import Any

__all__ = [
    "AltinnMacroModuleDataHandler",
    "MacroModule",
    "MacroModuleDataHandler",
]


def __getattr__(name: str) -> Any:
    # Imported lazily: the top-level package imports this package before its modules.
    if name in __all__:
        from ..modules import macro_module

        return getattr(macro_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
