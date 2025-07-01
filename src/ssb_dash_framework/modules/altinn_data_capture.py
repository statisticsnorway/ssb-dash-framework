import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from plotly.graph_objects import Figure

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class AltinnDataCapture(ABC):
    """Provides a layout and functionality for a modal that offers a graphical overview of the data capture from altinn3.

    Attributes:
        time_units (list): A list of the time units used.
        database (object): The eimerdb connection.
    """

    implemented_database_types = ["eimerdb_default"]

    _id_number = 0

    def __init__(
        self,
        time_units: list[str],
        label: str = "🎣 Datafangst",
        database_type: str | None = None,
        database: object | None = None,
    ) -> None:  # TODO check type hint for time_units
        """Initializes the AntinnDataCapture module.

        Args:
            time_units (list): A list of the time units used.
            database (object): The eimerdb connection.

        Raises:
            TypeError: If database object does not have query method.
        """
        self.module_number = AltinnDataCapture._id_number
        self.module_name = self.__class__.__name__
        AltinnDataCapture._id_number += 1

        self.icon = "🎣"
        self.label = label
        self.database_type = database_type
        self.database = database
        self.time_units = time_units
        self.get_amount_func = (None,)
        self.get_cumulative_func = None
        self.is_valid()

        self.module_layout = self._create_layout()

        self.variableselector = VariableSelector(
            selected_inputs=self.time_units, selected_states=[]
        )
        self.module_callbacks()
        module_validator(self)

    def is_valid(self) -> None:
        """Checks if the module is valid."""
        if self.database:
            if not isinstance(self.database_type, str):
                raise TypeError("database_type must be a string.")
            if self.database_type not in AltinnDataCapture.implemented_database_types:
                raise ValueError(
                    f"database_type must be one of {AltinnDataCapture.implemented_database_types}."
                )
            if not hasattr(self.database, "query"):
                raise TypeError("The provided object does not have a 'query' method.")

        elif self.database_type is None:
            if self.get_amount_func is None or self.get_cumulative_func is None:
                raise ValueError(
                    "Either a database connection or custom functions must be provided."
                )
            else:
                raise NotImplementedError(
                    "Currently this behavior is not implemented"
                )  # TODO implement this functionality.
        if not isinstance(self.time_units, list) and not all(
            isinstance(unit, str) for unit in self.time_units
        ):
            raise TypeError("time_units must be a list of strings.")

    def _create_layout(self) -> html.Div:
        """Generates the layout for the AltinnDataCapture module.

        Returns:
            layout: A Div element containing components for the graphs.
        """
        layout = html.Div(
            # style={
            #    "display": "grid",
            #    "height": "100%",
            #    "grid-template-rows": "100%",
            # },
            children=[
                html.Div(
                    children=[
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Velg graf"),
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
                                                # width=12,
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
                                # style={
                                #    "position": "fixed",
                                #    "z-index": 9999,
                                # },
                            ),
                        ),
                    ],
                    # style={"width": "90%", "margin-left": "5%"},
                ),
            ],
        )
        logger.debug("AltinnDataCapture layout created")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Defines the layout for the AltinnDataCapture module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Registers Dash callbacks for the Visualiseringsbygger module.

        Notes:
            - `get_skjemas`: Gets all the schemas from the eimerdb enheter table and adds them to a dropdown.
            - `update_altinnskjema`: Updates the chosen schema from the variable selector.
            - `datafangstmodal_toggle`: Toggles the modal, which contains the layout.
            - 'datafangst_graph': Queries the skjemamottak table in eimerdb and returns a graph.
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]
        if self.database_type == "eimerdb_default":
            self.callbacks_eimerdb_default(dynamic_states)

    def callbacks_eimerdb_default(self, dynamic_states) -> None:
        @callback(  # type: ignore[misc]
            Output("datafangst-dd1", "options"),
            Output("datafangst-dd1", "value", allow_duplicate=True),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def get_skjemas(
            *args: Any,
        ) -> tuple[list[dict[str, str]], str]:  # TODO doublecheck return type hint
            df = self.database.query(
                "SELECT DISTINCT skjemaer FROM enheter",
                partition_select={
                    column: [value]
                    for column, value in zip(self.time_units, args, strict=False)
                },
            )
            all_skjemas = df["skjemaer"].dropna().str.split(",").sum()
            distinct_skjemas = list(set(s.strip() for s in all_skjemas))
            default_value = distinct_skjemas[0]
            skjema_options = [
                {"label": skjema, "value": skjema} for skjema in distinct_skjemas
            ]
            return skjema_options, default_value

        @callback(  # type: ignore[misc]
            Output("datafangst-graph1", "figure"),
            Input("datafangst-radioitem1", "value"),
            Input("datafangst-dd1", "value"),
            *dynamic_states,
        )
        def datafangst_graph(graph_option: str, skjema: str, *args: Any) -> Figure:
            partition_select = (
                {
                    column: [value]
                    for column, value in zip(
                        [skjema, *self.time_units], [skjema, *args], strict=False
                    )
                }
                if skjema
                else {
                    column: [value]
                    for column, value in zip(self.time_units, args, strict=False)
                }
            )
            if graph_option == "antall":
                df = self.database.query(
                    """SELECT dato_mottatt, 1 AS antall
                    FROM skjemamottak
                    WHERE dato_mottatt is not NULL""",
                    partition_select=partition_select,
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
                        "skjemamottak": partition_select,
                        "enheter": {
                            x: y for x, y in partition_select.items() if x != "skjema"
                        },
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


class AltinnDataCaptureTab(TabImplementation, AltinnDataCapture):
    def __init__(
        self,
        time_units: list[str],
        label: str = "🎣 Datafangst",
        database_type: str | None = None,
        database: object | None = None,
    ) -> None:
        AltinnDataCapture.__init__(
            self,
            time_units=time_units,
            label=label,
            database_type=database_type,
            database=database,
        )
        TabImplementation.__init__(self)


class AltinnDataCaptureWindow(WindowImplementation, AltinnDataCapture):
    def __init__(
        self,
        time_units: list[str],
        label: str = "Datafangst",
        database_type: str | None = None,
        database: object | None = None,
    ) -> None:
        AltinnDataCapture.__init__(
            self,
            time_units=time_units,
            label=label,
            database_type=database_type,
            database=database,
        )
        WindowImplementation.__init__(self)
