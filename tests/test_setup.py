import dash_bootstrap_components as dbc
from ssb_dash_framework.setup.main_layout import main_layout


def test_main_layout():
    layout = main_layout([], [], [])
    assert isinstance(
        layout, dbc.Container
    ), f"main_layout not returning dbc.Container, returns: {type(layout)}"
