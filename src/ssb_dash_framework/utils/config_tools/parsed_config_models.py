import logging
from typing import Any

from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import (
    DataViewCustom,
)

logger = logging.getLogger(__name__)

def load_config(config: str | dict[Any, Any] | list[Any]):
    logger.debug(f"Parsing config part:\n{config}")
    parsed_config = []
    if isinstance(config, list):
        for component in config:
            parsed_config = load_config(component)
    if isinstance(config, dict):
        if config["type"] == "customview":
            module = DataViewCustom.from_dict(config)
            parsed_config.append(module)
            return parsed_config
        else:
            raise NotImplementedError(f"Currently yaml based setup does not support: {config['type']}")
    return parsed_config

