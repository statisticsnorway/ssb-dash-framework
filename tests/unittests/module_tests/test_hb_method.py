import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.modules.hb.data_handler import HBDataResult
from ssb_dash_framework.modules.hb_method import HBMethod


class StubHBDataHandler(HBDataHandlerMeta):
    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        raise AssertionError("The module shell must not call its handler.")


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


def test_hb_method_initializes_modulebase_with_injected_handler() -> None:
    hb_data_handler = StubHBDataHandler()

    hb_method = HBMethod(hb_data_handler=hb_data_handler)

    assert hb_method.label == "HB metoden"
    assert hb_method.icon.icon == "keyline-icons:pencil-ruler-sharp-duotone"
    assert hb_method.hb_data_handler is hb_data_handler
    assert isinstance(hb_method.module_layout, html.Div)
    assert hb_method.module_id.startswith("HBMethod-")


def test_hb_method_instances_have_unique_module_scoped_component_ids() -> None:
    first_hb_method = HBMethod(hb_data_handler=StubHBDataHandler())
    second_hb_method = HBMethod(hb_data_handler=StubHBDataHandler())

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


def test_hb_method_can_be_placed_as_tab_or_window() -> None:
    tab_hb_method = HBMethod(hb_data_handler=StubHBDataHandler(), as_type="Tab")
    window_hb_method = HBMethod(hb_data_handler=StubHBDataHandler(), as_type="Window")

    assert tab_hb_method.implemented_as == "Tab"
    assert isinstance(tab_hb_method._internal_layout(), dbc.Tab)

    assert window_hb_method.implemented_as == "Window"
    window_layout = window_hb_method._internal_layout()
    assert isinstance(window_layout, html.Div)
    assert any(isinstance(child, dbc.Modal) for child in window_layout.children)
