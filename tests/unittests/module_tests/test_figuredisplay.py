from ssb_dash_framework import FigureDisplay


def test_import() -> None:
    assert FigureDisplay is not None


def test_base_class() -> None:
    FigureDisplay(label="Test", figure_func=lambda x: x, inputs=[])


def test_tab() -> None:
    module = FigureDisplay(
        label="Test", figure_func=lambda x: x, inputs=[], as_type="Tab"
    )
    assert module.implemented_as == "Tab"


def test_window() -> None:
    module = FigureDisplay(
        label="Test", figure_func=lambda x: x, inputs=[], as_type="Window"
    )
    assert module.implemented_as == "Window"


def test_figure_func_callable() -> None:
    def figure_func_test() -> str:
        return "Success"

    figure = FigureDisplay(label="Test", figure_func=figure_func_test, inputs=[])
    assert figure.figure_func() == "Success"
