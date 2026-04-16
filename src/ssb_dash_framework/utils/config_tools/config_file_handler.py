from pydantic import BaseModel
from typing import Any, Annotated
from typing import Union
from pydantic import Field
import yaml
from pathlib import Path
from ...modules.building_blocks.tables import EditingTableConfig

CONFIG_TYPES = Union[EditingTableConfig]


class AppConfig(BaseModel):
    """Class for validating the configuration dictionary."""

    tab_modules: list[Annotated[CONFIG_TYPES, Field(
        #discriminator="type"
        )]]
    window_modules: list[Annotated[CONFIG_TYPES, Field(
        #discriminator="type"
        )]]


class ConfigConverter:
    """Tool for converting a configuration dictionary into a functioning app."""

    def __init__(self) -> None: ...


class IncludeLoader(yaml.SafeLoader):
    """YAML loader that supports !include tags for file splitting."""

    def __init__(self, stream):
        self._root = Path(stream.name).parent
        super().__init__(stream)


def _include_constructor(loader: IncludeLoader, node: yaml.Node):
    include_path = loader._root / loader.construct_scalar(node)
    with open(include_path) as f:
        # Create a new IncludeLoader so nested !includes resolve
        # relative to the included file's own directory
        return yaml.load(f, Loader=IncludeLoader)


IncludeLoader.add_constructor("!include", _include_constructor)


def config_parser_yaml(path: str | Path) -> dict:
    """Load a YAML config file, resolving any !include tags."""
    with open(path) as f:
        config = yaml.load(f, Loader=IncludeLoader)
    return config
