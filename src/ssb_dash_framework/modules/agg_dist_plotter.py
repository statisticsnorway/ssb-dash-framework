import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import ibis
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
from ..utils import active_no_duplicates_refnr_list
from ..utils import get_connection
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

    Note:
        Current implementation is very locked into a specific data structure.
    """

    # TODO: Loosen constraints on datastructure.

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the callbacks.
            "ident",
            "valgt_tabell",
            "altinnskjema",
        ]
    )

    def __init__(
        self, time_units: list[str], main_table_name="skjemadata_hoved"
    ) -> None:
        """Initializes the AggDistPlotter.

        Args:
            time_units: Your time variables used in the variable selector. Example year, quarter, month, etc.
            conn: A connection object to a database. It must have a .query method that can handle SQL queries.
                Currently designed with eimerdb in mind.
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        #        if not isinstance(conn, EimerDBInstance) and conn.__class__.__name__ != "Backend":
        #            raise TypeError("Argument 'conn' must be an 'EimerDBInstance' or Ibis backend. Received: {type(conn)}")
        self.module_number = AggDistPlotter._id_number
        self.module_name = self.__class__.__name__
        AggDistPlotter._id_number += 1

        self.icon = "🌌"
        self.label = "Aggregering"

        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        print("TIME UNITS ", self.time_units)
        self.main_table_name = main_table_name

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in AggDistPlotter._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
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
                                className="ag-theme-alpine header-style-on-filter",
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
            A Dash HTML Div component representing the layout of the module.
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
        dynamic_states = self.variableselector.get_all_inputs()

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
            if not isinstance(tabell, str) or tabell == "":
                raise ValueError(
                    f"Trying to run query with no value for 'tabell'. Received value: '{tabell}'"
                )

            partition_args = dict(zip(self.time_units, dynamic_states, strict=False))
            partition_select_no_skjema = create_partition_select(
                desired_partitions=self.time_units, skjema=None, **partition_args
            )
            updated_partition_select = self.update_partition_select(
                partition_select_no_skjema, rullerende_var
            )
            time_vars = updated_partition_select.get(rullerende_var)
            if not isinstance(time_vars, list):
                raise ValueError(
                    f"'time_vars' must be list, not '{type(time_vars)}': {time_vars}"
                )
            if time_vars[0] is None or time_vars[1] is None:
                raise ValueError(
                    "'time_vars' must have two values and they cannot be None."
                )
            _t_0 = str(time_vars[0])
            _t_1 = str(time_vars[1])

            with get_connection(  # necessary_tables and partition_select are used for eimerdb connection.
                necessary_tables=["skjemamottak", "datatyper", self.main_table_name],
                partition_select=updated_partition_select,
            ) as conn:
                skjemadata_tbl = conn.table(self.main_table_name)
                datatyper_tbl = conn.table("datatyper")

                relevant_refnr = active_no_duplicates_refnr_list(conn, skjema)

                skjemadata_tbl = (
                    skjemadata_tbl.filter(skjemadata_tbl.refnr.isin(relevant_refnr))
                    .join(
                        datatyper_tbl.select("variabel", "datatype"),
                        ["variabel"],
                        how="inner",
                    )
                    .filter(datatyper_tbl.datatype.isin(["number", "int", "float"]))
                    .cast({"verdi": "float", rullerende_var: "str"})
                    .cast({"verdi": "int"})
                    .mutate(verdi=lambda t: t["verdi"].round(0))
                    .pivot_wider(
                        id_cols=["variabel"],
                        names_from=rullerende_var,  # TODO: Tidsenhet
                        values_from="verdi",
                        values_agg="sum",
                    )
                )
                if _t_1 in skjemadata_tbl.columns:
                    logger.debug("Calculating diff from last year.")
                    skjemadata_tbl.mutate(
                        diff=lambda t: t[_t_0] - t[_t_1],
                        pdiff=lambda t: (
                            (t[_t_0].fill_null(0) - t[_t_1].fill_null(0))
                            / t[_t_1].fill_null(1)
                            * 100
                        ).round(2),
                    )
                else:
                    logger.debug(
                        f"Didn't find previous period value, no diff calculated. Columns in dataset: {skjemadata_tbl.columns}"
                    )

                pandas_table = skjemadata_tbl.to_pandas()
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                    }
                    for col in pandas_table.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
                return pandas_table.to_dict("records"), columns

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
            variabel = current_row[0]["variabel"]

            partition_args = dict(
                zip(self.time_units, [int(x) for x in args], strict=False)
            )
            logger.debug(f"Partition args: {partition_args}")
            if skjema == "all":
                partition_select = create_partition_select(
                    desired_partitions=self.time_units,
                    skjema=None,
                    **partition_args,
                )
            else:
                partition_select = create_partition_select(
                    desired_partitions=self.time_units,
                    skjema=skjema,
                    **partition_args,
                )

            with get_connection(
                necessary_tables=["skjemamottak", self.main_table_name],
                partition_select=partition_select,
            ) as conn:
                skjemamottak_tbl = conn.table("skjemamottak")
                skjemadata_tbl = conn.table(self.main_table_name)

                skjemamottak_tbl = (  # Get relevant refnr values from skjemamottak
                    skjemamottak_tbl.filter(skjemamottak_tbl.aktiv)
                    .order_by(ibis.desc(skjemamottak_tbl.dato_mottatt))
                    .distinct(on=[*self.time_units, "ident"], keep="first")
                )

                relevant_refnr = active_no_duplicates_refnr_list(conn, skjema)

                skjemadata_tbl = (
                    skjemadata_tbl.filter(
                        [
                            skjemadata_tbl.refnr.isin(relevant_refnr),
                            skjemadata_tbl.variabel == variabel,
                            skjemadata_tbl.verdi.notnull(),
                        ]
                    )
                    .cast({"verdi": "float"})
                    .cast({"verdi": "int"})
                )

                df = skjemadata_tbl.to_pandas()

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
                    agg_df["verdi"] = (
                        agg_df["verdi"] / agg_df["verdi"].sum() * 100
                    ).round(2)
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

    def __init__(
        self, time_units: list[str], main_table_name="skjemadata_hoved"
    ) -> None:
        """Initializes the AggDistPlotterTab class."""
        AggDistPlotter.__init__(
            self, time_units=time_units, main_table_name=main_table_name
        )
        TabImplementation.__init__(self)


class AggDistPlotterWindow(WindowImplementation, AggDistPlotter):
    """AggDistPlotterWindow is an implementation of the AggDistPlotter module as a tab in a Dash application."""

    def __init__(
        self, time_units: list[str], main_table_name="skjemadata_hoved"
    ) -> None:
        """Initializes the AggDistPlotterWindow class."""
        AggDistPlotter.__init__(
            self, time_units=time_units, main_table_name=main_table_name
        )
        WindowImplementation.__init__(self)
