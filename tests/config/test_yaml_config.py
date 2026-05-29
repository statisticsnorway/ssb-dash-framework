from ssb_dash_framework.config.models import AppConfig
from ssb_dash_framework.config.models import AppModules
from ssb_dash_framework.config.models import AppSettings
from ssb_dash_framework.config.models import ModuleConfig


def test_yaml_app_settings(config_yaml):
    AppSettings(**config_yaml["app_settings"])


def test_yaml_module_config(config_yaml):
    for module in config_yaml["modules"]["windows"]:
        ModuleConfig(**module)
    for module in config_yaml["modules"]["tabs"]:
        ModuleConfig(**module)


def test_yaml_app_modules(config_yaml):
    AppModules(**config_yaml["modules"])


def test_yaml_app_config(config_yaml):
    AppConfig(**config_yaml)
