import datetime
import logging
import time
from typing import Any

import dash_bootstrap_components as dbc
from dash import ALL
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash import no_update
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


_DEFAULT_ICONS = {
    "success": "feather:check-circle",
    "warning": "feather:alert-triangle",
    "info": "feather:info",
    "primary": "feather:bell",
    "secondary": "feather:bell",
    "light": "feather:bell",
    "dark": "feather:bell",
}


def create_alert(
    message: str,
    color: str | None = "info",
    ephemeral: bool | None = False,
    position: str | None = "bottom-left",
    duration: int | None = 5,
    icon: str | None = None,
) -> dict[str, Any]:
    """Creates a standardized alert record.

    Args:
        message: The alert message to display.
        color: The color of the alert, typically 'info', 'warning'. Defaults to 'info'.
        ephemeral: If True, the alert appears for 5 seconds but remains in the store for the modal. Defaults to False.
        position: Controls alert placement ("bottom-left", "center", "top-right", etc.).
        duration: Decides for how long the alert should show in seconds. Defaults to 5.
        icon: Defines the alert icon on the notification. Defaults to the icons listed in DashIconify ('Feather' icons) according to color.

    Returns:
        A dictionary containing the alert details, including timestamp, message, color, ephemeral status, and alert position.
    """
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "color": color,
        "ephemeral": ephemeral,
        "position": position,
        "duration": duration,
        "icon": icon or _DEFAULT_ICONS.get(color),
        # used to track how long it's been visible if ephemeral
        "created_at": time.time(),
    }


_TOAST_POSITIONS = ("bottom-left", "center", "top-right")
_MAX_TOASTS_PER_POSITION = 4

_ToastSlots = dict[str, list[tuple[dict[str, Any], bool] | None]]
_ToastSignature = dict[str, list[list[Any] | None]]


def _toast_slot_id(position: str, index: int) -> str:
    """Builds the id of a single toast slot.

    Args:
        position: One of the toast positions.
        index: The slot index within that position.

    Returns:
        The component id for that slot.
    """
    return f"alert-toast-{position}-{index}"


def _ephemeral_toast_state(
    alerts: list[dict[str, Any]] | None,
    now: float,
    previous_signature: _ToastSignature | None = None,
) -> tuple[_ToastSlots, _ToastSignature]:
    """Assigns the currently visible ephemeral alerts to fixed toast slots.

    Each toast lives in its own slot so that re-rendering one toast never
    rewrites a sibling's slot. Since Dash 4.2.0 any write to a container's
    children remounts every child in it (plotly/dash#3846), which restarts the
    CSS entry animation, so a toast must keep the same slot for its whole life.

    Args:
        alerts: The current list of alerts stored in the application.
        now: The current time as a unix timestamp.
        previous_signature: The signature from the previous tick, used to keep
            each toast in the slot it already occupies.

    Returns:
        A tuple of (slots, signature). slots maps each position to a fixed-length
        list holding either an (alert, is_dying) pair or None per slot, and
        signature is the JSON-serializable equivalent used to detect which slots
        actually changed.
    """
    previous = previous_signature if isinstance(previous_signature, dict) else {}
    slots: _ToastSlots = {
        position: [None] * _MAX_TOASTS_PER_POSITION for position in _TOAST_POSITIONS
    }

    pending = []
    for a in alerts or []:
        if not a.get("ephemeral", False):
            continue
        duration = a.get("duration", 5)
        age = now - a["created_at"]
        if age >= duration:
            continue
        position = a.get("position", "bottom-left")
        if position not in slots:
            position = "bottom-left"
        # str() because the signature round-trips through browser JSON, which
        # does not reliably preserve the float/int type of timestamps
        pending.append((position, str(a["created_at"]), a, age > duration - 0.8))

    unplaced = []
    for position, key, alert, dying in pending:
        for index, entry in enumerate(previous.get(position) or []):
            if (
                index < _MAX_TOASTS_PER_POSITION
                and entry
                and entry[0] == key
                and slots[position][index] is None
            ):
                slots[position][index] = (alert, dying)
                break
        else:
            unplaced.append((position, key, alert, dying))

    for position, _key, alert, dying in unplaced:
        for index in range(_MAX_TOASTS_PER_POSITION):
            if slots[position][index] is None:
                slots[position][index] = (alert, dying)
                break

    signature: _ToastSignature = {
        position: [
            (
                [str(entry[0]["created_at"]), entry[0]["message"], entry[1]]
                if entry
                else None
            )
            for entry in slots[position]
        ]
        for position in _TOAST_POSITIONS
    }
    return slots, signature


class AlertHandler:
    """Manages alerts for the application.

    This class provides functionality for:
    - Displaying a modal with all alerts, which can be filtered and dismissed.
    - Showing ephemeral alerts at the top-middle of the screen for 5 seconds without removing them from the store.

    In order to add alerts to the AlertHandler, you need to modify your callback to include an extra State and Output and append your alert to the list of existing alerts.

    Example:
        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            State("alert_store", "data"),
        )
        def callback_function_with_alert(alert_log):
            alert_log.append(
                create_alert(
                    f"Your message",
                    "info", # The type of alert
                    ephemeral=True, # If true, pops up as a notification
                )
            )
            return alert_log
    """

    def __init__(self) -> None:
        """Initializes the AlertHandler instance.

        This method sets up the necessary callbacks for managing alerts.
        """
        self.callbacks()

    def layout(self) -> html.Div:
        """Creates the layout for the AlertHandler.

        The layout includes:
        - `dcc.Store` components for storing all alerts, the current filter, and the last-rendered toast signature (used to skip redundant re-renders).
        - A fixed container for displaying ephemeral alerts.
        - An interval component to drive ephemeral updates.
        - A modal with filter buttons and a dismissable alert container.
        - A button to open the modal.

        Returns:
            A Dash HTML Div component containing the layout for the AlertHandler.
        """
        return html.Div(
            [
                dcc.Store(
                    id="alert_store", data=[create_alert("Application started", "info")]
                ),
                dcc.Store(id="alert_filter", data="all"),
                dcc.Store(id="alert_toast_signature", data={}),
                *[
                    html.Div(
                        [
                            html.Div(id=_toast_slot_id(position, index))
                            for index in range(_MAX_TOASTS_PER_POSITION)
                        ],
                        id=f"alert-container-{position}",
                        className=f"alert-container {position}",
                    )
                    for position in _TOAST_POSITIONS
                ],
                dcc.Interval(
                    id="alert_ephemeral_interval", interval=1000, n_intervals=0
                ),  # The 1s tick drives toast appearance/expiry; idle ticks are cheap because the display callback raises PreventUpdate when the toast signature is unchanged.
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Varsler")),
                        dbc.ModalBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis alle",
                                                id="alert_filter_all",
                                                className="ssb-btn primary-btn",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun info",
                                                id="alert_filter_info",
                                                className="ssb-btn primary-btn",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun editeringer",
                                                id="alert_filter_success",
                                                className="ssb-btn primary-btn",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun advarsel",
                                                id="alert_filter_warning",
                                                className="ssb-btn primary-btn",
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                html.Div(id="alert_modal_container"),
                            ]
                        ),
                    ],
                    id="alerts_modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button(
                    DashIconify(icon="feather:bell", width=24),
                    "App-logg",
                    "sidebar-alerts-button",
                ),
            ]
        )

    def callbacks(self) -> None:
        """Registers Dash callbacks for the AlertHandler functionality.

        This method defines callbacks for:
        - Toggling the alert modal.
        - Setting the alert filter based on user input.
        - Displaying alerts in the modal, filtered by type.
        - Removing dismissed alerts from the store.
        - Displaying ephemeral alerts.

        Notes:
            - Alerts must be added to each callback to ensure proper functionality.
        """

        @callback(  # type: ignore[misc]
            Output("alerts_modal", "is_open"),
            Input("sidebar-alerts-button", "n_clicks"),
            State("alerts_modal", "is_open"),
            prevent_initial_call=True,
        )
        def toggle_modal(n: int | None, is_open: bool) -> bool:
            """Toggles the visibility of the alert modal.

            Args:
                n: The number of clicks on the sidebar button.
                is_open: The current state of the modal (open or closed).

            Returns:
                bool: The new state of the modal (True for open, False for closed).
            """
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            Output("alert_filter", "data"),
            Input("alert_filter_all", "n_clicks"),
            Input("alert_filter_info", "n_clicks"),
            Input("alert_filter_success", "n_clicks"),
            Input("alert_filter_warning", "n_clicks"),
            prevent_initial_call=True,
        )
        def set_filter(
            _: int | None,
            __: int | None,
            ___: int | None,
            ____: int | None,
        ) -> str:
            """Updates the alert filter based on the clicked filter button.

            Args:
                _: Number of clicks on the "Vis alle" button.
                __: Number of clicks on the "Vis kun info" button.
                ___: Number of clicks on the "Vis kun editeringer" button.
                ____: Number of clicks on the "Vis kun advarsel" button.
                _____: Number of clicks on the "Vis kun feil" button.

            Returns:
                str: The selected filter type ('all', 'info' or 'warning').
            """  # noqa: DOC102, DOC103, DOC106
            triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None
            if triggered_id == "alert_filter_info":
                return "info"
            elif triggered_id == "alert_filter_success":
                return "success"
            elif triggered_id == "alert_filter_warning":
                return "warning"
            else:
                return "all"

        @callback(  # type: ignore[misc]
            Output("alert_modal_container", "children"),
            Input("alert_store", "data"),
            Input("alert_filter", "data"),
        )
        def show_modal_alerts(
            alerts: list[dict[str, Any]], current_filter: str
        ) -> list[dbc.Alert]:
            """Displays alerts in the modal, filtered by type.

            Each alert is dismissable using a pattern-matching ID.

            Args:
                alerts: A list of all alerts stored in the application.
                current_filter: The current filter type ('all', 'info' or 'warning').

            Returns:
                A list of Dash Bootstrap Components alerts to display in the modal.
            """
            if not alerts:
                return []

            if current_filter != "all":
                alerts = [a for a in alerts if a["color"] == current_filter]

            components = []
            for i, alert_data in enumerate(alerts):
                components.append(
                    dbc.Alert(
                        [
                            html.Div(
                                DashIconify(icon=_map_icon(alert_data["color"])),
                                className="icon-panel",
                            ),
                            html.Div(
                                [
                                    html.Small(
                                        alert_data["timestamp"],
                                        className="alert-timestamp content me-3",
                                    ),
                                    dcc.Markdown(
                                        alert_data["message"],
                                        className="content",
                                        style={
                                            "display": "inline-block",
                                            "font-size": "16px",
                                        },
                                    ),
                                ],
                                className="dialog-content",
                            ),
                        ],
                        dismissable=True,
                        is_open=True,
                        id={"type": "modal_alert", "index": i},
                        className=f"ssb-dialog {alert_data['color']} mb-2",
                    )
                )
            return components

        def _map_icon(variant: str) -> str:
            return {
                "warning": "feather:alert-triangle",
                "info": "feather:info",
                "success": "feather:check-circle",
            }.get(variant, "feather:info")

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input({"type": "modal_alert", "index": ALL}, "is_open"),
            State("alert_store", "data"),
            State("alert_filter", "data"),
            prevent_initial_call=True,
        )
        def remove_dismissed_alerts(
            is_open_list: list[dbc.Alert],
            current_alerts: list[dict[str, Any]],
            current_filter: str,
        ) -> list[dict[str, Any]]:
            """Removes alerts that have been dismissed by the user.

            If the user dismisses an alert in the modal (by clicking 'x'), this callback removes the alert from the store.

            Args:
                is_open_list: A list indicating the open/closed state of each alert in the modal.
                current_alerts: The current list of alerts stored in the application.
                current_filter: The currently active alert filter ('all', 'info', 'success' or 'warning').

            Returns:
                The updated list of alerts with dismissed alerts removed.
            """
            if not current_alerts or not is_open_list:
                return current_alerts

            # Reproduce the same filtered view the modal used
            filtered = [
                (i, a)
                for i, a in enumerate(current_alerts)
                if current_filter == "all" or a["color"] == current_filter
            ]

            to_remove = set()
            for display_index, (original_index, _) in enumerate(filtered):
                if (
                    display_index < len(is_open_list)
                    and not is_open_list[display_index]
                ):
                    to_remove.add(original_index)

            return [a for i, a in enumerate(current_alerts) if i not in to_remove]

        @callback(  # type: ignore[misc]
            *[
                Output(_toast_slot_id(position, index), "children")
                for position in _TOAST_POSITIONS
                for index in range(_MAX_TOASTS_PER_POSITION)
            ],
            Output("alert_toast_signature", "data"),
            Input("alert_ephemeral_interval", "n_intervals"),
            State("alert_store", "data"),
            State("alert_toast_signature", "data"),
        )
        def display_ephemeral_alerts(
            _: int,
            alerts: list[dict[str, Any]],
            previous_signature: _ToastSignature | None,
        ) -> tuple[Any, ...]:
            """Displays ephemeral alerts for the duration of each alert.

            Ephemeral alerts are not removed from the store, so they remain visible in the modal.
            Determines the location of the alert based on the input, where default is "bottom-left".

            Since Dash 4.2.0 every write to a container's children remounts the
            DOM nodes and replays the CSS entry animation (plotly/dash#3846).
            Each toast therefore gets its own slot, and only the slots that
            actually changed are written; unchanged ticks skip entirely.

            Args:
                _: The number of intervals elapsed since the application started.
                alerts: The current list of alerts stored in the application.
                previous_signature: The toast slot signature from the previous tick.

            Returns:
                The children of every toast slot (no_update where unchanged), plus the new toast signature.

            Raises:
                PreventUpdate: If no toast slot changed since the previous tick.
            """  # noqa: DOC102, DOC103
            slots, signature = _ephemeral_toast_state(
                alerts, time.time(), previous_signature
            )
            previous = (
                previous_signature if isinstance(previous_signature, dict) else {}
            )
            empty: list[list[Any] | None] = [None] * _MAX_TOASTS_PER_POSITION

            if all(
                signature[position] == (previous.get(position) or empty)
                for position in _TOAST_POSITIONS
            ):
                raise PreventUpdate

            def make_alert(a: dict[str, Any], dying: bool) -> dbc.Alert:
                icon = DashIconify(icon=a["icon"]) if a.get("icon") else None

                return dbc.Alert(
                    [
                        html.Div(icon, className="icon-panel"),
                        html.Div(
                            dcc.Markdown(
                                a["message"],
                                style={"font-size": "16px"},
                                className="content",
                            ),
                            className="dialog-content",
                        ),
                    ],
                    dismissable=False,
                    className=f"ssb-dialog {a['color']} alert-toast {'alert-dying' if dying else ''}",
                )

            children: list[Any] = []
            for position in _TOAST_POSITIONS:
                previous_slots = previous.get(position) or empty
                for index in range(_MAX_TOASTS_PER_POSITION):
                    was = previous_slots[index] if index < len(previous_slots) else None
                    if signature[position][index] == was:
                        children.append(no_update)
                        continue
                    entry = slots[position][index]
                    children.append(make_alert(entry[0], entry[1]) if entry else [])

            return (*children, signature)
