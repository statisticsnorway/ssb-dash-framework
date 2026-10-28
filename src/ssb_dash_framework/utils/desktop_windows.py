
"""Reusable desktop-window layout components."""

from dash import html
from dash.development.base_component import Component
from dash_iconify import DashIconify


def desktop_window(
    module_id: str,
    title: str | Component,
    children: Component | list[Component],
    icon: str | Component = "",
    width: str = "1100px",
    height: str = "700px",
    open_button_id: str | None = None,
) -> html.Div:
    """Create a draggable, resizable desktop-style window."""

    if isinstance(title, str):
        title = html.Span(title, className="modal-title-text")

    return html.Div(
        id=f"{module_id}-window",
        className="desktop-window",
        **(
            {"data-open-button-id": open_button_id}
            if open_button_id
            else {}
        ),
        style={
            "display": "none",
            "left": "80px",
            "top": "40px",
            "width": width,
            "height": height,
        },
        children=[
            html.Div(
                className="desktop-window-titlebar",
                children=[
                    html.Div(
                        className="desktop-window-title",
                        children=[
                            html.Span(icon, className="modal-title-icon"),
                            title,
                        ],
                    ),
                    html.Div(
                        className="desktop-window-controls",
                        children=[
                            html.Button(
                                "_",
                                id=f"{module_id}-window-minimize",
                                className="desktop-window-control",
                                title="Minimer vindu",
                                n_clicks=0,
                            ),
                            html.Button(
                                children=[
                                    DashIconify(
                                        icon="feather:maximize-2",
                                        width=16,
                                        className="window-maximize-icon",
                                    ),
                                    DashIconify(
                                        icon="feather:minimize-2",
                                        width=16,
                                        className="window-restore-icon",
                                    ),
                                ],
                                id=f"{module_id}-window-maximize",
                                className="desktop-window-control",
                                title="Maksimer vindu",
                                n_clicks=0,
                            ),
                            html.Button(
                                "×",
                                id=f"{module_id}-window-close",
                                className="desktop-window-control",
                                title="Lukk vindu",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="desktop-window-body dbc dbc-ag-grid",
                children=children,
            ),
            *[
                html.Div(
                    className=(
                        f"desktop-window-resize-handle resize-{edge}"
                    ),
                    **{"data-resize-edge": edge},
                )
                for edge in ("n", "s", "e", "w", "ne", "nw", "se", "sw")
            ],
        ],
    )
