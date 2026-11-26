import logging
from collections.abc import Callable
from io import StringIO
from unittest.mock import Mock

import dash_bootstrap_components as dbc
import pandas as pd
import pytest
from dash import Input
from dash import Output
from dash import html
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.modules.hb.data_handler import HBDataResult
from ssb_dash_framework.modules.hb.data_handler import HBDataWarning
from ssb_dash_framework.modules.hb.hb_method import HBMethod
from ssb_dash_framework.modules.hb.hb_method import (
    _extract_hb_unit_id_from_plotly_click_data,
)
from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType
from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.setup.variableselector import VariableSelectorConfig
from ssb_dash_framework.setup.variableselector import VariableSelectorOption
from ssb_dash_framework.utils.alert_handler import AlertHandler

from .fake_hb_data_handler import FakeHBDataHandler


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
    monkeypatch.setattr(VariableSelector, "_ident", None)
    configured_hb_time_unit = TimeUnit(
        name="periode",
        frequency=TimeUnitType.YEAR,
    )
    VariableSelectorConfig(ident="ident", time_units=configured_hb_time_unit)
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


def _capture_hb_method_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[tuple[object, ...], dict[str, object], Callable[..., object]]]:
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
        "ssb_dash_framework.modules.hb.hb_method.callback",
        capture_callback,
    )
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.hb_method.clientside_callback",
        Mock(),
    )
    return captured_callbacks


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
            f"{hb_method.module_id}-hb_info_icon",
            f"{hb_method.module_id}-hb_result_loading",
            f"{hb_method.module_id}-hb_error_message",
            f"{hb_method.module_id}-hb_empty_state",
            f"{hb_method.module_id}-hb_result_store",
            f"{hb_method.module_id}-hb_run_gate_state",
            f"{hb_method.module_id}-hb_run_request",
            f"{hb_method.module_id}-hb_result_graph",
            f"{hb_method.module_id}-hb_candidate_state_summary",
        }.issubset(component_ids)
        assert all(component_id.startswith(hb_method.module_id) for component_id in component_ids)
        hb_controls = next(
            child
            for child in hb_method.module_layout.children
            if getattr(child, "id", None) == f"{hb_method.module_id}-hb_controls"
        )
        hb_tooltip = next(
            child
            for child in hb_controls.children
            if isinstance(child, dbc.Tooltip)
        )
        assert hb_tooltip.target == f"{hb_method.module_id}-hb_info_icon"


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
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    hb_data_handler = StubHBDataHandler()
    warning_alert = Mock()
    monkeypatch.setattr(AlertHandler, "warning", warning_alert)
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
            "strata": ["A"],
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
        "ssb_dash_framework.modules.hb.hb_method.run_hb_vaskify",
        fake_run_hb_vaskify,
    )
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.hb_method.normalize_hb_result",
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
        f"{hb_method.module_id}-hb_run_request"
    )
    assert callback_options["prevent_initial_call"] is True

    callback_result = callback_function(
        {
            "hb_run_request_id": 1,
            "selected_hb_variable": "omsetning",
            "selector_period_value": "2024",
        }
    )

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
        "hb_run_request_id": 1,
    }
    display_callback = captured_callbacks[1][2]
    with pytest.raises(PreventUpdate):
        display_callback(callback_result, {"hb_run_request_id": 2})
    warning_alert.assert_not_called()
    display_callback(callback_result, {"hb_run_request_id": 1})
    warning_alert.assert_called_once_with(
        "HB-data inneholder 1 advarsel/advarsler.",
        ephemeral=True,
    )
    assert not hasattr(hb_method, "selected_hb_variable")
    assert not hasattr(hb_method, "selector_period_value")


def test_hb_result_callback_displays_diagnostics_and_candidate_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_hb_selectors(monkeypatch)
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    HBMethod(
        hb_data_handler=StubHBDataHandler(),
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=TimeUnit(
            name="periode",
            frequency=TimeUnitType.YEAR,
        ),
        configured_hb_strata_variable="næring",
    )
    normalized_hb_result_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-flagged", "unit-unflagged", "unit-not-comparable"],
            "value_2023": [10.0, 20.0, 30.0],
            "value_2024": [15.0, 25.0, 35.0],
            "strata": ["A", "A", "B"],
            "ratio": [1.5, 1.0, None],
            "median_ratio": [1.1, 1.1, None],
            "lower_limit": [0.8, 0.8, None],
            "upper_limit": [1.2, 1.2, None],
            "flag_hb": [1, 0, None],
        }
    )
    hb_result_store_data = {
        "hb_run_request_id": 1,
        "hb_comparison_periods": ["2023", "2024"],
        "hb_result_dataframe_json": normalized_hb_result_dataframe.to_json(
            orient="split",
            date_format="iso",
        ),
        "hb_warnings": [],
    }

    display_callback = captured_callbacks[1][2]
    (
        hb_result_figure,
        hb_result_graph_style,
        hb_empty_state_style,
        candidate_state_summary,
        candidate_state_summary_style,
    ) = display_callback(
        hb_result_store_data,
        {"hb_run_request_id": 1},
    )

    hb_trace_names = {trace.name for trace in hb_result_figure.data}
    assert {
        "Flagget",
        "Ikke flagget",
        "Median ratio — A",
        "Øvre grense — A",
        "Nedre grense — A",
    }.issubset(hb_trace_names)
    assert hb_result_figure.layout.xaxis.title.text == "Verdi i 2024"
    assert hb_result_figure.layout.yaxis.title.text == "Forholdstall (ratio)"
    assert all(
        trace.customdata is not None
        and all(isinstance(point_customdata[0], str) for point_customdata in trace.customdata)
        for trace in hb_result_figure.data
    )
    candidate_traces_by_name = {
        trace.name: trace for trace in hb_result_figure.data if trace.name in {"Flagget", "Ikke flagget"}
    }
    assert candidate_traces_by_name["Flagget"].customdata[0][0] == "unit-flagged"
    assert candidate_traces_by_name["Ikke flagget"].customdata[0][0] == "unit-unflagged"
    assert candidate_traces_by_name["Flagget"].customdata[0][1] == 10.0
    assert candidate_traces_by_name["Flagget"].customdata[0][2] == 1.1
    assert "Verdi i 2024: %{x}" in candidate_traces_by_name["Flagget"].hovertemplate
    assert (
        "Verdi i 2023: %{customdata[1]}"
        in candidate_traces_by_name["Flagget"].hovertemplate
    )
    median_trace = next(
        trace for trace in hb_result_figure.data if trace.name == "Median ratio — A"
    )
    assert median_trace.customdata[0][1] == 10.0
    assert "Verdi i 2023: %{customdata[1]}" in median_trace.hovertemplate
    assert hb_result_graph_style == {"display": "block"}
    assert hb_empty_state_style == {"display": "none"}
    assert candidate_state_summary == (
        "Flagget: 1 · Ikke flagget: 1 · Ikke sammenlignbar: 1"
    )
    assert candidate_state_summary_style == {"display": "block"}

    empty_display_result = display_callback(None, {"hb_run_request_id": 1})
    assert empty_display_result == (
        {},
        {"display": "none"},
        {},
        "",
        {"display": "none"},
    )
    with pytest.raises(PreventUpdate):
        display_callback(hb_result_store_data, {"hb_run_request_id": 2})


def test_hb_graph_click_updates_configured_ident_for_multiple_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    hb_data_handler = StubHBDataHandler()
    vaskify_call = Mock(side_effect=AssertionError("Vaskify must not run on selection."))
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.hb_method.run_hb_vaskify",
        vaskify_call,
    )
    HBMethod(
        hb_data_handler=hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )

    click_callback = captured_callbacks[2][2]
    hb_result_store_data = {
        "hb_run_request_id": 1,
        "hb_result_dataframe_json": pd.DataFrame(
            {"unit_id": ["unit-flagged", "unit-unflagged"]}
        ).to_json(orient="split"),
    }
    latest_hb_run_request = {"hb_run_request_id": 1}

    selected_unit_ids = [
        click_callback(
            {"points": [{"customdata": [candidate_unit_id, 1.2]}]},
            hb_result_store_data,
            latest_hb_run_request,
        )
        for candidate_unit_id in ("unit-flagged", "unit-unflagged")
    ]

    assert selected_unit_ids == ["unit-flagged", "unit-unflagged"]
    assert captured_callbacks[2][0][0] == VariableSelector.get_ident(Output)
    assert hb_data_handler.calls == []
    vaskify_call.assert_not_called()


def test_hb_graph_click_without_a_point_prevents_selector_update_and_hb_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    hb_data_handler = StubHBDataHandler()
    vaskify_call = Mock(side_effect=AssertionError("Vaskify must not run on selection."))
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.hb_method.run_hb_vaskify",
        vaskify_call,
    )
    HBMethod(
        hb_data_handler=hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )
    click_callback = captured_callbacks[2][2]
    hb_result_store_data = {
        "hb_run_request_id": 1,
        "hb_result_dataframe_json": pd.DataFrame(
            {"unit_id": ["unit-flagged"]}
        ).to_json(orient="split"),
    }

    with pytest.raises(PreventUpdate):
        click_callback(
            None,
            hb_result_store_data,
            {"hb_run_request_id": 1},
        )

    assert hb_result_store_data == {
        "hb_run_request_id": 1,
        "hb_result_dataframe_json": pd.DataFrame(
            {"unit_id": ["unit-flagged"]}
        ).to_json(orient="split"),
    }
    assert hb_data_handler.calls == []
    vaskify_call.assert_not_called()


@pytest.mark.parametrize(
    ("click_data", "expected_hb_unit_id"),
    [
        ({"points": [{"customdata": ["unit-flagged", 1.1]}]}, "unit-flagged"),
        ({"points": [{"customdata": "unit-unflagged"}]}, "unit-unflagged"),
        (
            {"points": [{"hovertext": "unit-hover", "pointNumber": 7, "x": 4}]},
            None,
        ),
        ({"points": []}, None),
        ({"points": [{"customdata": []}]}, None),
        (None, None),
    ],
)
def test_hb_unit_id_is_extracted_only_from_plotly_customdata(
    click_data: dict[str, object] | None,
    expected_hb_unit_id: str | None,
) -> None:
    assert _extract_hb_unit_id_from_plotly_click_data(click_data) == expected_hb_unit_id


@pytest.mark.parametrize("failure_point", ["handler", "vaskify", "empty_normalized"])
def test_hb_run_failures_alert_and_log_without_row_data(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure_point: str,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    hb_data_handler = StubHBDataHandler()
    hb_data_handler.hb_warnings = ()
    error_alert = Mock()
    monkeypatch.setattr(AlertHandler, "error", error_alert)
    sensitive_error_detail = "sensitive-unit-742 value-12345"

    if failure_point == "handler":
        monkeypatch.setattr(
            hb_data_handler,
            "get_hb_dataframe",
            Mock(side_effect=RuntimeError(sensitive_error_detail)),
        )
    elif failure_point == "vaskify":
        monkeypatch.setattr(
            "ssb_dash_framework.modules.hb.hb_method.run_hb_vaskify",
            Mock(side_effect=RuntimeError(sensitive_error_detail)),
        )
    else:
        empty_vaskify_result_dataframe = pd.DataFrame(
            columns=[
                "unit_id",
                "value_2023",
                "value_2024",
                "lower_limit",
                "upper_limit",
                "ratio",
                "median_ratio",
                "flag_hb",
            ]
        )
        monkeypatch.setattr(
            "ssb_dash_framework.modules.hb.hb_method.run_hb_vaskify",
            Mock(return_value=empty_vaskify_result_dataframe),
        )

    HBMethod(
        hb_data_handler=hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )
    run_callback = captured_callbacks[0][2]

    with caplog.at_level(
        logging.ERROR,
        logger="ssb_dash_framework.modules.hb.hb_method",
    ):
        failed_run_result = run_callback(
            {
                "hb_run_request_id": 1,
                "selected_hb_variable": "omsetning",
                "selector_period_value": "2024",
            }
        )

    assert failed_run_result == {
        "hb_run_request_id": 1,
        "hb_run_error": True,
    }
    display_callback = captured_callbacks[1][2]
    with pytest.raises(PreventUpdate):
        display_callback(failed_run_result, {"hb_run_request_id": 2})
    error_alert.assert_not_called()
    display_callback(failed_run_result, {"hb_run_request_id": 1})
    error_alert.assert_called_once_with(
        "HB-kjøringen feilet. Kontroller valgt variabel og periode.",
        ephemeral=True,
    )
    assert "module_id=HBMethod-" in caplog.text
    assert "selected_hb_variable='omsetning'" in caplog.text
    assert "selector_period_value='2024'" in caplog.text
    assert sensitive_error_detail not in caplog.text


def test_hb_module_integration_with_fake_handler_avoids_production_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured_hb_time_unit = _configure_hb_selectors(monkeypatch)
    captured_callbacks = _capture_hb_method_callbacks(monkeypatch)
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": ["2023", "2024", "2023", "2024"],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )
    fake_hb_data_handler = FakeHBDataHandler(hb_input_dataframe)

    def production_backend_must_not_be_called(*args: object, **kwargs: object):
        raise AssertionError("The fake-handler integration test accessed the backend.")

    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.altinn_candidate_retrieval.get_connection",
        production_backend_must_not_be_called,
    )
    monkeypatch.setattr(
        "ssb_dash_framework.modules.hb.altinn_candidate_retrieval.active_no_duplicates_refnr_list",
        production_backend_must_not_be_called,
    )
    HBMethod(
        hb_data_handler=fake_hb_data_handler,
        hb_variable_selector="statistikkvariabel",
        configured_hb_time_unit=configured_hb_time_unit,
    )
    run_callback = captured_callbacks[0][2]

    hb_result_store_data = run_callback(
        {
            "hb_run_request_id": 1,
            "selected_hb_variable": "omsetning",
            "selector_period_value": "2024",
        }
    )
    normalized_hb_result_dataframe = pd.read_json(
        StringIO(hb_result_store_data["hb_result_dataframe_json"]),
        orient="split",
    )

    assert fake_hb_data_handler.requests[0].selected_hb_variable == "omsetning"
    assert fake_hb_data_handler.requests[0].hb_comparison_periods == (
        "2023",
        "2024",
    )
    assert normalized_hb_result_dataframe["unit_id"].tolist() == [
        "unit-1",
        "unit-2",
    ]
    assert {
        "ratio",
        "median_ratio",
        "lower_limit",
        "upper_limit",
        "flag_hb",
    }.issubset(normalized_hb_result_dataframe.columns)
