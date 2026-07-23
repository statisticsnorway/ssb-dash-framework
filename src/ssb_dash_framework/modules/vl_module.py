"""VL visualisation module."""

from functools import lru_cache
from collections.abc import Callable
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
from dash import no_update

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
        file_path_resolver: Callable[[str, str], str],
    ) -> None:
        self.module_number = VLModule._id_number
        VLModule._id_number += 1

        self.module_name = self.__class__.__name__
        self.icon = "📊"
        self.label = "VL"

        self.file_path_resolver = file_path_resolver

        self.data_version_id = f"vl-data-version-{self.module_number}"
        self.visualisation_id = f"vl-visualisation-{self.module_number}"
        self.naring_id = f"vl-naring-{self.module_number}"
        self.variable_id = f"vl-variable-{self.module_number}"
        self.multi_variable_id = f"vl-multi-variable-{self.module_number}"
        self.multi_naring_id = f"vl-multi-naring-{self.module_number}"
        self.enterprise_id = f"vl-enterprise-{self.module_number}"
        self.enterprise_name_search_id = (
            f"vl-enterprise-name-search-{self.module_number}"
        )
        self.change_year_id = f"vl-change-year-{self.module_number}"
        self.change_top_n_id = f"vl-change-top-n-{self.module_number}"
        self.change_controls_container_id = (
            f"vl-change-controls-container-{self.module_number}"
        )
        self.single_variable_container_id = (
            f"vl-single-variable-container-{self.module_number}"
        )
        self.multi_variable_container_id = (
            f"vl-multi-variable-container-{self.module_number}"
        )
        self.enterprise_container_id = (
            f"vl-enterprise-container-{self.module_number}"
        )
        self.single_naring_container_id = (
            f"vl-single-naring-container-{self.module_number}"
        )
        self.multi_naring_container_id = (
            f"vl-multi-naring-container-{self.module_number}"
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
                        html.P(
                            "Velg datagrunnlag og visualisering."
                        ),
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
                                        for value, label
                                        in VL_VISUALISATIONS.items()
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
                                    children=(
                                        "Trendanalyse – én variabel"
                                    ),
                                ),
                                html.P(
                                    id=self.graph_description_id,
                                    children=(
                                        "Viser utviklingen over tid "
                                        "sammen med forventet "
                                        "variasjonsområde basert på "
                                        "historiske endringer."
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
                                                html.Div(
                                                    id=(
                                                        self
                                                        .single_naring_container_id
                                                    ),
                                                    children=[
                                                        html.Label(
                                                            "Næring"
                                                        ),
                                                        dcc.Dropdown(
                                                            id=(
                                                                self
                                                                .naring_id
                                                            ),
                                                            className=(
                                                                "ssb-dropdown"
                                                            ),
                                                            options=[],
                                                            clearable=False,
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    id=(
                                                        self
                                                        .multi_naring_container_id
                                                    ),
                                                    style={
                                                        "display": "none"
                                                    },
                                                    children=[
                                                        html.Label(
                                                            "Næringer"
                                                        ),
                                                        dcc.Dropdown(
                                                            id=(
                                                                self
                                                                .multi_naring_id
                                                            ),
                                                            className=(
                                                                "ssb-dropdown"
                                                            ),
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            clearable=True,
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    id=(
                                                        self
                                                        .single_variable_container_id
                                                    ),
                                                    children=[
                                                        html.Label(
                                                            "Variabel"
                                                        ),
                                                        dcc.Dropdown(
                                                            id=(
                                                                self
                                                                .variable_id
                                                            ),
                                                            className=(
                                                                "ssb-dropdown"
                                                            ),
                                                            options=[],
                                                            clearable=False,
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    id=(
                                                        self
                                                        .multi_variable_container_id
                                                    ),
                                                    style={
                                                        "display": "none"
                                                    },
                                                    children=[
                                                        html.Label(
                                                            "Variabler"
                                                        ),
                                                        dcc.Dropdown(
                                                            id=(
                                                                self
                                                                .multi_variable_id
                                                            ),
                                                            className=(
                                                                "ssb-dropdown"
                                                            ),
                                                            options=[],
                                                            value=[],
                                                            multi=True,
                                                            clearable=True,
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            id=(
                                                self
                                                .enterprise_container_id
                                            ),
                                            style={
                                                "display": "none"
                                            },
                                            children=[
                                                html.Label(
                                                    "Organisasjonsnummer"
                                                ),
                                                dcc.Input(
                                                    id=self.enterprise_id,
                                                    type="text",
                                                    value="817209882",
                                                    placeholder=(
                                                        "Skriv inn "
                                                        "orgnr_foretak"
                                                    ),
                                                    debounce=True,
                                                    style={
                                                        "width": "100%",
                                                        "marginBottom": (
                                                            "12px"
                                                        ),
                                                    },
                                                ),
                                                html.Label(
                                                    "Eller søk etter navn"
                                                ),
                                                dcc.Dropdown(
                                                    id=(
                                                        self
                                                        .enterprise_name_search_id
                                                    ),
                                                    className=(
                                                        "ssb-dropdown"
                                                    ),
                                                    options=[],
                                                    value=None,
                                                    placeholder=(
                                                        "Skriv minst to tegn "
                                                        "i foretaksnavnet"
                                                    ),
                                                    clearable=True,
                                                    searchable=True,
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            id=(
                                                self
                                                .change_controls_container_id
                                            ),
                                            style={
                                                "display": "none"
                                            },
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.change_year_id,
                                                    className=(
                                                        "ssb-dropdown"
                                                    ),
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    (
                                                        "Antall største "
                                                        "foretak"
                                                    ),
                                                    style={
                                                        "marginTop": (
                                                            "12px"
                                                        ),
                                                    },
                                                ),
                                                dcc.Dropdown(
                                                    id=self.change_top_n_id,
                                                    className=(
                                                        "ssb-dropdown"
                                                    ),
                                                    options=[
                                                        {
                                                            "label": "5",
                                                            "value": 5,
                                                        },
                                                        {
                                                            "label": "10",
                                                            "value": 10,
                                                        },
                                                        {
                                                            "label": "15",
                                                            "value": 15,
                                                        },
                                                        {
                                                            "label": "20",
                                                            "value": 20,
                                                        },
                                                    ],
                                                    value=10,
                                                    clearable=False,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id=self.status_id
                                ),
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
            

    def _parquet_path(
        self,
        data_version: str,
        dataset: str = "agg_naring4",
    ) -> str:
        """Resolve the physical path for a logical VL dataset."""
        return self.file_path_resolver(
            data_version,
            dataset,
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
    @lru_cache(maxsize=4)
    def _read_enterprise_data(
        parquet_path: str,
    ) -> pd.DataFrame:
        """Read and cache the enterprise-level VL dataset."""
        df = pd.read_parquet(parquet_path)

        required_columns = {
            "orgnr_foretak",
            "year",
        }

        missing_columns = required_columns.difference(df.columns)

        if missing_columns:
            raise ValueError(
                "foretak.parquet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        df = df.copy()

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        )

        df["orgnr_foretak"] = (
            df["orgnr_foretak"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
        )

        return df

    @staticmethod
    @lru_cache(maxsize=4)
    def _read_business_data(
        parquet_path: str,
    ) -> pd.DataFrame:
        """Read and cache the business-level VL dataset."""
        df = pd.read_parquet(parquet_path)

        required_columns = {
            "orgnr_foretak",
            "orgnr_bedrift",
            "navn",
            "year",
            "naring_4",
        }

        missing_columns = required_columns.difference(df.columns)

        if missing_columns:
            raise ValueError(
                "bedrifter.parquet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        df = df.copy()

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        )

        df["naring_4"] = df["naring_4"].astype(str)

        df["orgnr_foretak"] = (
            df["orgnr_foretak"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
        )

        df["orgnr_bedrift"] = (
            df["orgnr_bedrift"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
        )

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

    @staticmethod
    def _create_industry_trend_figure(
        df: pd.DataFrame,
        narings: list[str],
        variable: str,
    ) -> go.Figure:
        """Create a time-series figure containing multiple industries."""
        fig = go.Figure()

        for naring in narings:
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

            fig.add_trace(
                go.Scatter(
                    x=sub["year"],
                    y=sub[variable],
                    mode="lines+markers",
                    name=str(naring),
                    line={"width": 3},
                    marker={"size": 7},
                    hovertemplate=(
                        "År: %{x}<br>"
                        f"Næring: {naring}<br>"
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
            title=f"{variable} – flere næringer",
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
    def _create_enterprise_trend_figure(
        df: pd.DataFrame,
        enterprise: str,
        variable: str,
    ) -> go.Figure:
        """Create a trend figure for one enterprise."""
        sub = df.loc[
            df["orgnr_foretak"].astype(str) == str(enterprise),
            ["year", variable],
        ].copy()

        sub = sub.dropna(subset=["year"])
        sub = sub.sort_values("year").reset_index(drop=True)

        sub[variable] = pd.to_numeric(
            sub[variable],
            errors="coerce",
        )

        fig = go.Figure()

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
                    f"Foretak: {enterprise}<br>"
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
            title=f"{variable} – foretak {enterprise}",
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
    def _create_change_share_figure(
        df: pd.DataFrame,
        naring: str,
        variable: str,
        year: int,
        top_n: int,
    ) -> go.Figure:
        """Show which enterprises contribute most to annual change."""
        previous_year = year - 1

        filtered = df.loc[
            (df["naring_4"].astype(str) == str(naring))
            & (df["year"].isin([previous_year, year])),
            [
                "orgnr_foretak",
                "navn",
                "year",
                variable,
            ],
        ].copy()

        if filtered.empty:
            return VLModule._empty_figure(
                (
                    f"Fant ingen data for næring {naring} "
                    f"i {previous_year} og {year}."
                )
            )

        filtered[variable] = pd.to_numeric(
            filtered[variable],
            errors="coerce",
        ).fillna(0)

        # A foretak can contain several establishments, so values are
        # aggregated to enterprise level before calculating the change.
        enterprise_values = (
            filtered.groupby(
                [
                    "orgnr_foretak",
                    "year",
                ],
                as_index=False,
            )
            .agg(
                value=(variable, "sum"),
                navn=(
                    "navn",
                    lambda values: next(
                        (
                            str(value)
                            for value in values
                            if pd.notna(value)
                            and str(value).strip()
                        ),
                        "",
                    ),
                ),
            )
        )

        values_by_year = enterprise_values.pivot(
            index="orgnr_foretak",
            columns="year",
            values="value",
        ).fillna(0)

        for required_year in [previous_year, year]:
            if required_year not in values_by_year.columns:
                values_by_year[required_year] = 0

        changes = values_by_year.reset_index()

        changes["change"] = (
            changes[year]
            - changes[previous_year]
        )

        names = (
            enterprise_values.loc[
                enterprise_values["navn"].astype(str).str.strip() != ""
            ]
            .sort_values("year")
            .drop_duplicates(
                subset="orgnr_foretak",
                keep="last",
            )
            .set_index("orgnr_foretak")["navn"]
        )

        changes["navn"] = (
            changes["orgnr_foretak"]
            .map(names)
            .fillna("")
        )

        changes["absolute_change"] = changes["change"].abs()

        changes = changes.loc[
            changes["absolute_change"] > 0
        ].copy()

        if changes.empty:
            return VLModule._empty_figure(
                (
                    f"Det var ingen registrerte endringer i "
                    f"{variable} for næring {naring} fra "
                    f"{previous_year} til {year}."
                )
            )

        changes = changes.sort_values(
            "absolute_change",
            ascending=False,
        )

        top_n = max(int(top_n), 1)

        largest = changes.head(top_n).copy()
        remaining = changes.iloc[top_n:].copy()

        largest["label"] = largest.apply(
            lambda row: (
                f"{row['navn']} — {row['orgnr_foretak']}"
                if str(row["navn"]).strip()
                else str(row["orgnr_foretak"])
            ),
            axis=1,
        )

        if not remaining.empty:
            other_row = pd.DataFrame(
                {
                    "label": ["Andre foretak"],
                    "absolute_change": [
                        remaining["absolute_change"].sum()
                    ],
                    "change": [
                        remaining["change"].sum()
                    ],
                }
            )

            plot_data = pd.concat(
                [
                    largest[
                        [
                            "label",
                            "absolute_change",
                            "change",
                        ]
                    ],
                    other_row,
                ],
                ignore_index=True,
            )
        else:
            plot_data = largest[
                [
                    "label",
                    "absolute_change",
                    "change",
                ]
            ].copy()

        total_absolute_change = plot_data[
            "absolute_change"
        ].sum()

        plot_data["share"] = (
            plot_data["absolute_change"]
            / total_absolute_change
            * 100
        )

        net_change = changes["change"].sum()

        figure = go.Figure(
            data=[
                go.Pie(
                    labels=plot_data["label"],
                    values=plot_data["absolute_change"],
                    customdata=plot_data[
                        [
                            "change",
                            "share",
                        ]
                    ],
                    hole=0.35,
                    textinfo="label+percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Andel av absolutt endring: "
                        "%{customdata[1]:.1f}%<br>"
                        "Endring: %{customdata[0]:,.0f}"
                        "<extra></extra>"
                    ),
                )
            ]
        )

        figure.update_layout(
            title=(
                f"{variable} – bidrag til endringen i næring "
                f"{naring}, {previous_year}–{year}"
                f"<br><sup>Nettoendring: {net_change:,.0f}</sup>"
            ),
            legend_title_text="Foretak",
            margin={
                "l": 40,
                "r": 40,
                "t": 100,
                "b": 40,
            },
        )

        return figure

    def module_callbacks(self) -> None:
        """Register VL callbacks."""

        @callback(
            Output(self.naring_id, "options"),
            Output(self.naring_id, "value"),
            Output(self.multi_naring_id, "options"),
            Output(self.multi_naring_id, "value"),
            Output(self.variable_id, "options"),
            Output(self.variable_id, "value"),
            Output(self.multi_variable_id, "options"),
            Output(self.multi_variable_id, "value"),
            Output(self.change_year_id, "options"),
            Output(self.change_year_id, "value"),
            Output(self.status_id, "children"),
            Input(self.data_version_id, "value"),
        )

        def load_dropdown_options(
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
            list[dict[str, str]],
            list[str],
            list[dict[str, str]],
            str | None,
            list[dict[str, str]],
            list[str],
            list[dict[str, int]],
            int | None,
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

                multi_naring_value = naring_values[:3]

                variable_value = (
                    variable_values[0]
                    if variable_values
                    else None
                )

                multi_variable_value = variable_values[:3]

                year_values = sorted(
                    df["year"]
                    .dropna()
                    .astype(int)
                    .unique()
                    .tolist()
                )

                year_options = [
                    {
                        "label": str(year),
                        "value": year,
                    }
                    for year in year_values
                ]

                change_year_value = (
                    year_values[-1]
                    if year_values
                    else None
                )

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
                    naring_options,
                    multi_naring_value,
                    variable_options,
                    variable_value,
                    variable_options,
                    multi_variable_value,
                    year_options,
                    change_year_value,
                    status,
                )

            except Exception as error:
                return (
                    [],
                    None,
                    [],
                    [],
                    [],
                    None,
                    [],
                    [],
                    [],
                    None,
                    html.Div(
                        f"Kunne ikke lese data: {error}",
                        className="alert alert-danger",
                    ),
                )

        @callback(
            Output(self.enterprise_name_search_id, "options"),
            Input(self.enterprise_name_search_id, "search_value"),
            Input(self.data_version_id, "value"),
        )
        def search_enterprise_names(
            search_value: str | None,
            data_version: str,
        ) -> list[dict[str, str]]:
            """Return a limited list of enterprises matching name or orgnr."""
            if not search_value:
                return []

            search_text = search_value.strip()

            if len(search_text) < 2:
                return []

            parquet_path = self._parquet_path(
                data_version,
                dataset="foretak",
            )
            df = self._read_enterprise_data(parquet_path)

            if "navn" not in df.columns:
                return []

            lookup = df.loc[
                df["navn"].notna(),
                [
                    "orgnr_foretak",
                    "year",
                    "navn",
                ],
            ].copy()

            lookup["navn"] = lookup["navn"].astype(str)
            lookup["orgnr_foretak"] = (
                lookup["orgnr_foretak"].astype(str)
            )

            # Use the latest available non-missing name for each enterprise.
            lookup = (
                lookup.sort_values(
                    "year",
                    ascending=False,
                )
                .drop_duplicates(
                    subset="orgnr_foretak",
                    keep="first",
                )
            )

            matches = lookup.loc[
                lookup["navn"].str.contains(
                    search_text,
                    case=False,
                    na=False,
                    regex=False,
                )
                | lookup["orgnr_foretak"].str.contains(
                    search_text,
                    case=False,
                    na=False,
                    regex=False,
                )
            ].head(25)

            return [
                {
                    "label": (
                        f"{row.navn} — "
                        f"{row.orgnr_foretak}"
                    ),
                    "value": row.orgnr_foretak,
                }
                for row in matches.itertuples()
            ]

        @callback(
            Output(self.enterprise_id, "value"),
            Input(self.enterprise_name_search_id, "value"),
            prevent_initial_call=True,
        )
        def select_enterprise_from_name(
            selected_orgnr: str | None,
        ) -> str | Any:
            """Copy the selected organisation number into the input field."""
            if not selected_orgnr:
                return no_update

            return str(selected_orgnr)

        @callback(
            Output(self.graph_title_id, "children"),
            Output(self.graph_description_id, "children"),
            Output(self.single_naring_container_id, "style"),
            Output(self.multi_naring_container_id, "style"),
            Output(self.enterprise_container_id, "style"),
            Output(self.change_controls_container_id, "style"),
            Output(self.single_variable_container_id, "style"),
            Output(self.multi_variable_container_id, "style"),
            Input(self.visualisation_id, "value"),
        )
        def update_visualisation_controls(
            visualisation: str,
        ) -> tuple[
            str,
            str,
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
        ]:
            if visualisation == "trend-multi":
                return (
                    "Trendanalyse – flere variabler",
                    (
                        "Sammenligner utviklingen i flere valgte variabler "
                        "for samme næring over tid."
                    ),
                    {"display": "block"},  # single næring
                    {"display": "none"},   # multiple næringer
                    {"display": "none"},   # enterprise
                    {"display": "none"},   # change controls
                    {"display": "none"},   # single variable
                    {"display": "block"},  # multiple variables
                )

            if visualisation == "trend-industries":
                return (
                    "Trendanalyse – flere næringer",
                    (
                        "Sammenligner utviklingen i én valgt variabel "
                        "for flere næringer over tid."
                    ),
                    {"display": "none"},   # single næring
                    {"display": "block"},  # multiple næringer
                    {"display": "none"},   # enterprise
                    {"display": "none"},   # change controls
                    {"display": "block"},  # single variable
                    {"display": "none"},   # multiple variables
                )

            if visualisation == "trend-enterprise":
                return (
                    "Trendanalyse – enkeltforetak",
                    (
                        "Viser utviklingen i én valgt variabel "
                        "for ett foretak over tid."
                    ),
                    {"display": "none"},   # single næring
                    {"display": "none"},   # multiple næringer
                    {"display": "block"},  # enterprise
                    {"display": "none"},   # change controls
                    {"display": "block"},  # single variable
                    {"display": "none"},   # multiple variables
                )

            if visualisation == "change-share":
                return (
                    "Prosentandeler av endringene",
                    (
                        "Viser hvilke foretak som bidrar mest til "
                        "endringen i valgt variabel fra året før."
                    ),
                    {"display": "block"},  # single næring
                    {"display": "none"},   # multiple næringer
                    {"display": "none"},   # enterprise
                    {"display": "block"},  # change controls
                    {"display": "block"},  # single variable
                    {"display": "none"},   # multiple variables
                )

            return (
                "Trendanalyse – én variabel",
                (
                    "Viser utviklingen over tid sammen med forventet "
                    "variasjonsområde basert på historiske endringer."
                ),
                {"display": "block"},  # single næring
                {"display": "none"},   # multiple næringer
                {"display": "none"},   # enterprise
                {"display": "none"},   # change controls
                {"display": "block"},  # single variable
                {"display": "none"},   # multiple variables
            )

        @callback(
            Output(self.graph_id, "figure"),
            Output(self.graph_section_id, "style"),
            Input(self.visualisation_id, "value"),
            Input(self.data_version_id, "value"),
            Input(self.naring_id, "value"),
            Input(self.multi_naring_id, "value"),
            Input(self.enterprise_id, "value"),
            Input(self.variable_id, "value"),
            Input(self.multi_variable_id, "value"),
            Input(self.change_year_id, "value"),
            Input(self.change_top_n_id, "value"),
        )
        def update_graph(
            visualisation: str,
            data_version: str,
            naring: str | None,
            multi_narings: list[str] | None,
            enterprise: str | None,
            variable: str | None,
            multi_variables: list[str] | None,
            change_year: int | None,
            change_top_n: int | None,
        ) -> tuple[go.Figure, dict[str, str]]:
            supported_visualisations = {
                "trend-single",
                "trend-multi",
                "trend-industries",
                "trend-enterprise",
                "change-share",
            }

            graph_style = {
                "display": "block",
                "width": "100%",
                "maxWidth": "none",
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
                    graph_style,
                )

            try:
                if visualisation == "trend-enterprise":
                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="foretak",
                    )
                    df = self._read_enterprise_data(
                        parquet_path
                    )

                elif visualisation == "change-share":
                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )
                    df = self._read_business_data(
                        parquet_path
                    )

                else:
                    parquet_path = self._parquet_path(
                        data_version
                    )
                    df = self._read_data(
                        parquet_path
                    )

                if visualisation == "trend-multi":
                    if not naring:
                        figure = self._empty_figure(
                            "Velg en næring."
                        )
                    elif not multi_variables:
                        figure = self._empty_figure(
                            "Velg minst én variabel."
                        )
                    else:
                        figure = self._create_multi_trend_figure(
                            df=df,
                            naring=naring,
                            variables=multi_variables,
                        )

                elif visualisation == "trend-enterprise":
                    if not enterprise:
                        figure = self._empty_figure(
                            "Velg et foretak."
                        )
                    elif not variable:
                        figure = self._empty_figure(
                            "Velg en variabel."
                        )
                    elif variable not in df.columns:
                        figure = self._empty_figure(
                            f"Variabelen {variable} finnes ikke i foretaksdataene."
                        )
                    else:
                        figure = self._create_enterprise_trend_figure(
                            df=df,
                            enterprise=enterprise,
                            variable=variable,
                        )

                elif visualisation == "change-share":
                    if not naring:
                        figure = self._empty_figure(
                            "Velg en næring."
                        )
                    elif not variable:
                        figure = self._empty_figure(
                            "Velg en variabel."
                        )
                    elif change_year is None:
                        figure = self._empty_figure(
                            "Velg et år."
                        )
                    elif variable not in df.columns:
                        figure = self._empty_figure(
                            f"Variabelen {variable} finnes ikke i bedriftsdataene."
                        )
                    else:
                        figure = self._create_change_share_figure(
                            df=df,
                            naring=naring,
                            variable=variable,
                            year=change_year,
                            top_n=change_top_n or 10,
                        )
                else:
                    if not naring:
                        figure = self._empty_figure(
                            "Velg en næring."
                        )
                    elif not variable:
                        figure = self._empty_figure(
                            "Velg en variabel."
                        )
                    else:
                        figure = self._create_trend_figure(
                            df=df,
                            naring=naring,
                            variable=variable,
                        )

                return figure, graph_style

            except Exception as error:
                return (
                    self._empty_figure(
                        f"Kunne ikke lage figur: {error}"
                    ),
                    graph_style,
                )


class VLModuleTab(TabImplementation, VLModule):
    """VL module displayed as an application tab."""

    def __init__(
        self,
        file_path_resolver: Callable[[str, str], str],
    ) -> None:
        VLModule.__init__(
            self,
            file_path_resolver=file_path_resolver,
        )
        TabImplementation.__init__(self)


class VLModuleWindow(WindowImplementation, VLModule):
    """VL module displayed as a sidebar window."""

    def __init__(
        self,
        file_path_resolver: Callable[[str, str], str],
    ) -> None:
        VLModule.__init__(
            self,
            file_path_resolver=file_path_resolver,
        )
        WindowImplementation.__init__(self)