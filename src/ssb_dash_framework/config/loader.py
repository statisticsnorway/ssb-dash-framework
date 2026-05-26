import os
from typing import Literal
from ..setup.app_setup import app_setup
from .models import AppConfig
from .models import AppModules
from .models import AppSettings
from .models import VariableSelectorConfig, ModuleConfig
from .yaml_parser import config_parser_yaml


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



def build_modules(modules: AppModules):
    for module in modules.tabs:
        instantiate_module(module)
    for module in modules.windows:
        instantiate_module(module)

def build_app_from_config(config: AppConfig):
    app = apply_app_settings(config.app_settings)
    instantiate_modules(config.modules)
    return app


def run_app_from_config(path: str):
    if path.endswith(".yaml"):
        config = config_parser_yaml(path)

    app = build_app_from_config(config)

    app.run(
        debug=True,
        port=config.app_settings.port,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
