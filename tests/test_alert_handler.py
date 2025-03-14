from dash import html
from ssb_sirius_dash.utils.alert_handler import AlertHandler
from ssb_sirius_dash.utils.alert_handler import create_alert


def test_create_alert():
    alert = create_alert("Test message", "info", True)
    assert isinstance(alert, dict)
    assert len(alert.keys()) == 5


def test_alerthandler():
    handler = AlertHandler()
    handler_layout = handler.layout()
    assert isinstance(handler_layout, html.Div)
