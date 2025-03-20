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
    message: str, color: str = "info", ephemeral: bool = False
) -> dict[str, Any]:
    """Create a standardized alert record.

    - color: typically 'info', 'warning', or 'danger'
    - ephemeral=True => the alert also appears top-center for 4s
                        (but remains in the store for the modal).
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
    """Manages alerts.

    - A modal that displays all alerts (filterable, dismissable).
    - An ephemeral "top-middle" area showing alerts for 4s, but not removed from store.
    """

    def __init__(self) -> None:
        """Initializes the AlertHandler module."""
        self.callbacks()

    def layout(self) -> html.Div:
        """Returns a Div containing.

        - dcc.Store for all alerts.
        - dcc.Store for current filter.
        - fixed container for ephemeral alerts.
        - interval to drive ephemeral updates.
        - a modal with filter buttons and a dismissable alert container.
        - a button to open the modal.
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
                    style={
                        "position": "fixed",
                        "bottom": "10px",
                        "left": "10px",
                        "zIndex": 2000,
                    },
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
        """Register Dash callbacks for the Alert handler functionality.

        Notes:
            - Alerts must be added to each callback.
        """

        @callback(  # type: ignore[misc]
            Output("alerts_modal", "is_open"),
            Input("sidebar-alerts-button", "n_clicks"),
            State("alerts_modal", "is_open"),
            prevent_initial_call=True,
        )
        def toggle_modal(n: int | None, is_open: bool) -> bool:
            """Open/close the error log modal."""
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
            """Update the filter store based on which filter button was clicked."""
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
            """Display the alerts in the modal, filtered by color/type.

            Each alert is dismissable with a pattern-matching ID.
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
            """Removes dismissed alerts.

            If the user dismisses an alert in the modal (clicks 'x'),
            remove that alert from the store.
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
            """Show ephemeral alerts at top-center for 4 seconds.

            We do NOT remove them from the store, so they remain visible in the modal.
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
