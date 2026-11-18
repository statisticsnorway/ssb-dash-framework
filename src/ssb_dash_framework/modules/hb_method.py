"""HB methodology application module."""

from dataclasses import asdict
from typing import Any

import dash_bootstrap_components as dbc
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
from ssb_dash_framework.utils.base_classes import AsType
from ssb_dash_framework.utils.base_classes import ModuleBase


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
                dcc.Loading(
                    id=f"{self.module_id}-hb_result_loading",
                    type="default",
                    children=dcc.Graph(
                        id=f"{self.module_id}-hb_result_graph",
                        figure={},
                        style={"display": "none"},
                    ),
                ),
            ]
        )

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
        """Register the explicit-run callback for selector-backed HB data retrieval."""
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
        ) -> dict[str, Any]:
            if not n_clicks:
                raise PreventUpdate
            return self._execute_hb_run(
                selected_hb_variable=selected_hb_variable,
                selector_period_value=selector_period_value,
            )
