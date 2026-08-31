# pyright: reportInvalidTypeForm=false
# pyright: reportCallIssue=false
from itertools import cycle
import uuid

import dash_ag_grid as dag
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import callback
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash import Patch
from dash.exceptions import PreventUpdate
from ....utils import EditorSettings
from ....meta import FetcherMeta
from .......setup.variableselector import VariableSelector
from .......utils.config_tools.set_variables import (
    SelectedTimeUnit,
    TimeUnit,
    get_ident,
    get_refnr,
    get_time_units,
)

GRAPH_COLORS = [
    "rgba(26, 157, 73, 255)",
    "rgba(7, 87, 69, 255)",
    "rgba(29, 157, 226, 255)",
    "rgba(15, 32, 128, 255)",
    "rgba(199, 136, 0, 255)",
    "rgba(71, 31, 0, 255)",
    "rgba(199, 117, 167, 255)",
    "rgba(163, 19, 108, 255)",
    "rgba(144, 144, 144, 255)",
]


class TimeseriesAio(html.Div):
    def __init__(
        self,
        variables: str | list[str],
        num_periods: int,
        settings: EditorSettings,
        fetcher: FetcherMeta,
        width: int,
        _id: str | None = None,
        **kwargs,
    ):
        if _id is None:
            internal_id = str(uuid.uuid4())
        else:
            internal_id = _id

        selector = VariableSelector(
            [get_refnr(), get_ident(), get_time_units().name], []
        )

        GRAPH_CYCLE = cycle(GRAPH_COLORS)

        initial_fig = go.Figure(data=[])
        initial_fig.update_layout(
            margin={
                "l": 0,
                "r": 0,
                "t": 0,
                "b": 0,
            },  # Sets all padding/margins to 0 pixels
            xaxis={"automargin": True},
            yaxis={"automargin": True},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
            plot_bgcolor="rgba(0,0,0,0)",  # Color inside the plot axes
            paper_bgcolor="rgba(0,0,0,0)",  # Color of the outer canvas
        )

        if isinstance(variables, str):
            variables = [variables]
        else:
            variables = variables

        column_defs = [{"field": settings.period_col}]
        for variable in variables:
            column_defs.append({"field": variable})

        children = [
            dbc.Label("Table view or graph view"),
            dbc.Checklist(
                options=[
                    {"label": "", "value": 1},
                ],
                value=[1],
                id=f"switch-{internal_id}",
                switch=True,
            ),
            html.Div(
                children=[
                    html.Div(
                        id=f"graph-container-{internal_id}",
                        style={"display": "block"},
                        children=[
                            dcc.Graph(id=f"graph-{internal_id}", figure=initial_fig)
                        ],
                    ),
                    html.Div(
                        id=f"table-container-{internal_id}",
                        style={"display": "none"},
                        children=[
                            dag.AgGrid(
                                id=f"table-{internal_id}",
                                columnDefs=column_defs,
                            )
                        ],
                    ),
                ]
            ),
        ]
        super().__init__(style={"width": width}, children=children, **kwargs)

        @callback(
            Output(f"graph-{internal_id}", "figure"),
            Output(f"table-{internal_id}", "rowData"),
            inputs={
                "refnr": selector.get_input(get_refnr()),
                "ident": selector.get_input(get_ident()),
                "period": selector.get_input(get_time_units().name),
            },
        )
        def get_timeseries_data(refnr, ident, period):
            if not refnr or not ident or not period:
                raise PreventUpdate

            selected_period: SelectedTimeUnit = TimeUnit.parse(get_time_units(), period)

            periods_to_get = [selected_period.to_str()]
            for i in range(1, num_periods + 1):
                prev_period = selected_period.subtract(i)
                periods_to_get.append(prev_period.to_str())

            timeseries = fetcher.get_timeseries(settings, variables, refnr, ident, periods_to_get)

            def sort_timeseries(period, frequency):
                return TimeUnit.parse(frequency, period).dt
            
            sorted_series = sorted(
                timeseries,
                key=lambda x: sort_timeseries(
                    x[settings.period_col], selected_period.timeunit
                ),
            )

            patch_obj = Patch()
            if isinstance(variables, str):
                temp_variables = [variables]
            else:
                temp_variables = variables

            patch_obj["data"] = []
            x_axis = [item[settings.period_col] for item in sorted_series]
            for i in temp_variables:
                y_axis = []
                for item in sorted_series:
                    if isinstance(item[i], str):
                        y_axis.append(int(item[i]))
                    else:
                        y_axis.append(item[i])

                patch_obj["data"].append(
                    go.Scatter(
                        x=x_axis,
                        y=y_axis,
                        mode="lines+markers",
                        name=i,
                        line=dict(color=next(GRAPH_CYCLE), width=4),
                    )
                )

            return patch_obj, sorted_series

        @callback(
            Output(f"graph-container-{internal_id}", "style"),
            Output(f"table-container-{internal_id}", "style"),
            Input(f"switch-{internal_id}", "value"),
        )
        def toogle_graph(value):
            if value:
                return {"display": "block"}, {"display": "none"}
            else:
                return {"display": "none"}, {"display": "block"}
