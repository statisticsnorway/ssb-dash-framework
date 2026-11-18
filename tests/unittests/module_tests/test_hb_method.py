from collections.abc import Callable

import dash_bootstrap_components as dbc
import pandas as pd
import pytest
from dash import Input
from dash import Output
from dash import State
from dash import html
from dash.development.base_component import Component

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.modules.hb.data_handler import HBDataResult
from ssb_dash_framework.modules.hb.data_handler import HBDataWarning
from ssb_dash_framework.modules.hb_method import HBMethod
from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType
from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.setup.variableselector import VariableSelectorConfig
from ssb_dash_framework.setup.variableselector import VariableSelectorOption


class StubHBDataHandler(HBDataHandlerMeta):
    def __init__(self) -> None:
        """Create a handler stub that records calls and returns test data."""
        self.calls: list[dict[str, object]] = []
        self.hb_dataframe = pd.DataFrame(
            {
                "unit_id": ["unit-1", "unit-1"],
                "period": ["2023", "2024"],
                "value": [10.0, 12.0],
            }
        )
        self.hb_warnings = (HBDataWarning("Missing value.", "unit-1", "2023"),)

    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        self.calls.append(
            {
                "selected_hb_variable": selected_hb_variable,
                "hb_comparison_periods": hb_comparison_periods,
                "configured_hb_strata_variable": configured_hb_strata_variable,
            }
        )
        return HBDataResult(self.hb_dataframe, self.hb_warnings)


def _configure_hb_selectors(
    monkeypatch: pytest.MonkeyPatch,
    *,
    add_hb_variable_selector: bool = True,
) -> TimeUnit:
    monkeypatch.setattr(VariableSelector, "_time_unit", None)
    configured_hb_time_unit = TimeUnit(
        name="periode",
        frequency=TimeUnitType.YEAR,
    )
    VariableSelectorConfig(time_units=configured_hb_time_unit)
    if add_hb_variable_selector:
        VariableSelectorOption("statistikkvariabel")
    return configured_hb_time_unit


def _component_ids(component: Component) -> set[str]:
    component_id = getattr(component, "id", None)
    component_ids = {component_id} if isinstance(component_id, str) else set()
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            if isinstance(child, Component):
                component_ids.update(_component_ids(child))
    elif isinstance(children, Component):
        component_ids.update(_component_ids(children))
    return component_ids


def test_hb_method_initializes_modulebase_with_injected_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    hb_data_handler = StubHBDataHandler()

    hb_method = HBMethod(
        hb_data_handler=hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )

    assert hb_method.label == "HB metoden"
    assert hb_method.icon.icon == "keyline-icons:pencil-ruler-sharp-duotone"
    assert hb_method.hb_data_handler is hb_data_handler
    assert isinstance(hb_method.module_layout, html.Div)
    assert hb_method.module_id.startswith("HBMethod-")


def test_hb_method_instances_have_unique_module_scoped_component_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    first_hb_method = HBMethod(
        hb_data_handler=StubHBDataHandler(),
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )
    second_hb_method = HBMethod(
        hb_data_handler=StubHBDataHandler(),
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )

    first_component_ids = _component_ids(first_hb_method.module_layout)
    second_component_ids = _component_ids(second_hb_method.module_layout)

    assert first_hb_method.module_id != second_hb_method.module_id
    assert first_component_ids.isdisjoint(second_component_ids)
    for hb_method, component_ids in (
        (first_hb_method, first_component_ids),
        (second_hb_method, second_component_ids),
    ):
        assert {
            f"{hb_method.module_id}-hb_controls",
            f"{hb_method.module_id}-hb_run_button",
            f"{hb_method.module_id}-hb_result_loading",
            f"{hb_method.module_id}-hb_error_message",
            f"{hb_method.module_id}-hb_empty_state",
            f"{hb_method.module_id}-hb_result_store",
            f"{hb_method.module_id}-hb_result_graph",
        }.issubset(component_ids)
        assert all(component_id.startswith(hb_method.module_id) for component_id in component_ids)


def test_hb_method_can_be_placed_as_tab_or_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    tab_hb_method = HBMethod(
        hb_data_handler=StubHBDataHandler(),
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
        as_type="Tab",
    )
    window_hb_method = HBMethod(
        hb_data_handler=StubHBDataHandler(),
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
        as_type="Window",
    )

    assert tab_hb_method.implemented_as == "Tab"
    assert isinstance(tab_hb_method._internal_layout(), dbc.Tab)

    assert window_hb_method.implemented_as == "Window"
    window_layout = window_hb_method._internal_layout()
    assert isinstance(window_layout, html.Div)
    assert any(isinstance(child, dbc.Modal) for child in window_layout.children)


def test_hb_method_requires_configured_time_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(VariableSelector, "_time_unit", None)
    VariableSelectorOption("statistikkvariabel")
    configured_hb_time_unit = TimeUnit(
        name="periode",
        frequency=TimeUnitType.YEAR,
    )

    with pytest.raises(RuntimeError, match="Time unit is not set"):
        HBMethod(
            hb_data_handler=StubHBDataHandler(),
            hb_variable_selector="statistikkvariabel",
            configured_hb_time_unit=configured_hb_time_unit,
        )


def test_hb_method_requires_configured_variable_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(
        monkeypatch,
        add_hb_variable_selector=False,
    )
    with pytest.raises(ValueError, match="not in list of options"):
        HBMethod(
            hb_data_handler=StubHBDataHandler(),
            hb_variable_selector="statistikkvariabel",
            configured_hb_time_unit=configured_hb_time_unit,
        )


def test_hb_method_rejects_time_unit_with_different_selector_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_hb_selectors(monkeypatch)
    mismatched_hb_time_unit = TimeUnit(
        name="another_period",
        frequency=TimeUnitType.QUARTER,
    )
    VariableSelectorOption("another_period")

    with pytest.raises(ValueError, match="same selector name"):
        HBMethod(
            hb_data_handler=StubHBDataHandler(),
            hb_variable_selector="statistikkvariabel",
            configured_hb_time_unit=mismatched_hb_time_unit,
        )


def test_hb_run_callback_calls_handler_vaskify_and_normalizer_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    captured_callbacks: list[
        tuple[tuple[object, ...], dict[str, object], Callable[..., object]]
    ] = []

    def capture_callback(*dependencies: object, **kwargs: object):
        def register(
            callback_function: Callable[..., object],
        ) -> Callable[..., object]:
            captured_callbacks.append((dependencies, kwargs, callback_function))
            return callback_function

        return register

    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb_method.callback",
        capture_callback,
    )
    hb_data_handler = StubHBDataHandler()
    execution_order: list[str] = []
    original_get_hb_dataframe = hb_data_handler.get_hb_dataframe

    def tracked_get_hb_dataframe(
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        execution_order.append("handler")
        return original_get_hb_dataframe(
            selected_hb_variable=selected_hb_variable,
            hb_comparison_periods=hb_comparison_periods,
            configured_hb_strata_variable=configured_hb_strata_variable,
        )

    monkeypatch.setattr(
        hb_data_handler,
        "get_hb_dataframe",
        tracked_get_hb_dataframe,
    )
    hb_vaskify_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1"],
            "ratio": [1.2],
            "median_ratio": [1.0],
            "lower_limit": [0.8],
            "upper_limit": [1.2],
            "flag_hb": [0],
        }
    )
    normalized_hb_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1"],
            "value_2023": [10.0],
            "value_2024": [12.0],
            "ratio": [1.2],
            "median_ratio": [1.0],
            "lower_limit": [0.8],
            "upper_limit": [1.2],
            "flag_hb": [0],
        }
    )

    def fake_run_hb_vaskify(
        hb_input_dataframe: pd.DataFrame,
        *,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> pd.DataFrame:
        execution_order.append("vaskify")
        assert hb_input_dataframe is hb_data_handler.hb_dataframe
        assert hb_comparison_periods == ("2023", "2024")
        assert configured_hb_strata_variable == "fylke"
        return hb_vaskify_result_dataframe

    def fake_normalize_hb_result(
        hb_input_dataframe: pd.DataFrame,
        input_hb_vaskify_result_dataframe: pd.DataFrame,
        *,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> pd.DataFrame:
        execution_order.append("normalize")
        assert hb_input_dataframe is hb_data_handler.hb_dataframe
        assert input_hb_vaskify_result_dataframe is hb_vaskify_result_dataframe
        assert hb_comparison_periods == ("2023", "2024")
        assert configured_hb_strata_variable == "fylke"
        return normalized_hb_result_dataframe

    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb_method.run_hb_vaskify",
        fake_run_hb_vaskify,
    )
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb_method.normalize_hb_result",
        fake_normalize_hb_result,
    )
    hb_method = HBMethod(
        hb_data_handler=hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
        configured_hb_strata_variable="fylke",
    )

    callback_dependencies, callback_options, callback_function = captured_callbacks[0]
    assert isinstance(callback_dependencies[0], Output)
    assert callback_dependencies[0].component_id == (
        f"{hb_method.module_id}-hb_result_store"
    )
    assert isinstance(callback_dependencies[1], Input)
    assert callback_dependencies[1].component_id == (
        f"{hb_method.module_id}-hb_run_button"
    )
    assert isinstance(callback_dependencies[2], State)
    assert callback_dependencies[2].component_id == "var-statistikkvariabel"
    assert isinstance(callback_dependencies[3], State)
    assert callback_dependencies[3].component_id == "var-periode"
    assert callback_options["prevent_initial_call"] is True

    callback_result = callback_function(1, "omsetning", "2024")

    assert execution_order == ["handler", "vaskify", "normalize"]
    assert hb_data_handler.calls == [
        {
            "selected_hb_variable": "omsetning",
            "hb_comparison_periods": ("2023", "2024"),
            "configured_hb_strata_variable": "fylke",
        }
    ]
    assert callback_result == {
        "hb_comparison_periods": ["2023", "2024"],
        "hb_result_dataframe_json": normalized_hb_result_dataframe.to_json(
            orient="split",
            date_format="iso",
        ),
        "hb_warnings": [
            {"message": "Missing value.", "unit_id": "unit-1", "period": "2023"}
        ],
    }
    assert not hasattr(hb_method, "selected_hb_variable")
    assert not hasattr(hb_method, "selector_period_value")
