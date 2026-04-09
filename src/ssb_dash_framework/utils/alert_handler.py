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

from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


_DEFAULT_ICONS = {
    "success": "bi bi-check-circle-fill",
    "danger": "bi bi-x-circle-fill",
    "warning": "bi bi-exclamation-triangle-fill",
    "info": "bi bi-info-circle-fill",
    "primary": "bi bi-bell-fill",
    "secondary": "bi bi-bell-fill",
    "light": "bi bi-bell-fill",
    "dark": "bi bi-bell-fill",
}


def create_alert(
    message: str, color: str | None = "info", ephemeral: bool | None = False, position: str | None = "bottom-left", duration: int | None = 5, icon: str | None = None,
) -> dict[str, Any]:
    """Creates a standardized alert record.

    Args:
        message: The alert message to display.
        color: The color of the alert, typically 'info', 'warning', or 'danger'. Defaults to 'info'.
        ephemeral: If True, the alert appears for 5 seconds but remains in the store for the modal. Defaults to False.
        position: Controls alert placement ("bottom-left", "center", "top-right", etc.).
        duration: Decides for how long the alert should show in seconds. Defaults to 5.
        icon: Defines the alert icon on the notification. Defaults to the icons listed in _DEFAULT_ICONS according to color.

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
        - `dcc.Store` components for storing all alerts and the current filter.
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
                html.Div(id="alert-container-bottom-left", className="alert-container bottom-left"),
                html.Div(id="alert-container-center", className="alert-container center"),
                html.Div(id="alert-container-top-right", className="alert-container top-right"),
                dcc.Interval(
                    id="alert_ephemeral_interval", interval=1000, n_intervals=0
                ),  # Unsure of performance, check if maybe it should update less often.
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Varsler")),
                        dbc.ModalBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis alle", id="alert_filter_all"
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun info", id="alert_filter_info"
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun editeringer", id="alert_filter_success"
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun advarsel",
                                                id="alert_filter_warning",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Vis kun feil", id="alert_filter_danger"
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
                sidebar_button("📜", "App-logg", "sidebar-alerts-button"),
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
            Input("alert_filter_danger", "n_clicks"),
            prevent_initial_call=True,
        )
        def set_filter(
            _: int | None, __: int | None, ___: int | None, ____: int | None, _____: int | None
        ) -> str:
            """Updates the alert filter based on the clicked filter button.

            Args:
                _: Number of clicks on the "Vis alle" button.
                __: Number of clicks on the "Vis kun info" button.
                ___: Number of clicks on the "Vis kun editeringer" button.
                ____: Number of clicks on the "Vis kun advarsel" button.
                _____: Number of clicks on the "Vis kun feil" button.

            Returns:
                str: The selected filter type ('all', 'info', 'warning', or 'danger').
            """  # noqa: DOC102, DOC103, DOC106
            triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None
            if triggered_id == "alert_filter_info":
                return "info"
            elif triggered_id == "alert_filter_success":
                return "success"
            elif triggered_id == "alert_filter_warning":
                return "warning"
            elif triggered_id == "alert_filter_danger":
                return "danger"
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
                current_filter: The current filter type ('all', 'info', 'warning', or 'danger').

            Returns:
                A list of Dash Bootstrap Components alerts to display in the modal.
            """
            if not alerts:
                return []

            if current_filter != "all":
                alerts = [a for a in alerts if a["color"] == current_filter]

            components = []
            for i, alert_data in enumerate(alerts):
                icon = html.I(className=f"{alert_data['icon']} me-3 alert-icon") if alert_data.get("icon") else None
                components.append(
                    dbc.Alert(
                        [
                            html.Div(
                                [
                                    icon,
                                    html.Small(alert_data["timestamp"], className="alert-timestamp me-3"),
                                    dcc.Markdown(alert_data["message"], className="alert-message", style={"display": "inline-block"}),
                                ],
                                className="d-flex align-items-center",
                            ), 
                        ],
                        color=alert_data["color"],
                        dismissable=True,
                        is_open=True,
                        id={"type": "modal_alert", "index": i},
                        className="mb-2 alert-modal-item",
                    )
                )
            return components

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input({"type": "modal_alert", "index": ALL}, "is_open"),
            State("alert_store", "data"),
            State("alert_filter", "data"),
            prevent_initial_call=True,
        )
        def remove_dismissed_alerts(
            is_open_list: list[dbc.Alert], current_alerts: list[dict[str, Any]], current_filter
        ) -> list[dict[str, Any]]:
            """Removes alerts that have been dismissed by the user.

            If the user dismisses an alert in the modal (by clicking 'x'), this callback removes the alert from the store.

            Args:
                is_open_list: A list indicating the open/closed state of each alert in the modal.
                current_alerts: The current list of alerts stored in the application.

            Returns:
                The updated list of alerts with dismissed alerts removed.
            """
            if not current_alerts or not is_open_list:
                return current_alerts

            # Reproduce the same filtered view the modal used
            filtered = [
            (i, a) for i, a in enumerate(current_alerts)
                if current_filter == "all" or a["color"] == current_filter
            ]

            to_remove = set()
            for display_index, (original_index, _) in enumerate(filtered):
                if display_index < len(is_open_list) and not is_open_list[display_index]:
                    to_remove.add(original_index)

            return [a for i, a in enumerate(current_alerts) if i not in to_remove]

        @callback(  # type: ignore[misc]
            Output("alert-container-bottom-left", "children"),
            Output("alert-container-center", "children"),
            Output("alert-container-top-right", "children"),
            Input("alert_ephemeral_interval", "n_intervals"),
            State("alert_store", "data"),
        )
        def display_ephemeral_alerts(
            _: int, alerts: list[dict[str, Any]]
        ) -> tuple[list, list, list]:
            """Displays ephemeral alerts for 5 seconds.

            Ephemeral alerts are not removed from the store, so they remain visible in the modal.
            Determines the location of the alert based on the input, where default is "bottom-left".

            Args:
                _: The number of intervals elapsed since the application started.
                alerts: The current list of alerts stored in the application.

            Returns:
                A list of Dash Bootstrap Components alerts to display as ephemeral alerts.
            """  # noqa: DOC102, DOC103
            if not alerts:
                return [], [], []

            now = time.time()
            ephemeral_alerts = [
                a
                for a in alerts
                if a.get("ephemeral", False) and (now - a["created_at"] < a.get("duration", 5))
            ]

            def make_alert(a):
                now = time.time()
                dying = (now - a["created_at"]) > (a.get("duration", 6) - 0.8)
                icon = html.I(className=f"{a['icon']} me-2 alert-icon") if a.get("icon") else None

                return dbc.Alert(
                    [
                        html.Div(
                            [
                                icon,
                                dcc.Markdown(a["message"], className="alert-message"),
                            ],
                            className="d-flex align-items-center",
                        ),
                        # html.Small(a["timestamp"], className="alert-timestamp"),
                    ],
                    color=a["color"],
                    className=f"mb-2 alert-toast {'alert-dying' if dying else ''}",
                )

            bottom_left = [make_alert(a) for a in ephemeral_alerts if a.get("position", "bottom-left") == "bottom-left"]
            center      = [make_alert(a) for a in ephemeral_alerts if a.get("position") == "center"]
            top_right   = [make_alert(a) for a in ephemeral_alerts if a.get("position") == "top-right"]

            return bottom_left, center, top_right
