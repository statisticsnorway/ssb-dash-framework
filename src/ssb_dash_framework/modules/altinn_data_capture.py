import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from eimerdb import EimerDBInstance
from plotly.graph_objects import Figure

from ssb_dash_framework.utils import conn_is_ibis

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class AltinnDataCapture(ABC):
    """Provides a layout and functionality for a modal that offers a graphical overview of the data capture from altinn3.

    This module vizualizes the data capture and makes it easy to see how many forms have been received over time.

    Currently it only suppoerts the altinn_default with default schemas.
    """

    implemented_database_types: ClassVar[list[str]] = ["altinn_default"]

    _id_number: int = 0

    def __init__(
        self,
        time_units: list[str],
        label: str = "🎣 Datafangst",
        database_type: str | None = "altinn_default",
        database: object | None = None,
    ) -> None:  # TODO check type hint for time_units
        """Initializes the AntinnDataCapture module.

        Args:
            time_units (list): A list of the time units used.
            label (str): The label for the module.
            database_type (str | None): The selected method / set of database connections. Defaults to None.
            database (object): The database connection.

        Raises:
            TypeError if database is invalid connection type.
        """
        if not isinstance(database, EimerDBInstance) and not conn_is_ibis(database):
            raise TypeError(
                f"The database object must be 'EimerDBInstance' or ibis connection. Received: {type(database)}"
            )
        self.module_number = AltinnDataCapture._id_number
        self.module_name = self.__class__.__name__
        AltinnDataCapture._id_number += 1

        self.icon = "🎣"
        self.label = label
        self.database_type = database_type
        self.database = database
        self.get_amount_func = (None,)
        self.get_cumulative_func = None

        self.module_layout = self._create_layout()

        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.is_valid()
        self.module_callbacks()
        module_validator(self)

    def is_valid(self) -> None:
        """Checks if the module is valid.

        Raises:
            TypeError: If database object does not have query method.
            ValueError: If database_type is not one of the implemented types.
            NotImplementedError: If attempting to create custom functions.
        """
        if self.database:
            if not isinstance(self.database_type, str):
                raise TypeError("database_type must be a string.")
            if self.database_type not in AltinnDataCapture.implemented_database_types:
                raise NotImplementedError(
                    f"database_type must be one of {AltinnDataCapture.implemented_database_types}."
                )
            # if not hasattr(self.database, "query"):
            #     raise TypeError("The provided object does not have a 'query' method.")

        elif self.database_type is None:
            if self.get_amount_func is None or self.get_cumulative_func is None:
                raise ValueError(
                    "Either a database connection or custom functions must be provided."
                )
            else:
                raise NotImplementedError(
                    "Currently this behavior is not implemented"
                )  # TODO implement this functionality.
        if not isinstance(self.time_units, list):
            raise TypeError("time_units must be a list of strings.")
        if not all(isinstance(unit, str) for unit in self.time_units):
            raise TypeError("time_units must be a list of strings.")

    def _create_layout(self) -> html.Div:
        """Generates the layout for the AltinnDataCapture module.

        Returns:
            layout: A Div element containing components for the graphs.
        """
        layout = html.Div(
            className="altinn-data-capture",
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
                        className="altinn-data-capture-loading",
                        id="datafangst-graph1-loading",
                        children=[
                            dcc.Graph(
                                id="datafangst-graph1",
                            ),
                        ],
                        type="graph",
                    ),
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
        """Defines the callbacks for the AltinnDataCapture module."""
        dynamic_states = [
            self.variableselector.get_all_inputs(),
        ]
        if self.database_type == "altinn_default":
            self.callbacks_eimerdb_default(dynamic_states)

    def callbacks_eimerdb_default(self, dynamic_states: list[Input]) -> None:
        """Defines the callbacks when using the altinn_default database type."""

        @callback(  # type: ignore[misc]
            Output("datafangst-dd1", "options"),
            Output("datafangst-dd1", "value", allow_duplicate=True),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def get_skjemas(
            *args: Any,
        ) -> tuple[list[dict[str, str]], str]:  # TODO doublecheck return type hint
            logger.debug(
                "Args:\n" + "\n".join([f"arg{i}: {arg}" for i, arg in enumerate(args)])
            )
            df = self.database.query(
                "SELECT DISTINCT skjema FROM enheter",
                partition_select={
                    column: [value]
                    for column, value in zip(self.time_units, args, strict=False)
                },
            )
            all_skjemas = df["skjema"].dropna().str.split(",").sum()
            distinct_skjemas = list(set(s.strip() for s in all_skjemas))
            default_value = distinct_skjemas[0]
            skjema_options = [
                {"label": skjema, "value": skjema} for skjema in distinct_skjemas
            ]
            logger.debug(
                f"get_skjemas returns. skjema_options: {skjema_options}, default_value: {default_value}"
            )
            return skjema_options, default_value

        @callback(  # type: ignore[misc]
            Output("datafangst-graph1", "figure"),
            Input("datafangst-radioitem1", "value"),
            Input("datafangst-dd1", "value"),
            *dynamic_states,
        )
        def datafangst_graph(graph_option: str, skjema: str, *args: Any) -> Figure:
            logger.debug(
                "Args:\n"
                f"graph_option: {graph_option}\n"
                f"skjema: {skjema}\n"
                "\n".join([f"arg{i}: {arg}" for i, arg in enumerate(args)])
            )
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

            elif graph_option == "kumulativ":
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
            else:
                logger.debug(
                    f"Something went wrong, args: {graph_option}, {skjema}, {args}"
                )


class AltinnDataCaptureTab(TabImplementation, AltinnDataCapture):
    """AltinnDatacapture implemented as a tab."""

    def __init__(
        self,
        time_units: list[str],
        label: str = "🎣 Datafangst",
        database_type: str | None = "altinn_default",
        database: object | None = None,
    ) -> None:
        """Initializes the AltinnDataCaptureTab module."""
        AltinnDataCapture.__init__(
            self,
            time_units=time_units,
            label=label,
            database_type=database_type,
            database=database,
        )
        TabImplementation.__init__(self)


class AltinnDataCaptureWindow(WindowImplementation, AltinnDataCapture):
    """AltinnDatacapture implemented as a window."""

    def __init__(
        self,
        time_units: list[str],
        label: str = "Datafangst",
        database_type: str | None = "altinn_default",
        database: object | None = None,
    ) -> None:
        """Initializes the AltinnDataCaptureWindow module."""
        AltinnDataCapture.__init__(
            self,
            time_units=time_units,
            label=label,
            database_type=database_type,
            database=database,
        )
        WindowImplementation.__init__(self)
