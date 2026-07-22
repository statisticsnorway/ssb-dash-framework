"""VL visualisation module."""

from functools import lru_cache
from typing import Any
from typing import ClassVar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import html

from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator


VL_VISUALISATIONS = {
    "trend-single": "Trendanalyse – én variabel",
    "trend-multi": "Trendanalyse – flere variabler",
    "trend-industries": "Trendanalyse – flere næringer",
    "trend-enterprise": "Trendanalyse – enkeltforetak",
    "change-share": "Prosentandeler av endringene",
    "noku-table": "NØKU-tabell",
    "large-changes": "Store endringer",
    "negative-nopost": "Negative NO-poster",
    "nr-controls": "NR-kontroller",
    "opposite-direction": "Motsatte bevegelser",
    "breakdown": "Sammensatte variabler",
    "moms": "Mot MOMS",
    "movement": "Tilgang og avgang",
    "method-analysis": "Metodeanalyse",
}


class VLModule:
    """Container for VL visualisations."""

    _id_number: ClassVar[int] = 0

    def __init__(
        self,
        base_path: str = (
            "gs://ssb-strukt-naering-data-produkt-prod/"
            "naringer/klargjorte-data/vl-data"
        ),
    ) -> None:
        self.module_number = VLModule._id_number
        VLModule._id_number += 1

        self.module_name = self.__class__.__name__
        self.icon = "📊"
        self.label = "VL"

        self.base_path = base_path.rstrip("/")

        self.data_version_id = f"vl-data-version-{self.module_number}"
        self.visualisation_id = f"vl-visualisation-{self.module_number}"
        self.naring_id = f"vl-naring-{self.module_number}"
        self.variable_id = f"vl-variable-{self.module_number}"
        self.multi_variable_id = f"vl-multi-variable-{self.module_number}"
        self.single_variable_container_id = (
            f"vl-single-variable-container-{self.module_number}"
        )
        self.multi_variable_container_id = (
            f"vl-multi-variable-container-{self.module_number}"
        )
        self.graph_title_id = f"vl-graph-title-{self.module_number}"
        self.graph_description_id = f"vl-graph-description-{self.module_number}"
        self.graph_id = f"vl-graph-{self.module_number}"
        self.status_id = f"vl-status-{self.module_number}"
        self.graph_section_id = f"vl-graph-section-{self.module_number}"

        self.module_layout = self._create_layout()

        self.module_callbacks()
        module_validator(self)

    def _create_layout(self) -> html.Div:
        """Create the main VL layout."""
        return html.Div(
            className="vl-module",
            style={
                "width": "100%",
                "maxWidth": "none",
            },
            children=[
                html.Div(
                    style={
                        "maxWidth": "900px",
                    },
                    children=[
                        html.H1("VL-visualiseringer"),
                        html.P("Velg datagrunnlag og visualisering."),
                        html.Div(
                            children=[
                                html.Label("Datagrunnlag"),
                                dcc.RadioItems(
                                    id=self.data_version_id,
                                    className="ssb-radio-buttons",
                                    options=[
                                        {
                                            "label": "Konsolidert",
                                            "value": "consolidated",
                                        },
                                        {
                                            "label": "Ukonsolidert",
                                            "value": "unconsolidated",
                                        },
                                    ],
                                    value="consolidated",
                                ),
                            ],
                        ),
                        html.Div(
                            children=[
                                html.Label("Visualisering"),
                                dcc.Dropdown(
                                    id=self.visualisation_id,
                                    className="ssb-dropdown",
                                    options=[
                                        {
                                            "label": label,
                                            "value": value,
                                        }
                                        for value, label in VL_VISUALISATIONS.items()
                                    ],
                                    value="trend-single",
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Hr(),
                    ],
                ),
                html.Div(
                    id=self.graph_section_id,
                    style={
                        "width": "100%",
                        "maxWidth": "none",
                    },
                    children=[
                        html.Div(
                            style={
                                "maxWidth": "900px",
                            },
                            children=[
                                html.H2(
                                    id=self.graph_title_id,
                                    children="Trendanalyse – én variabel",
                                ),
                                html.P(
                                    id=self.graph_description_id,
                                    children=(
                                        "Viser utviklingen over tid sammen med forventet "
                                        "variasjonsområde basert på historiske endringer."
                                    ),
                                ),
                                html.Div(
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": (
                                            "minmax(220px, 1fr) "
                                            "minmax(220px, 1fr)"
                                        ),
                                        "gap": "16px",
                                        "marginBottom": "16px",
                                    },
                                    children=[
                                        html.Div(
                                            children=[
                                                html.Label("Næring"),
                                                dcc.Dropdown(
                                                    id=self.naring_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    id=self.single_variable_container_id,
                                                    children=[
                                                        html.Label("Variabel"),
                                                        dcc.Dropdown(
                                                            id=self.variable_id,
                                                            className="ssb-dropdown",
                                                            options=[],
                                                            clearable=False,
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    id=self.multi_variable_container_id,
                                                    style={"display": "none"},
                                                    children=[
                                                        html.Label("Variabler"),
                                                        dcc.Dropdown(
                                                            id=self.multi_variable_id,
                                                            className="ssb-dropdown",
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            clearable=True,
                                                        ),
                                                    ],
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                                html.Div(id=self.status_id),
                            ],
                        ),
                        dcc.Loading(
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id=self.graph_id,
                                    figure=go.Figure(),
                                    config={
                                        "displaylogo": False,
                                        "responsive": True,
                                        "scrollZoom": True,
                                    },
                                    style={
                                        "width": "100%",
                                        "height": "75vh",
                                        "minHeight": "700px",
                                    },
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )

    def _parquet_path(self, data_version: str) -> str:
        return (
            f"{self.base_path}/{data_version}/"
            "df_agg_naring4.parquet"
        )

    @staticmethod
    @lru_cache(maxsize=4)
    def _read_data(parquet_path: str) -> pd.DataFrame:
        """Read and cache the aggregated VL dataset."""
        df = pd.read_parquet(parquet_path)

        if "year" not in df.columns:
            raise ValueError("df_agg_naring4 mangler kolonnen 'year'.")

        if "naring_4" not in df.columns:
            raise ValueError(
                "df_agg_naring4 mangler kolonnen 'naring_4'."
            )

        df = df.copy()
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["naring_4"] = df["naring_4"].astype(str)

        return df

    @staticmethod
    def _empty_figure(message: str) -> go.Figure:
        fig = go.Figure()

        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"size": 16},
        )

        fig.update_layout(
            template="plotly_white",
            xaxis={"visible": False},
            yaxis={"visible": False},
        )

        return fig

    @staticmethod
    def _create_trend_figure(
        df: pd.DataFrame,
        naring: str,
        variable: str,
    ) -> go.Figure:
        sub = df.loc[
            df["naring_4"].astype(str) == str(naring),
            ["year", variable],
        ].copy()

        sub = sub.dropna(subset=["year"])
        sub = sub.sort_values("year").reset_index(drop=True)

        sub[variable] = pd.to_numeric(
            sub[variable],
            errors="coerce",
        )

        values = sub[variable]

        # Same principle as the notebook function:
        # bounds for year t are centred on the previous year's actual value.
        annual_change = values.diff()
        lagged_change = annual_change.shift(1)
        rolling_std = lagged_change.rolling(
            window=5,
            min_periods=2,
        ).std()

        centre = values.shift(1)

        sub["upper"] = centre + 2.5 * rolling_std
        sub["lower"] = centre - 2.5 * rolling_std
        sub["breach"] = (
            rolling_std.notna()
            & (
                (values > sub["upper"])
                | (values < sub["lower"])
            )
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub["upper"],
                mode="lines",
                line={"width": 0},
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub["lower"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(120, 120, 120, 0.18)",
                name="Forventet variasjonsområde",
                hovertemplate=(
                    "År: %{x}<br>"
                    "Nedre grense: %{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub[variable],
                mode="lines+markers",
                name=variable,
                line={"width": 3},
                marker={"size": 8},
                hovertemplate=(
                    "År: %{x}<br>"
                    f"{variable}: " + "%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )

        breaches = sub.loc[sub["breach"]]

        if not breaches.empty:
            fig.add_trace(
                go.Scatter(
                    x=breaches["year"],
                    y=breaches[variable],
                    mode="markers",
                    name="Utenfor forventet område",
                    marker={
                        "size": 13,
                        "symbol": "diamond",
                        "color": "red",
                    },
                    hovertemplate=(
                        "År: %{x}<br>"
                        f"{variable}: " + "%{y:,.0f}"
                        "<extra>Avvik</extra>"
                    ),
                )
            )

        fig.update_layout(
            autosize=True,
            width=None,
            height=None,
            title=f"{variable} – næring {naring}",
            xaxis_title="År",
            yaxis_title=variable,
            template="plotly_white",
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0,
            },
            margin={
                "l": 70,
                "r": 40,
                "t": 100,
                "b": 70,
            },
        )

        fig.update_xaxes(dtick=1)

        return fig

    @staticmethod
    def _create_multi_trend_figure(
        df: pd.DataFrame,
        naring: str,
        variables: list[str],
    ) -> go.Figure:
        """Create a time-series figure containing multiple variables."""
        selected_columns = ["year", *variables]

        sub = df.loc[
            df["naring_4"].astype(str) == str(naring),
            selected_columns,
        ].copy()

        sub = sub.dropna(subset=["year"])
        sub = sub.sort_values("year").reset_index(drop=True)

        fig = go.Figure()

        for variable in variables:
            sub[variable] = pd.to_numeric(
                sub[variable],
                errors="coerce",
            )

            fig.add_trace(
                go.Scatter(
                    x=sub["year"],
                    y=sub[variable],
                    mode="lines+markers",
                    name=variable,
                    line={"width": 3},
                    marker={"size": 7},
                    hovertemplate=(
                        "År: %{x}<br>"
                        f"{variable}: "
                        "%{y:,.0f}"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            autosize=True,
            width=None,
            height=None,
            title=f"Flere variabler – næring {naring}",
            xaxis_title="År",
            yaxis_title="Verdi",
            template="plotly_white",
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0,
            },
            margin={
                "l": 70,
                "r": 40,
                "t": 100,
                "b": 70,
            },
        )

        fig.update_xaxes(dtick=1)

        return fig
    def module_callbacks(self) -> None:
        """Register VL callbacks."""

        @callback(
            Output(self.naring_id, "options"),
            Output(self.naring_id, "value"),
            Output(self.variable_id, "options"),
            Output(self.variable_id, "value"),
            Output(self.multi_variable_id, "options"),
            Output(self.multi_variable_id, "value"),
            Output(self.status_id, "children"),
            Input(self.data_version_id, "value"),
        )
        def load_dropdown_options(
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
            list[dict[str, str]],
            str | None,
            list[dict[str, str]],
            list[str],
            Any,
        ]:
            try:
                parquet_path = self._parquet_path(data_version)
                df = self._read_data(parquet_path)

                naring_values = sorted(
                    df["naring_4"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                numeric_columns = (
                    df.select_dtypes(include=[np.number])
                    .columns
                    .tolist()
                )

                variable_values = sorted(
                    column
                    for column in numeric_columns
                    if column != "year"
                )

                naring_options = [
                    {"label": value, "value": value}
                    for value in naring_values
                ]

                variable_options = [
                    {"label": value, "value": value}
                    for value in variable_values
                ]

                naring_value = (
                    naring_values[0]
                    if naring_values
                    else None
                )

                variable_value = (
                    variable_values[0]
                    if variable_values
                    else None
                )

                multi_variable_value = variable_values[:3]

                status = html.P(
                    [
                        "Lest fra ",
                        html.Code(parquet_path),
                    ],
                    style={"fontSize": "12px"},
                )

                return (
                    naring_options,
                    naring_value,
                    variable_options,
                    variable_value,
                    variable_options,
                    multi_variable_value,
                    status,
                )

            except Exception as error:
                return (
                    [],
                    None,
                    [],
                    None,
                    [],
                    [],
                    html.Div(
                        f"Kunne ikke lese data: {error}",
                        className="alert alert-danger",
                    ),
                )

        @callback(
            Output(self.graph_title_id, "children"),
            Output(self.graph_description_id, "children"),
            Output(self.single_variable_container_id, "style"),
            Output(self.multi_variable_container_id, "style"),
            Input(self.visualisation_id, "value"),
        )
        def update_visualisation_controls(
            visualisation: str,
        ) -> tuple[str, str, dict[str, str], dict[str, str]]:
            if visualisation == "trend-multi":
                return (
                    "Trendanalyse – flere variabler",
                    (
                        "Sammenligner utviklingen i flere valgte variabler "
                        "for samme næring over tid."
                    ),
                    {"display": "none"},
                    {"display": "block"},
                )

            return (
                "Trendanalyse – én variabel",
                (
                    "Viser utviklingen over tid sammen med forventet "
                    "variasjonsområde basert på historiske endringer."
                ),
                {"display": "block"},
                {"display": "none"},
            )

        @callback(
            Output(self.graph_id, "figure"),
            Output(self.graph_section_id, "style"),
            Input(self.visualisation_id, "value"),
            Input(self.data_version_id, "value"),
            Input(self.naring_id, "value"),
            Input(self.variable_id, "value"),
            Input(self.multi_variable_id, "value"),
        )
        def update_graph(
            visualisation: str,
            data_version: str,
            naring: str | None,
            variable: str | None,
            multi_variables: list[str] | None,
        ) -> tuple[go.Figure, dict[str, str]]:
            supported_visualisations = {
                "trend-single",
                "trend-multi",
            }

            if visualisation not in supported_visualisations:
                label = VL_VISUALISATIONS.get(
                    visualisation,
                    visualisation,
                )

                return (
                    self._empty_figure(
                        f"{label} blir lagt til i neste steg."
                    ),
                    {
                        "display": "block",
                        "width": "100%",
                        "maxWidth": "none",
                    },
                )

            if not naring:
                return (
                    self._empty_figure("Velg næring."),
                    {
                        "display": "block",
                        "width": "100%",
                        "maxWidth": "none",
                    },
                )

            try:
                parquet_path = self._parquet_path(data_version)
                df = self._read_data(parquet_path)

                if visualisation == "trend-multi":
                    if not multi_variables:
                        figure = self._empty_figure(
                            "Velg minst én variabel."
                        )
                    else:
                        figure = self._create_multi_trend_figure(
                            df=df,
                            naring=naring,
                            variables=multi_variables,
                        )

                else:
                    if not variable:
                        figure = self._empty_figure(
                            "Velg en variabel."
                        )
                    else:
                        figure = self._create_trend_figure(
                            df=df,
                            naring=naring,
                            variable=variable,
                        )

                return (
                    figure,
                    {
                        "display": "block",
                        "width": "100%",
                        "maxWidth": "none",
                    },
                )

            except Exception as error:
                return (
                    self._empty_figure(
                        f"Kunne ikke lage figur: {error}"
                    ),
                    {
                        "display": "block",
                        "width": "100%",
                        "maxWidth": "none",
                    },
                )


class VLModuleTab(TabImplementation, VLModule):
    """VL module displayed as an application tab."""

    def __init__(
        self,
        base_path: str = (
            "gs://ssb-strukt-naering-data-produkt-prod/"
            "naringer/klargjorte-data/vl-data"
        ),
    ) -> None:
        VLModule.__init__(
            self,
            base_path=base_path,
        )
        TabImplementation.__init__(self)


class VLModuleWindow(WindowImplementation, VLModule):
    """VL module displayed as a sidebar window."""

    def __init__(
        self,
        base_path: str = (
            "gs://ssb-strukt-naering-data-produkt-prod/"
            "naringer/klargjorte-data/vl-data"
        ),
    ) -> None:
        VLModule.__init__(
            self,
            base_path=base_path,
        )
        WindowImplementation.__init__(self)