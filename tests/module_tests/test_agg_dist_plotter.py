from ssb_dash_framework import AggDistPlotter
from ssb_dash_framework import AggDistPlotterTab
from ssb_dash_framework import AggDistPlotterWindow
from ssb_dash_framework import set_variables


def test_import() -> None:
    assert AggDistPlotter is not None
    assert AggDistPlotterTab is not None
    assert AggDistPlotterWindow is not None


def test_instantiation() -> None:
    set_variables(
        [
            "aar",
            "maaned",  # Required for selected time units
            "ident",
            "valgt_tabell",
            "altinnskjema",  # Required by the module itself
        ]
    )
    AggDistPlotterTab(time_units=["aar", "maaned"])
    AggDistPlotterWindow(time_units=["aar", "maaned"])
