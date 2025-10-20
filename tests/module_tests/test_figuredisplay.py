from ssb_dash_framework import FigureDisplay
from ssb_dash_framework import FigureDisplayTab
from ssb_dash_framework import FigureDisplayWindow


def test_import():
    assert FigureDisplay is not None
    assert FigureDisplayTab is not None
    assert FigureDisplayWindow is not None


def test_base_class():
    FigureDisplay(label="Test", figure_func=lambda x: x, inputs=[])


def test_tab():
    FigureDisplayTab(label="Test", figure_func=lambda x: x, inputs=[])


def test_window():
    FigureDisplayWindow(label="Test", figure_func=lambda x: x, inputs=[])


def test_figure_func_callable():
    def figure_func_test():
        return "Success"

    figure = FigureDisplayWindow(label="Test", figure_func=figure_func_test, inputs=[])
    assert figure.figure_func() == "Success"
