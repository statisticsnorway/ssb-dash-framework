from typing import Any

import pytest
from dash._callback import GLOBAL_CALLBACK_MAP

from ssb_dash_framework import ControlView
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


def test_import() -> None:
    assert ControlView is not None


class _StopCallback(Exception):
    """Raised by the dummy control class to stop the callback before it hits the database."""


def test_control_class_receives_time_units_as_list() -> None:
    """ControlFrameworkBase unpacks time_units, so a bare string becomes one column per character."""
    VariableSelectorConfig(
        refnr="refnr",
        ident="ident",
        time_units=TimeUnit(name="aar", frequency=TimeUnitType.YEAR),
        grouping_variables=["altinnskjema"],
    )
    received: dict[str, Any] = {}

    class DummyControls:
        def __init__(self, time_units: list[str], applies_to_subset: dict) -> None:
            received["time_units"] = time_units
            received["applies_to_subset"] = applies_to_subset
            raise _StopCallback

    module = ControlView(control_dict={"RA-0001": DummyControls})
    output_key = (
        f"..{module.module_number}-kontroller.rowData"
        f"...{module.module_number}-kontroller.columnDefs.."
    )
    get_kontroller_overview = GLOBAL_CALLBACK_MAP[output_key]["callback"].__wrapped__

    with pytest.raises(_StopCallback):
        get_kontroller_overview("RA-0001", None, 1, "2024")

    assert received["time_units"] == ["aar"]
    assert received["applies_to_subset"] == {"skjema": ["RA-0001"], "aar": "2024"}
