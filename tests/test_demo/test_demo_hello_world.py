import urllib.request
from collections.abc import Callable
from collections.abc import Generator

import pytest
from dash import Dash
from demo.hello_world.hello_module import HelloModule
from demo.hello_world.hello_module import HelloModuleDataHandlerDefault
from tests.live_server import serve_dash_app

from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout


def build_hello_app() -> Dash:
    VariableSelectorConfig(refnr="Refnr")
    app = app_setup(8070, None, "lumen", enable_logging=False)
    app.layout = main_layout(
        window_list=[],
        tab_list=[
            HelloModule(
                label="Test module", data_handler=HelloModuleDataHandlerDefault()
            )
        ],
    )
    return app


@pytest.fixture(scope="module")
def hello_url() -> Generator[str]:
    with serve_dash_app(build_hello_app()) as url:
        yield url


def assert_layout_served(url: str) -> None:
    with urllib.request.urlopen(f"{url}_dash-layout") as response:
        assert response.status == 200
        assert b"Test module" in response.read()


def test_hello_module_served_per_test(
    dash_server: Callable[[Dash], str],
) -> None:
    """Checks that the `dash_server` factory serves the hello app's layout.

    Verifies the per-test way of running an app, which stops when the test ends.
    """
    assert_layout_served(dash_server(build_hello_app()))


def test_hello_module_served_per_module(hello_url: str) -> None:
    """Checks that the module-scoped `hello_url` fixture serves the layout.

    Verifies the shared way of running an app with `serve_dash_app`, which
    keeps one app running for all tests in the module.
    """
    assert_layout_served(hello_url)
