import yaml

from ssb_dash_framework import AppConfig
from ssb_dash_framework import AppModules
from ssb_dash_framework import AppSettings
from ssb_dash_framework import HBMethod
from ssb_dash_framework import ModuleConfig
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import get_from_module_registry


def test_yaml_app_settings(config_yaml):
    AppSettings(**config_yaml["app_settings"])


def test_yaml_module_config(config_yaml):
    for module in config_yaml["modules"]["windows"]:
        ModuleConfig(**module)
    for module in config_yaml["modules"]["tabs"]:
        ModuleConfig(**module)


def test_yaml_hb_method_is_registered():
    hb_module_yaml = yaml.safe_load(
        """
        type: HBMethod
        hb_data_handler:
          configured_hb_form: RA-0187
          hb_variable_to_feltsti:
            turnover: /turnover
        hb_variable_selector: turnover
        configured_hb_time_unit:
          name: period
          frequency: YEAR
        """
    )

    hb_module_config = ModuleConfig(**hb_module_yaml)
    registered_module = get_from_module_registry(hb_module_config.type)

    assert registered_module.type is HBMethod
    assert set(hb_module_config.extra_kwargs) <= set(registered_module.kwargs)


def test_yaml_variableselector_config(config_yaml):
    VariableSelectorConfig(**config_yaml["app_settings"]["variableselector"])


def test_yaml_app_modules(config_yaml):
    AppModules(**config_yaml["modules"])


def test_yaml_app_config(config_yaml):
    AppConfig(**config_yaml)


def test_build_app_from_config(config_yaml):
    build_app_from_config(AppConfig(**config_yaml))
