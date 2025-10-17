from ssb_dash_framework import AltinnDataCapture
from ssb_dash_framework import AltinnDataCaptureTab
from ssb_dash_framework import AltinnDataCaptureWindow
from ssb_dash_framework import set_variables

from ..conftest import DummyDatabase


def test_import() -> None:
    assert AltinnDataCapture is not None
    assert AltinnDataCaptureTab is not None
    assert AltinnDataCaptureWindow is not None


def test_base_class_instantiation() -> None:
    from dash import html

    set_variables(["year", "month"])

    # AltinnDataCapture is abstract, so we need to subclass it for instantiation
    class DummyAltinnDataCapture(AltinnDataCapture):
        def layout(self) -> html.Div:
            return self.module_layout

    DummyAltinnDataCapture(
        time_units=["year", "month"],
        label="test",
        database_type="altinn_default",
        database=DummyDatabase(),
    )


def test_tab_instantiation() -> None:
    set_variables(["year", "month"])
    AltinnDataCaptureTab(
        time_units=["year", "month"],
        label="test",
        database_type="altinn_default",
        database=DummyDatabase(),
    )


def test_window_instantiation() -> None:
    set_variables(["year", "month"])
    AltinnDataCaptureWindow(
        time_units=["year", "month"],
        label="test",
        database_type="altinn_default",
        database=DummyDatabase(),
    )


# TODO reimplement test.
# def test_invalid_time_units_type() -> None:
#     set_variables(["notalist"])
#     with pytest.raises(TypeError):
#         AltinnDataCaptureTab(
#             time_units="notalist",  # type: ignore[arg-type]
#             label="test",
#             database_type="altinn_default",
#             database=DummyDatabase(),
#         )
