"""uv run pytest tests/test_my_app.py::test_something --headed --slowmo=500"""

import urllib.request
from collections.abc import Callable
from collections.abc import Generator

import pytest
from dash import Dash
from demo.hello_world.hello_module import HelloModule
from demo.hello_world.hello_module import HelloModuleDataHandlerDefault
from demo.hello_world.hello_module import HelloModuleMetaDataHandler
from playwright.sync_api import Page
from playwright.sync_api import expect

from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from tests.live_server import serve_dash_app


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


def test_meta_data_handler():
    assert HelloModuleMetaDataHandler is not None

    class DummyMetaDataHandler(HelloModuleMetaDataHandler):
        def __init__(self):
            super().__init__()

        def get_message(self, refnr: str):
            return "Dummy message"

        def update_message(self, refnr: str, new_value: str):
            return f"New Dummy message {refnr}, {new_value}"

        def on_failure(self):
            raise Exception("Dummy failure")

    dummy_handler = DummyMetaDataHandler()
    assert dummy_handler.get_message("123") == "Dummy message"
    assert (
        dummy_handler.update_message("123", "New Value")
        == "New Dummy message 123, New Value"
    )
    try:
        dummy_handler.on_failure()
    except Exception as e:
        assert str(e) == "Dummy failure"


def test_data_handler_default():
    handler = HelloModuleDataHandlerDefault()
    assert handler is not None
    assert handler.get_message("1") == "Hello world!"
    assert handler.get_message("2") == "Hello universe!"
    assert handler.update_message("1", "Hello test!") == "Hello test!"
    assert handler.get_message("1") == "Hello test!"
    try:
        handler.on_failure()
    except Exception as e:
        assert (
            str(e)
            == "An error happened, check the App-logg window for more information."
        )


def test_hello_module(page: Page, hello_url: str) -> None:
    """Opens the hello app in a browser and checks the module's buttons render.

    Verifies that the layout is built and rendered by Dash in a real browser.
    """
    page.goto(hello_url)
    page.pause()
    expect(page.get_by_text("Get currently stored message")).to_be_attached()
    expect(page.get_by_text("Update stored message")).to_be_attached()
