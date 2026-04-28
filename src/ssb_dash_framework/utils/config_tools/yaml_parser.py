"""
config_yaml_parser.py  —  Step 1
=================================
Parse YAML files into plain Python objects (dicts / lists / scalars).

The only responsibility of this module is to read files from disk and resolve
``!include`` directives.  No validation, no class construction.

Public API
----------
    load_yaml(path) -> Any
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .parsed_config_models import load_config

class _IncludeLoader(yaml.SafeLoader):
    """SafeLoader extended with an ``!include`` constructor.

    Relative paths in ``!include`` tags are resolved relative to the directory
    of the *including* file, so nested includes work correctly regardless of
    the working directory.
    """

    def __init__(self, stream: Any) -> None:
        self._root: Path = (
            Path(stream.name).parent if hasattr(stream, "name") else Path.cwd()
        )
        super().__init__(stream)


def _include_constructor(loader: _IncludeLoader, node: yaml.ScalarNode) -> Any:
    raw_path = loader.construct_scalar(node)
    include_path = Path(raw_path)
    if not include_path.is_absolute():
        include_path = loader._root / include_path
    return load_yaml(include_path)


_IncludeLoader.add_constructor("!include", _include_constructor)


def load_yaml(path: str | Path) -> Any:
    """Read *path* and return the parsed Python object.

    ``!include`` tags are resolved recursively.  The return type mirrors the
    YAML structure: a mapping becomes a ``dict``, a sequence becomes a
    ``list``, scalars become ``str`` / ``int`` / ``float`` / ``bool`` / ``None``.
    """
    with open(path, encoding="utf-8") as fh:
        read_config_file = yaml.load(fh, Loader=_IncludeLoader)
        print(read_config_file)
        return load_config(read_config_file)