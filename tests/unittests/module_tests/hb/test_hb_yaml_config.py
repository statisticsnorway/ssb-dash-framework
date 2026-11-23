import yaml

from ssb_dash_framework import HBMethod
from ssb_dash_framework import ModuleConfig
from ssb_dash_framework import get_from_module_registry


def test_yaml_hb_method_is_registered() -> None:
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
