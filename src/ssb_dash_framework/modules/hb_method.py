"""HB methodology application module."""

import logging
from dataclasses import asdict
from io import StringIO
from typing import Any

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.modules.hb.period_resolution import (
    resolve_hb_comparison_periods,
)
from ssb_dash_framework.modules.hb.vaskify import normalize_hb_result
from ssb_dash_framework.modules.hb.vaskify import run_hb_vaskify
from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.utils.alert_handler import AlertHandler
from ssb_dash_framework.utils.base_classes import AsType
from ssb_dash_framework.utils.base_classes import ModuleBase

logger = logging.getLogger(__name__)


def _extract_hb_unit_id_from_plotly_click_data(
    click_data: dict[str, Any] | None,
) -> str | None:
    """Read the stable unit identifier from a Plotly point's customdata."""
    if click_data is None:
        return None

    clicked_points = click_data.get("points")
    if not isinstance(clicked_points, list) or not clicked_points:
        return None

    clicked_point = clicked_points[0]
    if not isinstance(clicked_point, dict):
        return None

    point_customdata = clicked_point.get("customdata")
    if isinstance(point_customdata, (list, tuple)):
        if not point_customdata:
            return None
        clicked_hb_unit_id = point_customdata[0]
    else:
        clicked_hb_unit_id = point_customdata

    if not isinstance(clicked_hb_unit_id, str) or not clicked_hb_unit_id:
        return None
    return clicked_hb_unit_id


class HBMethod(ModuleBase):
    """Module shell for running and displaying the HB methodology."""

    def __init__(
        self,
        *,
        hb_data_handler: HBDataHandlerMeta,
        hb_variable_selector: str,
        configured_hb_time_unit: TimeUnit,
        configured_hb_strata_variable: str | None = None,
        as_type: AsType | None = None,
    ) -> None:
        """Initialize with the handler and validated selector configuration.

        Args:
            hb_data_handler: Source adapter that returns common HB input data.
            hb_variable_selector: Shared selector title containing the HB variable.
            configured_hb_time_unit: The same time unit used by the app's
                `VariableSelectorConfig`; its name must match the configured period
                selector.
            configured_hb_strata_variable: Optional source grouping variable.
            as_type: Optional ModuleBase placement as a tab or window.
        """
        if not isinstance(hb_variable_selector, str) or not hb_variable_selector.strip():
            raise ValueError("hb_variable_selector must be a non-empty selector title.")
        if not isinstance(configured_hb_time_unit, TimeUnit):
            raise TypeError("configured_hb_time_unit must be a TimeUnit.")
        if configured_hb_strata_variable is not None and (
            not isinstance(configured_hb_strata_variable, str)
            or not configured_hb_strata_variable.strip()
        ):
            raise ValueError(
                "configured_hb_strata_variable must be a non-empty string or None."
            )

        if hb_variable_selector == configured_hb_time_unit.name:
            raise ValueError(
                "hb_variable_selector must differ from the configured period selector."
            )
        selector_period_state = VariableSelector.get_timevar(State)
        VariableSelector.get_state(hb_variable_selector)
        configured_period_state = VariableSelector.get_state(
            configured_hb_time_unit.name
        )[0]
        if selector_period_state.component_id != configured_period_state.component_id:
            raise ValueError(
                "configured_hb_time_unit must use the same selector name as the "
                "VariableSelector period configuration."
            )

        self.label = "HB metoden"
        self.icon = DashIconify(icon="keyline-icons:pencil-ruler-sharp-duotone", width=24)
        self.hb_data_handler = hb_data_handler
        self.hb_variable_selector = hb_variable_selector
        self.configured_hb_time_unit = configured_hb_time_unit
        self.configured_hb_strata_variable = configured_hb_strata_variable

        super().__init__(as_type=as_type)

    def layout(self) -> html.Div:
        """Create the HB controls and placeholders for a run's state and result."""
        return html.Div(
            children=[
                dcc.Store(id=f"{self.module_id}-hb_result_store", data=None),
                html.Div(
                    dbc.Button(
                        "Kjør HB-metoden",
                        id=f"{self.module_id}-hb_run_button",
                        n_clicks=0,
                        className="ssb-btn primary-btn",
                    ),
                    id=f"{self.module_id}-hb_controls",
                ),
                dbc.Alert(
                    id=f"{self.module_id}-hb_error_message",
                    color="danger",
                    is_open=False,
                ),
                html.Div(
                    "Kjør HB-metoden for å vise resultater.",
                    id=f"{self.module_id}-hb_empty_state",
                    role="status",
                ),
                html.Div(
                    id=f"{self.module_id}-hb_candidate_state_summary",
                    role="status",
                    style={"display": "none"},
                ),
                dcc.Loading(
                    id=f"{self.module_id}-hb_result_loading",
                    type="default",
                    children=dcc.Graph(
                        id=f"{self.module_id}-hb_result_graph",
                        figure={},
                        style={"display": "none"},
                        config={"displaylogo": False},
                    ),
                ),
            ]
        )

    def _build_hb_result_figure(
        self,
        normalized_hb_result_dataframe: pd.DataFrame,
        *,
        hb_comparison_periods: tuple[str, str],
    ) -> go.Figure:
        """Plot returned HB ratios, thresholds, and candidate states."""
        selected_period_value_column = f"value_{hb_comparison_periods[1]}"
        hb_result_figure = go.Figure()

        if self.configured_hb_strata_variable is not None:
            hb_strata_groups = normalized_hb_result_dataframe.groupby(
                "strata",
                dropna=False,
                sort=False,
            )
        else:
            hb_strata_groups = [("All units", normalized_hb_result_dataframe)]

        for hb_strata_value, hb_strata_result_dataframe in hb_strata_groups:
            strata_label = (
                f" — {hb_strata_value}"
                if self.configured_hb_strata_variable is not None
                else ""
            )
            sorted_hb_strata_dataframe = hb_strata_result_dataframe.sort_values(
                selected_period_value_column,
                kind="stable",
                na_position="last",
            )
            for diagnostic_column, diagnostic_label, diagnostic_color in (
                ("median_ratio", "Median ratio", "#f1c40f"),
                ("upper_limit", "Øvre grense", "#e74c3c"),
                ("lower_limit", "Nedre grense", "#e74c3c"),
            ):
                diagnostic_values_dataframe = sorted_hb_strata_dataframe.dropna(
                    subset=[selected_period_value_column, diagnostic_column]
                )
                if diagnostic_values_dataframe.empty:
                    continue
                hb_result_figure.add_trace(
                    go.Scatter(
                        x=diagnostic_values_dataframe[selected_period_value_column],
                        y=diagnostic_values_dataframe[diagnostic_column],
                        mode="lines+markers",
                        name=f"{diagnostic_label}{strata_label}",
                        line={"color": diagnostic_color, "dash": "solid"},
                        marker={"size": 5},
                        customdata=diagnostic_values_dataframe[["unit_id"]].to_numpy(),
                        hovertemplate=(
                            "Enhet: %{customdata[0]}<br>"
                            f"{diagnostic_label}: %{{y}}<extra>{strata_label}</extra>"
                        ),
                    )
                )

        for candidate_flag, candidate_label, candidate_color in (
            (1, "Flagget", "#e74c3c"),
            (0, "Ikke flagget", "#3498db"),
        ):
            candidate_result_dataframe = normalized_hb_result_dataframe.loc[
                normalized_hb_result_dataframe["flag_hb"].eq(candidate_flag)
            ].dropna(subset=[selected_period_value_column, "ratio"])
            if candidate_result_dataframe.empty:
                continue
            hb_result_figure.add_trace(
                go.Scatter(
                    x=candidate_result_dataframe[selected_period_value_column],
                    y=candidate_result_dataframe["ratio"],
                    mode="markers",
                    name=candidate_label,
                    marker={"color": candidate_color, "size": 9},
                    customdata=candidate_result_dataframe[
                        ["unit_id", "median_ratio", "lower_limit", "upper_limit"]
                    ].to_numpy(),
                    hovertemplate=(
                        "Enhet: %{customdata[0]}<br>"
                        "Ratio: %{y}<br>"
                        "Median ratio: %{customdata[1]}<br>"
                        "Nedre grense: %{customdata[2]}<br>"
                        "Øvre grense: %{customdata[3]}<extra>"
                        f"{candidate_label}</extra>"
                    ),
                )
            )

        hb_result_figure.update_layout(
            title="HB-metoden",
            xaxis_title=f"Verdi i {hb_comparison_periods[1]}",
            yaxis_title="Forholdstall (ratio)",
            legend_title="Kandidatstatus",
            height=700,
            hovermode="closest",
        )
        return hb_result_figure

    def _execute_hb_run(
        self,
        *,
        selected_hb_variable: str | None,
        selector_period_value: str | None,
    ) -> dict[str, Any]:
        """Fetch, analyze, and normalize the HB data for one explicit run."""
        if not isinstance(selected_hb_variable, str) or not selected_hb_variable.strip():
            raise ValueError("Select an HB variable before running the HB method.")
        if not isinstance(selector_period_value, str) or not selector_period_value.strip():
            raise ValueError("Select a period before running the HB method.")

        hb_comparison_periods = resolve_hb_comparison_periods(
            selected_hb_period=selector_period_value,
            configured_hb_time_unit=self.configured_hb_time_unit,
        )
        hb_data_result = self.hb_data_handler.get_hb_dataframe(
            selected_hb_variable=selected_hb_variable,
            hb_comparison_periods=hb_comparison_periods,
            configured_hb_strata_variable=self.configured_hb_strata_variable,
        )
        if hb_data_result.hb_warnings:
            AlertHandler.warning(
                "HB-data inneholder "
                f"{len(hb_data_result.hb_warnings)} advarsel/advarsler.",
                ephemeral=True,
            )
        hb_vaskify_result_dataframe = run_hb_vaskify(
            hb_data_result.hb_dataframe,
            hb_comparison_periods=hb_comparison_periods,
            configured_hb_strata_variable=self.configured_hb_strata_variable,
        )
        normalized_hb_result_dataframe = normalize_hb_result(
            hb_data_result.hb_dataframe,
            hb_vaskify_result_dataframe,
            hb_comparison_periods=hb_comparison_periods,
            configured_hb_strata_variable=self.configured_hb_strata_variable,
        )
        return {
            "hb_comparison_periods": list(hb_comparison_periods),
            "hb_result_dataframe_json": normalized_hb_result_dataframe.to_json(
                orient="split",
                date_format="iso",
            ),
            "hb_warnings": [asdict(hb_warning) for hb_warning in hb_data_result.hb_warnings],
        }

    def module_callbacks(self) -> None:
        """Register callbacks for running HB and displaying the stored result."""
        selected_hb_variable_state = VariableSelector.get_state(
            self.hb_variable_selector
        )[0]
        selector_period_state = VariableSelector.get_timevar(State)

        @callback(
            Output(f"{self.module_id}-hb_result_store", "data"),
            Input(f"{self.module_id}-hb_run_button", "n_clicks"),
            selected_hb_variable_state,
            selector_period_state,
            prevent_initial_call=True,
        )
        def retrieve_hb_data_for_run(
            n_clicks: int | None,
            selected_hb_variable: str | None,
            selector_period_value: str | None,
        ) -> dict[str, Any] | None:
            if not n_clicks:
                raise PreventUpdate
            try:
                return self._execute_hb_run(
                    selected_hb_variable=selected_hb_variable,
                    selector_period_value=selector_period_value,
                )
            except Exception as error:
                logger.error(
                    "HB run failed (module_id=%s, selected_hb_variable=%r, "
                    "selector_period_value=%r, exception_type=%s).",
                    self.module_id,
                    selected_hb_variable,
                    selector_period_value,
                    type(error).__name__,
                )
                AlertHandler.error(
                    "HB-kjøringen feilet. Kontroller valgt variabel og periode.",
                    ephemeral=True,
                )
                return None

        @callback(
            Output(f"{self.module_id}-hb_result_graph", "figure"),
            Output(f"{self.module_id}-hb_result_graph", "style"),
            Output(f"{self.module_id}-hb_empty_state", "style"),
            Output(f"{self.module_id}-hb_candidate_state_summary", "children"),
            Output(f"{self.module_id}-hb_candidate_state_summary", "style"),
            Input(f"{self.module_id}-hb_result_store", "data"),
        )
        def display_hb_result(
            hb_result_store_data: dict[str, Any] | None,
        ) -> tuple[go.Figure | dict[str, Any], dict[str, str], dict[str, str], str, dict[str, str]]:
            if hb_result_store_data is None:
                return {}, {"display": "none"}, {}, "", {"display": "none"}

            normalized_hb_result_dataframe = pd.read_json(
                StringIO(hb_result_store_data["hb_result_dataframe_json"]),
                orient="split",
            )
            hb_comparison_periods = tuple(
                hb_result_store_data["hb_comparison_periods"]
            )
            if len(hb_comparison_periods) != 2:
                raise ValueError("HB result must contain exactly two comparison periods.")

            hb_result_figure = self._build_hb_result_figure(
                normalized_hb_result_dataframe,
                hb_comparison_periods=(
                    hb_comparison_periods[0],
                    hb_comparison_periods[1],
                ),
            )
            candidate_flags = normalized_hb_result_dataframe["flag_hb"]
            candidate_state_summary = (
                f"Flagget: {candidate_flags.eq(1).sum()} · "
                f"Ikke flagget: {candidate_flags.eq(0).sum()} · "
                f"Ikke sammenlignbar: {candidate_flags.isna().sum()}"
            )
            return (
                hb_result_figure,
                {"display": "block"},
                {"display": "none"},
                candidate_state_summary,
                {"display": "block"},
            )
