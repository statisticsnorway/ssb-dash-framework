import importlib


def test_hb_method_is_exported_from_package() -> None:
    package = importlib.import_module("ssb_dash_framework")
    modules = importlib.import_module("ssb_dash_framework.modules")
    hb_module = importlib.import_module("ssb_dash_framework.modules.hb")

    assert package.HBMethod is modules.HBMethod is hb_module.HBMethod
