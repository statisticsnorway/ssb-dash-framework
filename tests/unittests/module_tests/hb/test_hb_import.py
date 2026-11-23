import importlib
import warnings


def test_hb_method_is_exported_from_package() -> None:
    package = importlib.import_module("ssb_dash_framework")
    modules = importlib.import_module("ssb_dash_framework.modules")
    hb_module = importlib.import_module("ssb_dash_framework.modules.hb")

    assert package.HBMethod is modules.HBMethod is hb_module.HBMethod


def test_legacy_hb_module_warns_and_points_to_supported_api() -> None:
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always", FutureWarning)
        legacy_module = importlib.import_module(
            "ssb_dash_framework.experimental.modules.hb_method"
        )
        importlib.reload(legacy_module)

    assert any(
        issubclass(captured_warning.category, FutureWarning)
        and "ssb_dash_framework import HBMethod" in str(captured_warning.message)
        for captured_warning in captured_warnings
    )
