import os

from dash import Dash
from ssb_sirius_dash.setup.app_setup import app_setup


def test_app_setup():
    port = 8070
    service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
    domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
    app = app_setup(port, service_prefix, domain, "superhero")
    assert isinstance(app, Dash)
