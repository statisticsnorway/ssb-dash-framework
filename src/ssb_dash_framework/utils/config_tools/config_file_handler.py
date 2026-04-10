from pydantic import BaseModel
from typing import Any
from typing import Union
from pydantic import discriminator

from ...modules.building_blocks.tables import EditingTableConfig

CONFIG_TYPES = Union[EditingTableConfig]

class AppConfig(BaseModel):
    """Class for validating the configuration dictionary."""
    
    tab_modules: list[Annotated[CONFIG_TYPES, Field(discriminator="type")]]    
    window_modules: list[Annotated[CONFIG_TYPES, Field(discriminator="type")]]
    


class ConfigConverter:
    """Tool for converting a configuration dictionary into a functioning app."""
    def __init__(self) -> None:
        ...