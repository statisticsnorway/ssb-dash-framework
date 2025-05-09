import os

import dash_bootstrap_components as dbc
from dash import Dash

from ssb_dash_framework import VariableSelectorOption
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout


def test_add_option() -> None:
    VariableSelectorOption("foretak")


def test_main_layout() -> None:
    layout = main_layout([], [], [])
    assert isinstance(
        layout, dbc.Container
    ), f"main_layout not returning dbc.Container, returns: {type(layout)}"


def test_app_setup() -> None:
    port = 8070
    service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
    domain = os.getenv(
        "JUPYTERHUB_HTTP_REFERER", "localhost"
    )  # for testing purposes, set localhost if JUPYTERHUB_HTTP_REFERER is not set
    app = app_setup(port, service_prefix, domain, "superhero")
    assert isinstance(app, Dash)
