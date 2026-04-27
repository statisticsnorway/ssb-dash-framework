from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import (
    DataViewCustom,
)


def parse_config_dict(config):
    if isinstance(config, list):
        for component in config:
            parse_config_dict(component)
    if config["type"] == "customview":
        config = DataViewCustom.from_dict(config)
        return config
    print(config)
