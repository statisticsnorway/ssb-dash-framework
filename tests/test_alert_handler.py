import json

from dash import html

from ssb_dash_framework.utils.alert_handler import AlertHandler
from ssb_dash_framework.utils.alert_handler import _ephemeral_toast_state
from ssb_dash_framework.utils.alert_handler import create_alert


def test_create_alert() -> None:
    alert = create_alert("Test message", "info", True)
    assert isinstance(alert, dict)
    assert len(alert.keys()) == 8


def test_alerthandler() -> None:
    handler = AlertHandler()
    handler_layout = handler.layout()
    assert isinstance(handler_layout, html.Div)


EMPTY_SIGNATURE = {"bottom-left": [], "center": [], "top-right": []}


def test_ephemeral_toast_state_signature_stable_between_ticks() -> None:
    """The signature must not change between interval ticks while a toast is visible.

    A changed signature means the display callback rewrites a container's
    children, which since Dash 4.2.0 remounts the DOM nodes and replays the
    entry animation (the "one alert shows up 6 times" bug).
    """
    alert = create_alert("Test message", "info", ephemeral=True)
    t0 = alert["created_at"]

    visible_1, signature_1 = _ephemeral_toast_state([alert], t0 + 1)
    _visible_2, signature_2 = _ephemeral_toast_state([alert], t0 + 2)
    assert [a for a, _ in visible_1] == [alert]
    assert visible_1[0][1] is False  # not dying yet
    assert signature_1 == signature_2

    # The signature is stored in a dcc.Store, so it must survive a JSON round
    # trip unchanged for the equality check to hold on the next tick.
    assert json.loads(json.dumps(signature_1)) == signature_1


def test_ephemeral_toast_state_signature_is_per_position() -> None:
    """Each position has its own signature so unchanged containers can get no_update."""
    bottom = create_alert("Bottom message", "info", ephemeral=True)
    center = create_alert(
        "Center message", "warning", ephemeral=True, position="center"
    )
    t0 = max(bottom["created_at"], center["created_at"])

    _, signature = _ephemeral_toast_state([bottom, center], t0 + 1)
    assert len(signature["bottom-left"]) == 1
    assert len(signature["center"]) == 1
    assert signature["top-right"] == []


def test_ephemeral_toast_state_dying_and_expiry_change_signature() -> None:
    alert = create_alert("Test message", "info", ephemeral=True)
    t0 = alert["created_at"]

    _, signature_fresh = _ephemeral_toast_state([alert], t0 + 1)
    visible_dying, signature_dying = _ephemeral_toast_state([alert], t0 + 4.5)
    assert visible_dying[0][1] is True  # exit animation render
    assert signature_dying != signature_fresh

    visible_expired, signature_expired = _ephemeral_toast_state([alert], t0 + 5.5)
    assert visible_expired == []
    assert signature_expired == EMPTY_SIGNATURE


def test_ephemeral_toast_state_ignores_non_ephemeral_alerts() -> None:
    alert = create_alert("Test message", "info", ephemeral=False)
    result = _ephemeral_toast_state([alert], alert["created_at"] + 1)
    assert result == ([], EMPTY_SIGNATURE)
    assert _ephemeral_toast_state(None, 0.0) == ([], EMPTY_SIGNATURE)
