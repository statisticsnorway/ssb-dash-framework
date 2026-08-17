import json

from dash import html

from ssb_dash_framework.utils.alert_handler import _MAX_TOASTS_PER_POSITION
from ssb_dash_framework.utils.alert_handler import _TOAST_POSITIONS
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


EMPTY_SLOTS = [None] * _MAX_TOASTS_PER_POSITION
EMPTY_SIGNATURE = {pos: EMPTY_SLOTS for pos in _TOAST_POSITIONS}


def _occupied(signature: dict, position: str) -> list:
    return [entry for entry in signature[position] if entry is not None]


def test_ephemeral_toast_state_signature_stable_between_ticks() -> None:
    """The signature must not change between interval ticks while a toast is visible.

    A changed signature means the display callback rewrites a slot's children,
    which since Dash 4.2.0 remounts the DOM node and replays the entry
    animation (the "one alert shows up 6 times" bug).
    """
    alert = create_alert("Test message", "info", ephemeral=True)
    t0 = alert["created_at"]

    slots_1, signature_1 = _ephemeral_toast_state([alert], t0 + 1)
    _, signature_2 = _ephemeral_toast_state([alert], t0 + 2, signature_1)
    assert slots_1["bottom-left"][0] == (alert, False)  # occupies slot 0, not dying
    assert signature_1 == signature_2

    # The signature is stored in a dcc.Store, so it must survive a JSON round
    # trip unchanged for the equality check to hold on the next tick.
    assert json.loads(json.dumps(signature_1)) == signature_1


def test_ephemeral_toast_state_signature_is_per_position() -> None:
    """Each position has its own slots so unrelated containers can get no_update."""
    bottom = create_alert("Bottom message", "info", ephemeral=True)
    center = create_alert(
        "Center message", "warning", ephemeral=True, position="center"
    )
    t0 = max(bottom["created_at"], center["created_at"])

    _, signature = _ephemeral_toast_state([bottom, center], t0 + 1)
    assert len(_occupied(signature, "bottom-left")) == 1
    assert len(_occupied(signature, "center")) == 1
    assert _occupied(signature, "top-right") == []


def test_toast_keeps_its_slot_when_a_sibling_expires() -> None:
    """A surviving toast must not move slots when a sibling disappears.

    If it moved (or shared a container with the sibling), its slot would be
    rewritten and Dash >= 4.2.0 would remount it, replaying its entry
    animation - the "A showed itself 3 times" symptom.
    """
    long_alert = create_alert("Stays 10s", "info", ephemeral=True, duration=10)
    short_alert = create_alert("Goes at 3s", "warning", ephemeral=True, duration=3)
    t0 = max(long_alert["created_at"], short_alert["created_at"])

    _, both = _ephemeral_toast_state([long_alert, short_alert], t0 + 1)
    assert both["bottom-left"][0][1] == "Stays 10s"
    assert both["bottom-left"][1][1] == "Goes at 3s"

    # The short alert dies, then expires. The long alert's slot must be
    # byte-identical across all three ticks so it is never rewritten.
    _, dying = _ephemeral_toast_state([long_alert, short_alert], t0 + 2.5, both)
    _, gone = _ephemeral_toast_state([long_alert, short_alert], t0 + 4, dying)

    assert both["bottom-left"][0] == dying["bottom-left"][0] == gone["bottom-left"][0]
    assert dying["bottom-left"][1][2] is True  # sibling is dying
    assert gone["bottom-left"][1] is None  # sibling's slot cleared


def test_ephemeral_toast_state_dying_and_expiry_change_signature() -> None:
    alert = create_alert("Test message", "info", ephemeral=True)
    t0 = alert["created_at"]

    _, signature_fresh = _ephemeral_toast_state([alert], t0 + 1)
    slots_dying, signature_dying = _ephemeral_toast_state(
        [alert], t0 + 4.5, signature_fresh
    )
    assert slots_dying["bottom-left"][0][1] is True  # exit animation render
    assert signature_dying != signature_fresh

    slots_expired, signature_expired = _ephemeral_toast_state(
        [alert], t0 + 5.5, signature_dying
    )
    assert all(entry is None for entry in slots_expired["bottom-left"])
    assert signature_expired == EMPTY_SIGNATURE


def test_ephemeral_toast_state_ignores_non_ephemeral_alerts() -> None:
    alert = create_alert("Test message", "info", ephemeral=False)
    _, signature = _ephemeral_toast_state([alert], alert["created_at"] + 1)
    assert signature == EMPTY_SIGNATURE
    assert _ephemeral_toast_state(None, 0.0)[1] == EMPTY_SIGNATURE
