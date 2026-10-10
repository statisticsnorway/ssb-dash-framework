import importlib
from importlib.util import find_spec

import pytest


def test_package_import() -> None:
    spec = find_spec("ssb_dash_framework")
    assert spec is not None, "ssb_dash_framework module not found"

    try:
        importlib.import_module("ssb_dash_framework")
    except ImportError as e:
        pytest.fail(f"Failed to import ssb_dash_framework: {e}")
