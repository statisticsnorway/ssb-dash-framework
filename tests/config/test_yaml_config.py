from ssb_dash_framework import AppConfig
from ssb_dash_framework import AppModules
from ssb_dash_framework import AppSettings
from ssb_dash_framework import ModuleConfig
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import build_app_from_config


def test_yaml_app_settings(config_yaml):
    AppSettings(**config_yaml["app_settings"])


def test_yaml_module_config(config_yaml):
    for module in config_yaml["modules"]["windows"]:
        ModuleConfig(**module)
    for module in config_yaml["modules"]["tabs"]:
        ModuleConfig(**module)


def test_yaml_variableselector_config(config_yaml):
    VariableSelectorConfig(**config_yaml["app_settings"]["variableselector"])


def test_yaml_app_modules(config_yaml):
    AppModules(**config_yaml["modules"])


def test_yaml_app_config(config_yaml):
    AppConfig(**config_yaml)


def test_build_app_from_config(config_yaml):
    build_app_from_config(AppConfig(**config_yaml))
