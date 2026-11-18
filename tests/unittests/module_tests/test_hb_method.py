from dash import html

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


def test_hb_method_initializes_modulebase_with_injected_handler() -> None:
    hb_data_handler = StubHBDataHandler()

    hb_method = HBMethod(hb_data_handler=hb_data_handler)

    assert hb_method.label == "HB metoden"
    assert hb_method.icon.icon == "keyline-icons:pencil-ruler-sharp-duotone"
    assert hb_method.hb_data_handler is hb_data_handler
    assert isinstance(hb_method.module_layout, html.Div)
    assert hb_method.module_id.startswith("HBMethod-")
