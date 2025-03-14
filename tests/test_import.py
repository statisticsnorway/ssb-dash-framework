import importlib
from importlib.util import find_spec

import pytest


def test_package_import() -> None:
    spec = find_spec("ssb_sirius_dash")
    assert spec is not None, "ssb_sirius_dash module not found"

    try:
        importlib.import_module("ssb_sirius_dash")
    except ImportError as e:
        pytest.fail(f"Failed to import ssb_sirius_dash: {e}")


def test_top_level_access() -> None:
    import ssb_sirius_dash

    assert hasattr(
        ssb_sirius_dash, "main_layout"
    ), "main_layout is not accessible at the top level"
    assert callable(ssb_sirius_dash.main_layout), "main_layout is not callable"


def test_submodule_existence() -> None:
    modules_to_check = [
        "ssb_sirius_dash.modals.hb_method",
        "ssb_sirius_dash.setup.main_layout",
        "ssb_sirius_dash.tabs.bofregistry",
        "ssb_sirius_dash.control.framework",
    ]

    for module_path in modules_to_check:
        spec = find_spec(module_path)
        assert spec is not None, f"Module {module_path} could not be found!"


@pytest.mark.parametrize(
    "module_path, symbol",
    [
        ("ssb_sirius_dash.modals.hb_method", "HBMethod"),
        ("ssb_sirius_dash.setup.main_layout", "main_layout"),
        ("ssb_sirius_dash.tabs.bofregistry", "BofInformation"),
        ("ssb_sirius_dash.control.framework", "QualityReport"),
    ],
)
def test_specific_imports(module_path: str, symbol: str) -> None:
    try:
        # Dynamically construct the import statement
        exec(f"from {module_path} import {symbol}")
    except ImportError as e:
        pytest.fail(f"Failed to import {symbol} from {module_path}: {e}")
