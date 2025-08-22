import logging
import re
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.eimerdb_helpers import create_partition_select
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)

default_col_def = {
    "resizable": True,
    "sortable": True,
    "editable": False,
}

INITIAL_OPTIONS = [
    {"label": "Alle skjemaer", "value": "all"},
    {"label": "Bare valgt skjema (ingen valgt)", "value": "none"},
]

SQL_COLUMN_CONCAT = " || '_' || "


class AggDistPlotter(ABC):
    """The AggDistPlotter module lets you view macro values for your variables and find the distribution between them and the largest contributors.

    This module requires your data to follow the default eimerdb structure and requires som specific variables defined in the variable selector.
    """

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the callbacks.
            "ident",
            "valgt_tabell",
            "altinnskjema",
        ]
    )

    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the AggDistPlotter.

        Args:
            time_units (list[str]): Your time variables used in the variable selector. Example year, quarter, month, etc.
            conn (object): A connection object to a database. It must have a .query method that can handle SQL queries.
                Currently designed with eimerdb in mind.
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        assert hasattr(
            conn, "query"
        ), (  # Necessary because of mypy
            "The database object must have a 'query' method."
        )
        self.module_number = AggDistPlotter._id_number
        self.module_name = self.__class__.__name__
        AggDistPlotter._id_number += 1

        self.icon = "🌌"
        self.label = "Aggregering"

        self.time_units = time_units
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.conn = conn

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in AggDistPlotter._required_variables:
            try:
                self.variableselector.get_option(var)
            except ValueError as e:
                raise ValueError(
                    f"AggDistPlotter requires the variable selector option '{var}' to be set."
                ) from e

    def _create_layout(self) -> html.Div:
        """Generates the layout for the AggDistPlotter module."""
        layout = html.Div(
            className="aggdistplotter",
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Refresh/hent data",
                                id="aggdistplotter-refresh",
                            ),
                        ),
                        dbc.Col(
                            dcc.RadioItems(
                                id="aggdistplotter-radioitems",
                                options=INITIAL_OPTIONS,
                                value="all",
                            ),
                        ),
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.P("Velg rullerende tidsenhet"),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="aggdistplotter-rullvar-dd",
                                            options=[
                                                {
                                                    "label": unit,
                                                    "value": unit,
                                                }
                                                for unit in self.time_units
                                            ],
                                            value=(
                                                self.time_units[0]
                                                if self.time_units
                                                else None
                                            ),
                                            clearable=False,
                                            className="dbc aggdistplotter-dropdown",
                                        ),
                                        width="auto",
                                    ),
                                ],
                                align="center",
                            )
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dag.AgGrid(
                                id="aggdistplotter-table",
                                defaultColDef=default_col_def,
                                className="ag-theme-alpine-dark header-style-on-filter",
                                columnSize="responsiveSizeToFit",
                                dashGridOptions={
                                    "rowHeight": 38,
                                    "suppressLoadingOverlay": True,
                                },
                            ),
                            width=12,
                        )
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.RadioItems(
                                id="aggdistplotter-graph-type",
                                options=[
                                    {
                                        "label": "📦 Boksplott",
                                        "value": "box",
                                    },
                                    {
                                        "label": "🎻 Fiolin",
                                        "value": "fiolin",
                                    },
                                    {
                                        "label": "🥇 Bidrag",
                                        "value": "bidrag",
                                    },
                                ],
                                value="box",
                                inline=True,
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-info me-2",
                                labelCheckedClassName="active",
                            ),
                            width=12,
                        )
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="aggdistplotter-graph-loading",
                                children=[
                                    dcc.Graph(
                                        id="aggdistplotter-graph",
                                        className="m-1",
                                    )
                                ],
                                type="graph",
                            ),
                            width=12,
                        )
                    ]
                ),
            ],
        )
        logger.debug("Layout generated.")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the Aarsregnskap module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def update_partition_select(
        self, partition_dict: dict[str, list[int | str]], key_to_update: str
    ) -> dict[str, list[int | str]]:
        """Updates the partition select dictionary.

        Adds the previous value (N-1) to the list for a single specified key.

        :param partition_dict: Dictionary containing lists of values
        :param key_to_update: Key to update by appending (N-1)
        :return: Updated dictionary
        """
        logger.debug(
            f"Arg values\npartition_dict: {partition_dict}\nkey_to_update: {key_to_update}"
        )
        if partition_dict.get(key_to_update):
            min_value = min(partition_dict[key_to_update])
            partition_dict[key_to_update].append(int(min_value) - 1)
        logger.debug(f"Returning: {partition_dict}")
        return partition_dict

    def module_callbacks(self) -> None:
        """Defines the callbacks for the AggDistPlotter module."""
        dynamic_states = self.variableselector.get_inputs()

        @callback(  # type: ignore[misc]
            Output("aggdistplotter-radioitems", "options"),
            Input("var-altinnskjema", "value"),
        )
        def oppdater_valgt_skjema(skjema: str) -> list[dict[str, str]]:
            logger.debug(f"Skjema: {skjema}")
            if skjema:
                radio_item_options = [
                    {"label": "Alle skjemaer", "value": "all"},
                    {"label": f"Bare {skjema}", "value": skjema},
                ]
                logger.debug(f"Returning:\n{radio_item_options}")
                return radio_item_options
            else:
                logger.debug(f"Returning: {INITIAL_OPTIONS}")
                return INITIAL_OPTIONS

        @callback(  # type: ignore[misc]
            Output("aggdistplotter-table", "rowData"),
            Output("aggdistplotter-table", "columnDefs"),
            Input("aggdistplotter-refresh", "n_clicks"),
            Input("aggdistplotter-radioitems", "value"),
            Input("aggdistplotter-rullvar-dd", "value"),
            State("var-valgt_tabell", "value"),
            *dynamic_states,
        )
        def agg_table(
            refresh: int | None,
            radio_value: str,
            rullerende_var: str,
            tabell: str,
            *dynamic_states: Any,
        ) -> tuple[
            list[dict[str, Any]], list[dict[str, str | bool]]
        ]:  # TODO replace Any
            logger.debug(
                f"Args:\nrefresh: {refresh}\nradio_value: {radio_value}\nrullerende_var: {rullerende_var}\ntabell: {tabell}\ndynamic_states: {dynamic_states}"
            )
            skjema = radio_value
            if not refresh:
                logger.debug("Preventing update")
                raise PreventUpdate
            else:
                partition_args = dict(
                    zip(self.time_units, dynamic_states, strict=False)
                )
                partition_select_no_skjema = create_partition_select(
                    desired_partitions=self.time_units, skjema=None, **partition_args
                )
                updated_partition_select = self.update_partition_select(
                    partition_select_no_skjema, rullerende_var
                )
                column_name_expr_s = SQL_COLUMN_CONCAT.join(
                    [f"s.{unit}" for unit in self.time_units]
                )
                column_name_expr_t2 = SQL_COLUMN_CONCAT.join(
                    [f"t2.{unit}" for unit in self.time_units]
                )
                column_name_expr_d = SQL_COLUMN_CONCAT.join(
                    [f"d.{unit}" for unit in self.time_units]
                )

                group_by_clause = ", ".join([f"s.{unit}" for unit in self.time_units])

                if skjema != "all":
                    where_query_add = f"AND s.skjema = '{skjema}'"
                else:
                    where_query_add = ""

                query = f"""
                    SELECT
                        s.variabel,
                        {column_name_expr_s} AS time_combination,
                        SUM(CAST(s.verdi AS NUMERIC)) AS verdi
                    FROM {tabell} AS s
                    JOIN (
                        SELECT
                            {column_name_expr_t2} AS time_combination,
                            t2.ident,
                            t2.refnr,
                            t2.dato_mottatt
                        FROM
                            skjemamottak AS t2
                        WHERE aktiv = True
                        QUALIFY
                            ROW_NUMBER() OVER (
                                PARTITION BY {column_name_expr_t2}, t2.ident
                                ORDER BY t2.dato_mottatt DESC
                            ) = 1
                    ) AS mottak_subquery
                        ON {column_name_expr_s} = mottak_subquery.time_combination
                        AND s.ident = mottak_subquery.ident
                        AND s.refnr = mottak_subquery.refnr
                    JOIN (
                        SELECT
                            d.variabel,
                            {column_name_expr_d} AS time_combination,
                            d.radnr,
                            d.datatype
                        FROM datatyper AS d
                    ) AS datatype_subquery
                        ON s.variabel = datatype_subquery.variabel
                        AND {column_name_expr_s} = datatype_subquery.time_combination
                    WHERE datatype_subquery.datatype = 'int' {where_query_add}
                    GROUP BY
                        s.variabel,
                        datatype_subquery.radnr,
                        {group_by_clause}
                    ORDER BY datatype_subquery.radnr;
                """

                df = self.conn.query(
                    query,
                    partition_select={
                        tabell: updated_partition_select,
                        "datatyper": updated_partition_select,
                    },
                )

                df_wide = df.pivot(
                    index="variabel", columns="time_combination", values="verdi"
                ).reset_index()

                df_wide = df_wide.rename(
                    columns={
                        col: f"verdi_{col}" if col != "variabel" else col
                        for col in df_wide.columns
                    }
                )

                df_wide.columns.name = None

                def extract_numeric_sum(
                    col_name: str,
                ) -> int:  # TODO should return int | float?
                    numbers = list(map(int, re.findall(r"\d+", col_name)))
                    return sum(numbers) if numbers else 0

                time_columns_sorted = sorted(
                    [col for col in df_wide.columns if col.startswith("verdi_")],
                    key=extract_numeric_sum,
                )

                if len(time_columns_sorted) >= 2:
                    latest_col = max(time_columns_sorted, key=extract_numeric_sum)
                    prev_col = min(time_columns_sorted, key=extract_numeric_sum)
                    df_wide["diff"] = df_wide[latest_col] - df_wide[prev_col]
                    df_wide["pdiff"] = (df_wide["diff"] / df_wide[prev_col]) * 100
                    df_wide["pdiff"] = df_wide["pdiff"].round(2).astype(str) + " %"
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                    }
                    for col in df_wide.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
                return df_wide.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output("aggdistplotter-graph", "figure"),
            Input("aggdistplotter-table", "selectedRows"),
            Input("aggdistplotter-radioitems", "value"),
            Input("aggdistplotter-graph-type", "value"),
            State("var-valgt_tabell", "value"),
            *dynamic_states,
        )
        def agg_graph1(
            current_row: list[dict[str, int | float | str]],
            skjema: str,
            graph_type: str,
            tabell: str,
            *args: Any,
        ) -> go.Figure:  # TODO replace Any
            logger.debug(
                f"Args:\ncurrent_row: {current_row}\nskjema: {skjema}\n graph_type: {graph_type}\n tabell: {tabell}\n args: {args}"
            )
            if (
                current_row is None
                or skjema is None
                or graph_type is None
                or tabell is None
            ):
                raise PreventUpdate
            logger.debug(
                f"Creating graph for skjema: {skjema}, graph_type: {graph_type}, tabell: {tabell}"
            )
            partition_args = dict(
                zip(self.time_units, [int(x) for x in args], strict=False)
            )
            logger.debug(f"Partition args: {partition_args}")

            if skjema == "all":
                partition_select = create_partition_select(
                    desired_partitions=self.time_units, skjema=None, **partition_args
                )
            else:
                partition_select = create_partition_select(
                    desired_partitions=self.time_units, skjema=skjema, **partition_args
                )

            variabel = current_row[0]["variabel"]

            df = self.conn.query(
                f"""SELECT t1.aar, t1.ident, t1.variabel, t1.verdi
                FROM {tabell} as t1
                JOIN (
                    SELECT
                        t2.ident,
                        t2.refnr,
                        MAX(t2.dato_mottatt) AS newest_dato_mottatt
                    FROM
                        skjemamottak AS t2
                    GROUP BY
                        t2.ident,
                        t2.refnr
                ) AS subquery ON
                    t1.ident = subquery.ident
                    AND t1.refnr = subquery.refnr
                WHERE variabel = '{variabel}' AND verdi IS NOT NULL AND verdi != 0
                """,
                partition_select=partition_select,
            )

            df["verdi"] = df["verdi"].astype(int)

            top5_df = df.nlargest(5, "verdi")

            if graph_type == "box":
                fig = px.box(
                    df,
                    x="variabel",
                    y="verdi",
                    hover_data=["ident", "verdi"],
                    points="all",
                    title=f"📦 Boksplott for {variabel}, {partition_select!s}.",
                    template="plotly_dark",
                )
            elif graph_type == "fiolin":
                fig = px.violin(
                    df,
                    x="variabel",
                    y="verdi",
                    hover_data=["ident", "verdi"],
                    box=True,
                    points="all",
                    title=f"🎻 Fiolinplott for {variabel}, {partition_select!s}.",
                    template="plotly_dark",
                )
            elif graph_type == "bidrag":
                agg_df = df.groupby("ident", as_index=False)["verdi"].sum()
                agg_df["verdi"] = (agg_df["verdi"] / agg_df["verdi"].sum() * 100).round(
                    2
                )
                agg_df = agg_df.sort_values("verdi", ascending=False).head(10)

                fig = px.bar(
                    agg_df,
                    x="verdi",
                    y="ident",
                    orientation="h",
                    title=f"🥇 Bidragsanalyse - % av total verdi ({variabel})",
                    template="plotly_dark",
                    labels={"verdi": "%"},
                    custom_data=["ident"],
                )

                fig.update_layout(yaxis={"categoryorder": "total ascending"})

            else:
                fig = go.Figure()

            if graph_type in ["box", "fiolin"]:
                fig.add_scatter(
                    x=[variabel] * len(top5_df),
                    y=top5_df["verdi"],
                    mode="markers",
                    marker=dict(
                        size=13,
                        color="#00CC96",
                        symbol="diamond",
                        line=dict(width=1, color="white"),
                    ),
                    name="De fem største",
                    hovertext=top5_df["ident"],
                    hoverinfo="text+y",
                    customdata=top5_df[["ident"]].values,
                )
            return fig

        @callback(  # type: ignore[misc]
            Output("var-ident", "value", allow_duplicate=True),
            Input("aggdistplotter-graph", "clickData"),
            prevent_initial_call=True,
        )
        def output_to_variabelvelger(clickdata: dict[str, list[dict[str, Any]]]) -> str:
            logger.debug(clickdata)
            if clickdata:
                ident = clickdata["points"][0]["customdata"][0]
                return str(ident)
            else:
                raise PreventUpdate


class AggDistPlotterTab(TabImplementation, AggDistPlotter):
    """AggDistPlotterTab is an implementation of the AggDistPlotter module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the AggDistPlotterTab class."""
        AggDistPlotter.__init__(self, time_units=time_units, conn=conn)
        TabImplementation.__init__(self)


class AggDistPlotterWindow(WindowImplementation, AggDistPlotter):
    """AggDistPlotterWindow is an implementation of the AggDistPlotter module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the AggDistPlotterWindow class."""
        AggDistPlotter.__init__(self, time_units=time_units, conn=conn)
        WindowImplementation.__init__(self)
