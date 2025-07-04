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


def create_alert(
    message: str, color: str | None = "info", ephemeral: bool | None = False
) -> dict[str, Any]:
    """Creates a standardized alert record.

    Args:
        message (str): The alert message to display.
        color (str, optional): The color of the alert, typically 'info', 'warning', or 'danger'. Defaults to 'info'.
        ephemeral (bool, optional): If True, the alert appears at the top-center for 4 seconds but remains in the store for the modal. Defaults to False.

    Returns:
        dict[str, Any]: A dictionary containing the alert details, including timestamp, message, color, and ephemeral status.
    """
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "color": color,
        "ephemeral": ephemeral,
        # used to track how long it's been visible if ephemeral
        "created_at": time.time(),
    }


class AlertHandler:
    """Manages alerts for the application.

    This class provides functionality for:
    - Displaying a modal with all alerts, which can be filtered and dismissed.
    - Showing ephemeral alerts at the top-middle of the screen for 4 seconds without removing them from the store.
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
            html.Div: A Dash HTML Div component containing the layout for the AlertHandler.
        """
        return html.Div(
            [
                # Stores for alerts and filter
                dcc.Store(
                    id="alert_store", data=[create_alert("Application started", "info")]
                ),
                dcc.Store(id="alert_filter", data="all"),
                # Container for ephemeral alerts.
                html.Div(
                    id="alert_ephemeral_container",
                    className="alert-container",
                ),
                dcc.Interval(
                    id="alert_ephemeral_interval", interval=1000, n_intervals=0
                ),  # Unsure of performance, check if maybe it should update less often.
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Varsler")),
                        dbc.ModalBody(
                            [
                                # Filter buttons
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
                sidebar_button("📜", "App logg", "sidebar-alerts-button"),
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
                n (int | None): The number of clicks on the sidebar button.
                is_open (bool): The current state of the modal (open or closed).

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
            Input("alert_filter_warning", "n_clicks"),
            Input("alert_filter_danger", "n_clicks"),
            prevent_initial_call=True,
        )
        def set_filter(
            _: int | None, __: int | None, ___: int | None, ____: int | None
        ) -> str:
            """Updates the alert filter based on the clicked filter button.

            Args:
                _ (int | None): Number of clicks on the "Vis alle" button.
                __ (int | None): Number of clicks on the "Vis kun info" button.
                ___ (int | None): Number of clicks on the "Vis kun advarsel" button.
                ____ (int | None): Number of clicks on the "Vis kun feil" button.

            Returns:
                str: The selected filter type ('all', 'info', 'warning', or 'danger').
            """
            triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None
            if triggered_id == "alert_filter_info":
                return "info"
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
                alerts (list[dict[str, Any]]): A list of all alerts stored in the application.
                current_filter (str): The current filter type ('all', 'info', 'warning', or 'danger').

            Returns:
                list[dbc.Alert]: A list of Dash Bootstrap Components alerts to display in the modal.
            """
            if not alerts:
                return []

            # Filter by color if not "all"
            if current_filter != "all":
                alerts = [a for a in alerts if a["color"] == current_filter]

            # Build dismissable alerts
            components = []
            for i, alert_data in enumerate(alerts):
                components.append(
                    dbc.Alert(
                        [
                            html.Span(
                                alert_data["timestamp"] + " ", className="text-muted"
                            ),
                            alert_data["message"],
                        ],
                        color=alert_data["color"],
                        dismissable=True,
                        is_open=True,
                        id={"type": "modal_alert", "index": i},
                        className="mb-2",
                    )
                )
            return components

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input({"type": "modal_alert", "index": ALL}, "is_open"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def remove_dismissed_alerts(
            is_open_list: list[dbc.Alert], current_alerts: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """Removes alerts that have been dismissed by the user.

            If the user dismisses an alert in the modal (by clicking 'x'), this callback removes the alert from the store.

            Args:
                is_open_list (list[bool]): A list indicating the open/closed state of each alert in the modal.
                current_alerts (list[dict[str, Any]]): The current list of alerts stored in the application.

            Returns:
                list[dict[str, Any]]: The updated list of alerts with dismissed alerts removed.
            """
            if not current_alerts or not is_open_list:
                return current_alerts

            new_list = []
            display_index = 0
            for alert_item in current_alerts:
                if display_index < len(is_open_list):
                    if is_open_list[display_index]:  # still open => keep
                        new_list.append(alert_item)
                    display_index += 1
                else:
                    # Not displayed (perhaps filtered out?), so keep
                    new_list.append(alert_item)

            return new_list

        @callback(  # type: ignore[misc]
            Output("alert_ephemeral_container", "children"),
            Input("alert_ephemeral_interval", "n_intervals"),
            State("alert_store", "data"),
        )
        def display_ephemeral_alerts(
            _: int, alerts: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """Displays ephemeral alerts for 4 seconds.

            Ephemeral alerts are not removed from the store, so they remain visible in the modal.

            Args:
                _ (int): The number of intervals elapsed since the application started.
                alerts (list[dict[str, Any]]): The current list of alerts stored in the application.

            Returns:
                list[dbc.Alert]: A list of Dash Bootstrap Components alerts to display as ephemeral alerts.
            """
            if not alerts:
                return []

            now = time.time()
            ephemeral_alerts = [
                a
                for a in alerts
                if a.get("ephemeral", False) and (now - a["created_at"] < 4)
            ]

            comps = []
            for a in ephemeral_alerts:
                comps.append(
                    dbc.Alert(
                        [
                            html.Small(a["timestamp"] + ": ", className="text-muted"),
                            a["message"],
                        ],
                        color=a["color"],
                        className="mb-2",
                    )
                )
            return comps
