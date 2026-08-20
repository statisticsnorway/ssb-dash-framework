import os
from ssb_dash_framework import (
    build_app_from_config,
    config_parser_yaml,
    AppConfig,
    main_layout,
)

# Here the base of the app is built from the supplied yaml config file
# No need to change this part of the .py file
# If you want to include more modules, you can update the app.yaml file

yaml_content = config_parser_yaml("demo/parqueteditor/app.yaml")
config = AppConfig(**yaml_content)
app, tab_list, window_list = build_app_from_config(config)

# If you are using python to add modules, you can do so below this point by
# appending instantiated modules to tab_list and window_list


# From here the app is built and started, no need to change anything below this point

app.layout = main_layout(window_list=window_list, tab_list=tab_list)

app.run(
    debug=True,
    port=config.app_settings.port,
    jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
    jupyter_mode="tab",
    threaded=False,
)