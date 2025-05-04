from typing import Any
from typing import Literal

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ..utils.functions import sidebar_button


class AltinnDataCapture:
    """Provides a layout and functionality for a modal that offers a graphical overview of the data capture from altinn3.

    Attributes:
        time_units (list): A list of the time units used.
        database (object): The eimerdb connection.
    """

    def __init__(self, time_units: list, database: object) -> None:
        """Initializes the AntinnDataCapture module.

        Args:
            time_units (list): A list of the time units used.
            database (object): The eimerdb connection.

        Raises:
            TypeError: If database object does not have query method.
        """
        if not hasattr(database, "query"):
            raise TypeError("The provided object does not have a 'query' method.")
        self.time_units = time_units
        self.database = database
        self.callbacks()

    def layout(self) -> html.Div:
        """Generates the layout for the AltinnDataCapture module.

        Returns:
            layout: A Div element containing components for the graphs.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.ModalTitle("🎣 Datafangst"), width="auto"
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "🖵", id="datafangst-modal-fullscreen"
                                        ),
                                        width="auto",
                                        className="ms-auto",
                                    ),
                                ],
                                className="w-100",
                                align="center",
                                justify="between",
                            )
                        ),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    style={
                                        "display": "grid",
                                        "height": "100%",
                                        "grid-template-rows": "100%",
                                    },
                                    children=[
                                        html.Div(
                                            children=[
                                                dbc.Col(
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Velg graf"
                                                                    ),
                                                                    dbc.RadioItems(
                                                                        options=[
                                                                            {
                                                                                "label": "Antall/dag",
                                                                                "value": "antall",
                                                                            },
                                                                            {
                                                                                "label": "Kumulativ",
                                                                                "value": "kumulativ",
                                                                            },
                                                                        ],
                                                                        value="antall",
                                                                        id="datafangst-radioitem1",
                                                                    ),
                                                                ],
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Skjema",
                                                                        width=12,
                                                                        className="mb-1",
                                                                    ),
                                                                    dbc.Col(
                                                                        dcc.Dropdown(
                                                                            id="datafangst-dd1",
                                                                            className="dbc",
                                                                        )
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                ),
                                                dbc.Col(
                                                    dcc.Loading(
                                                        id="datafangst-graph1-loading",
                                                        children=[
                                                            dcc.Graph(
                                                                id="datafangst-graph1",
                                                            ),
                                                        ],
                                                        type="graph",
                                                        style={
                                                            "position": "fixed",
                                                            "z-index": 9999,
                                                        },
                                                    ),
                                                ),
                                            ],
                                            style={"width": "90%", "margin-left": "5%"},
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                    id="datafangst-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("🎣", "Datafangst", "sidebar-datafangst-button"),
            ],
        )
        return layout

    def create_partition_select(self, skjema: str | None = None, **kwargs: Any) -> dict:
        """Creates the partition select argument based on the chosen time units."""
        partition_select = {
            unit: [kwargs[unit]] for unit in self.time_units if unit in kwargs
        }
        if skjema is not None:
            partition_select["skjema"] = [skjema]
        return partition_select

    def create_callback_components(
        self, input_type: Literal["Input", "State"] = "Input"
    ) -> list:
        """Generates a list of dynamic Dash Input or State components."""
        component = Input if input_type == "Input" else State
        return [component(f"test-{unit}", "value") for unit in self.time_units]

    def callbacks(self) -> None:
        """Registers Dash callbacks for the Visualiseringsbygger module.

        Notes:
            - `get_skjemas`: Gets all the schemas from the eimerdb enheter table and adds them to a dropdown.
            - `update_altinnskjema`: Updates the chosen schema from the variable selector.
            - `datafangstmodal_toggle`: Toggles the modal, which contains the layout.
            - 'datafangst_graph': Queries the skjemamottak table in eimerdb and returns a graph.
        """

        @callback(
            Output("datafangst-dd1", "options"),
            Output("datafangst-dd1", "value", allow_duplicate=True),
            *self.create_callback_components("Input"),
            prevent_initial_call=True,
        )
        def get_skjemas(*args: Any):
            partition_args = dict(zip(self.time_units, args, strict=False))
            df = self.database.query(
                "SELECT DISTINCT skjemaer FROM enheter",
                partition_select=self.create_partition_select(
                    skjema=None, **partition_args
                ),
            )
            all_skjemas = df["skjemaer"].dropna().str.split(",").sum()
            distinct_skjemas = list(set(s.strip() for s in all_skjemas))
            default_value = distinct_skjemas[0]
            skjema_options = [
                {"label": skjema, "value": skjema} for skjema in distinct_skjemas
            ]
            return skjema_options, default_value

        @callback(
            Output("datafangst-dd1", "value", allow_duplicate=True),
            Input("var-altinnskjema", "value"),
            prevent_initial_call=True,
        )
        def update_altinnskjema(altinnskjema: str) -> str:
            return altinnskjema

        @callback(
            Output("datafangst-modal", "fullscreen"),
            Input("datafangst-modal-fullscreen", "n_clicks"),
            State("datafangst-modal", "fullscreen"),
        )
        def toggle_fullscreen_modal(n_clicks: int, fullscreen_state):
            if n_clicks > 0:
                if fullscreen_state == True:
                    fullscreen = "xxl-down"
                else:
                    fullscreen = True
                return fullscreen

        @callback(
            Output("datafangst-modal", "is_open"),
            Input("sidebar-datafangst-button", "n_clicks"),
            State("datafangst-modal", "is_open"),
        )
        def datafangstmodal_toggle(n: int, is_open: bool) -> bool:
            if n:
                return not is_open
            return is_open

        @callback(
            Output("datafangst-graph1", "figure"),
            Input("datafangst-radioitem1", "value"),
            Input("datafangst-dd1", "value"),
            *self.create_callback_components("State"),
        )
        def datafangst_graph(graph_option: str, skjema: str, *args: Any):
            partition_args = dict(zip(self.time_units, args, strict=False))
            if graph_option == "antall":
                df = self.database.query(
                    """SELECT dato_mottatt, 1 AS antall
                    FROM skjemamottak
                    WHERE dato_mottatt is not NULL""",
                    partition_select=self.create_partition_select(
                        skjema=skjema, **partition_args
                    ),
                )

                df = (
                    df.groupby(df["dato_mottatt"].dt.date)["antall"].sum().reset_index()
                )

                fig = px.bar(
                    data_frame=df,
                    x=df["dato_mottatt"],
                    y=df["antall"],
                    template="plotly_dark",
                )
                return fig

            if graph_option == "kumulativ":
                df = self.database.query(
                    """SELECT ranked.dato_mottatt,
                        COUNT(DISTINCT ranked.ident) AS antall,
                        subquery.antall_tot
                    FROM (
                        SELECT ident, dato_mottatt,
                               ROW_NUMBER() OVER (
                                   PARTITION BY ident ORDER BY dato_mottatt DESC
                                   ) AS rn
                        FROM skjemamottak
                        WHERE dato_mottatt IS NOT NULL
                    ) AS ranked
                    JOIN (
                        SELECT COUNT(*) AS antall_tot
                        FROM enheter
                    ) AS subquery ON true
                    WHERE ranked.rn = 1
                    GROUP BY ranked.dato_mottatt, subquery.antall_tot
                    ORDER BY ranked.dato_mottatt;""",
                    partition_select={
                        "skjemamottak": self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                        "enheter": self.create_partition_select(
                            skjema=None, **partition_args
                        ),
                    },
                )

                df["kumulativt_antall"] = df["antall"].cumsum()
                antall_tot = df["antall_tot"].iloc[0]
                df["percentage_filled"] = (df["kumulativt_antall"] / antall_tot) * 100
                x_last = df["dato_mottatt"].iloc[-1]
                y_last = df["kumulativt_antall"].iloc[-1]
                last_percentage = df["percentage_filled"].iloc[-1]

                fig = px.area(
                    df,
                    x="dato_mottatt",
                    y="kumulativt_antall",
                    title="Kumulativt antall innsamlede skjemaer",
                    labels={
                        "kumulativt_antall": "Totalt antall skjema mottatt",
                        "dato_mottatt": "Dato",
                    },
                    line_shape="linear",
                    template="plotly_dark",
                    hover_data={"percentage_filled": ":.2f"},
                )

                fig.add_hline(
                    y=antall_tot,
                    line_dash="dash",
                    annotation_text="Enheter som har mottatt skjema",
                    annotation_position="top left",
                )

                fig.add_annotation(
                    x=x_last,
                    y=y_last - (antall_tot * 0.05),
                    text=f"{last_percentage:.1f}%",
                    showarrow=False,
                    align="center",
                    borderpad=5,
                )
                return fig
