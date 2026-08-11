import importlib
import logging
import os
from typing import Literal

from ..setup.app_setup import app_setup
from ..setup.main_layout import main_layout
from .models import AppConfig
from .models import AppModules
from .models import AppSettings
from .models import ModuleConfig
from .models import VariableSelectorConfig
from .models import get_from_module_registry
from .yaml_parser import config_parser_yaml

logger = logging.getLogger(__name__)


def apply_app_settings(settings: AppSettings):
    setup_variableselector(settings.variableselector)
    app = app_setup(
        port=settings.port,
        service_prefix=settings.service_prefix,
        stylesheet=settings.stylesheet,
        enable_logging=settings.enable_logging,
        logging_level=settings.logging_level,
        log_to_file=settings.log_to_file,
    )
    return app


def setup_variableselector(
    variableselector_config: VariableSelectorConfig,
):  # This might be unnecessary due to VariableSelectorConfig having a model_post_init method.
    ...


def instantiate_module(module: ModuleConfig, type: Literal["tab", "window"]):
    if type not in ["tab", "window"]:
        raise ValueError("'type' must be either 'tab' or 'window'.")

    validation_model = get_from_module_registry(module.type)

    if type == "tab":
        if not validation_model.as_tab:
            raise ValueError(f"{module.type} is not available as a tab.")
        class_name = validation_model.as_tab
    elif type == "window":
        if not validation_model.as_window:
            raise ValueError(f"{module.type} is not available as a window.")
        class_name = validation_model.as_window

    library = importlib.import_module("ssb_dash_framework")
    cls = getattr(library, class_name, None)
    if cls is None:
        raise ValueError(f"No class named '{class_name}' found in ssb_dash_framework.")

    return cls(**module.extra_kwargs)


def build_modules(modules: AppModules):
    instantiated_tabs = []
    instantiated_windows = []
    for module in modules.tabs:
        instantiated_tabs.append(instantiate_module(module, type="tab"))
    for module in modules.windows:
        instantiated_windows.append(instantiate_module(module, type="window"))
    return instantiated_tabs, instantiated_windows


def build_app_from_config(config: AppConfig):
    app = apply_app_settings(config.app_settings)
    instantiated_tabs, instantiated_windows = build_modules(config.modules)
    return app, instantiated_tabs, instantiated_windows


def run_app_from_config(path: str):
    if path.endswith(".yaml"):
        yaml_content = config_parser_yaml(path)
        config = AppConfig(**yaml_content)
    else:
        raise NotImplementedError

    app, instantiated_tabs, instantiated_windows = build_app_from_config(config)

    app.layout = main_layout(
        window_list=instantiated_windows, tab_list=instantiated_tabs
    )

    app.run(
        debug=True,
        port=config.app_settings.port,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
