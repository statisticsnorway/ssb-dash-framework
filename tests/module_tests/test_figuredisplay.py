from ssb_dash_framework import FigureDisplay
from ssb_dash_framework import FigureDisplayTab
from ssb_dash_framework import FigureDisplayWindow


def test_import() -> None:
    assert FigureDisplay is not None
    assert FigureDisplayTab is not None
    assert FigureDisplayWindow is not None


def test_base_class() -> None:
    FigureDisplay(label="Test", figure_func=lambda x: x, inputs=[])


def test_tab() -> None:
    FigureDisplayTab(label="Test", figure_func=lambda x: x, inputs=[])


def test_window() -> None:
    FigureDisplayWindow(label="Test", figure_func=lambda x: x, inputs=[])


def test_figure_func_callable() -> None:
    def figure_func_test() -> str:
        return "Success"

    figure = FigureDisplayWindow(label="Test", figure_func=figure_func_test, inputs=[])
    assert figure.figure_func() == "Success"
