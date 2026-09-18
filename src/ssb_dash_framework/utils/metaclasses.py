import importlib
from typing import Any,TypeVar


class BaseDatahandler:
    pass

T = TypeVar("T", bound=BaseDatahandler)


def instantiate_class_instance(name: str, meta_class: type[T]) -> T:
    """Resolves a data handler referenced by name in a config file."""
    cls: Any = getattr(importlib.import_module("ssb_dash_framework"), name, None)
    if cls is None or not isinstance(cls, type) or not issubclass(cls, meta_class):
        raise ValueError(f"No data handler named '{name}' found in ssb_dash_framework.")
    return cls()