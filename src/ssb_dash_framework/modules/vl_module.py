"""
Reusable Dash module for VL analysis and quality control.

The module provides interactive figures and control tables for analysing
industry-level, enterprise-level and business-level VL data. It supports
both consolidated and unconsolidated datasets through an application-
provided file-path resolver.

Module structure
----------------
1. Visualisation registry and shared conventions
2. Component identifiers and layout construction
3. Dataset resolution and cached readers
4. Figure builders
5. Analysis and table-data builders
6. Shared table formatting
7. Dash callback registration
8. Framework tab and window adapters

Available analyses
------------------
- single-variable, multi-variable and multi-industry trends
- enterprise-level trend analysis
- contribution to year-over-year changes
- NØKU control tables and contributor drilldowns
- large business-level changes and rate summaries
- negative NO-post controls and enterprise drilldowns
- NR logical controls and enterprise drilldowns
- checks for related variables moving in opposite directions
- composite-variable breakdowns by industry, enterprise or business
- comparisons with MOMS data
- business entry, exit and industry-code movement
- method and accounting-ratio analysis

Industry-code convention
------------------------
Detailed industry codes include a decimal point. Character lengths are
therefore 2 for N2 (``47``), 4 for N3 (``47.3``), 5 for N4 (``47.31``)
and 6 for N5 (``47.310``). Where possible, this module derives levels
directly from the detailed ``naring`` code instead of relying on legacy
helper columns whose names do not always correspond to the displayed level.

Design notes
------------
The class owns its Dash component IDs, layout, cached readers, transformation
helpers and callbacks. Physical dataset locations remain application-specific
and are supplied through ``file_path_resolver``.
"""

from functools import lru_cache
from collections.abc import Callable
from typing import Any
from typing import ClassVar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from klass import KlassClassification
from dash import Input
from dash import Output
from dash import callback
from dash import dash_table
from dash import dcc
from dash import html
from dash import no_update

from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator


# ============================================================================
# Visualisation registry
# ============================================================================

TREND_SINGLE_LABEL = "Trendanalyse – én variabel"
TREND_MULTI_LABEL = "Trendanalyse – flere variabler"
TREND_INDUSTRIES_LABEL = "Trendanalyse – flere næringer"

VL_VISUALISATIONS = {
    "trend-single": TREND_SINGLE_LABEL,
    "trend-multi": TREND_MULTI_LABEL,
    "trend-industries": TREND_INDUSTRIES_LABEL,
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


# ============================================================================
# Core VL module
# ============================================================================

class VLModule:
    """
    Build and manage the interactive VL analysis interface.

    Each instance creates unique Dash component identifiers, constructs the
    complete layout and registers every callback required by the module.

    Parameters
    ----------
    file_path_resolver:
        Callable receiving ``data_version`` and ``dataset`` and returning the
        physical path to the requested parquet dataset.

    Notes
    -----
    Multiple instances may be mounted in the same Dash application. The
    monotonically increasing ``module_number`` is included in every component
    identifier to prevent layout and callback ID collisions.
    """

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

        # Main selections
        self.data_version_id = (
            f"vl-data-version-{self.module_number}"
        )
        self.visualisation_id = (
            f"vl-visualisation-{self.module_number}"
        )

        # Trend-analysis controls
        self.naring_id = (
            f"vl-naring-{self.module_number}"
        )
        self.variable_id = (
            f"vl-variable-{self.module_number}"
        )
        self.multi_variable_id = (
            f"vl-multi-variable-{self.module_number}"
        )

        self.multi_naring_group_id = (
            f"vl-multi-naring-group-{self.module_number}"
        )

        self.multi_naring_id = (
            f"vl-multi-naring-{self.module_number}"
        )

        # Enterprise trend controls
        self.enterprise_id = (
            f"vl-enterprise-{self.module_number}"
        )
        self.enterprise_name_search_id = (
            f"vl-enterprise-name-search-{self.module_number}"
        )

        # Change-share controls
        self.change_year_id = (
            f"vl-change-year-{self.module_number}"
        )
        self.change_top_n_id = (
            f"vl-change-top-n-{self.module_number}"
        )

        # NØKU table controls
        self.noku_group_id = (
            f"vl-noku-group-{self.module_number}"
        )
        self.noku_year_id = (
            f"vl-noku-year-{self.module_number}"
        )
        self.noku_rate_id = (
            f"vl-noku-rate-{self.module_number}"
        )
        self.noku_window_id = (
            f"vl-noku-window-{self.module_number}"
        )
        self.noku_standard_deviations_id = (
            f"vl-noku-standard-deviations-{self.module_number}"
        )

        # Large-changes controls
        self.large_changes_year_id = (
            f"vl-large-changes-year-{self.module_number}"
        )
        self.large_changes_group_level_id = (
            f"vl-large-changes-group-level-{self.module_number}"
        )
        self.large_changes_group_value_id = (
            f"vl-large-changes-group-value-{self.module_number}"
        )
        self.large_changes_variables_id = (
            f"vl-large-changes-variables-{self.module_number}"
        )
        self.large_changes_fylke_id = (
            f"vl-large-changes-fylke-{self.module_number}"
        )
        self.large_changes_top_n_id = (
            f"vl-large-changes-top-n-{self.module_number}"
        )

        # Negative NO-post controls
        self.negative_nopost_year_id = (
            f"vl-negative-nopost-year-{self.module_number}"
        )
        self.negative_nopost_group_level_id = (
            f"vl-negative-nopost-group-level-{self.module_number}"
        )
        self.negative_nopost_threshold_id = (
            f"vl-negative-nopost-threshold-{self.module_number}"
        )
        self.negative_nopost_hide_columns_id = (
            f"vl-negative-nopost-hide-columns-{self.module_number}"
        )
        self.negative_nopost_max_rows_id = (
            f"vl-negative-nopost-max-rows-{self.module_number}"
        )

        self.negative_nopost_selected_group_id = (
            f"vl-negative-nopost-selected-group-{self.module_number}"
        )
        self.negative_nopost_variable_id = (
            f"vl-negative-nopost-variable-{self.module_number}"
        )
        self.negative_nopost_top_enterprises_id = (
            f"vl-negative-nopost-top-enterprises-{self.module_number}"
        )
        self.negative_nopost_drilldown_container_id = (
            f"vl-negative-nopost-drilldown-container-{self.module_number}"
        )
        self.negative_nopost_drilldown_table_id = (
            f"vl-negative-nopost-drilldown-table-{self.module_number}"
        )
        self.negative_nopost_drilldown_message_id = (
            f"vl-negative-nopost-drilldown-message-{self.module_number}"
        )

        # NR-control controls
        self.nr_year_id = (
            f"vl-nr-year-{self.module_number}"
        )
        self.nr_group_level_id = (
            f"vl-nr-group-level-{self.module_number}"
        )
        self.nr_view_id = (
            f"vl-nr-view-{self.module_number}"
        )
        self.nr_threshold_id = (
            f"vl-nr-threshold-{self.module_number}"
        )
        self.nr_hide_columns_id = (
            f"vl-nr-hide-columns-{self.module_number}"
        )
        self.nr_max_rows_id = (
            f"vl-nr-max-rows-{self.module_number}"
        )

        self.nr_selected_group_id = (
            f"vl-nr-selected-group-{self.module_number}"
        )

        self.nr_variable_id = (
            f"vl-nr-variable-{self.module_number}"
        )

        self.nr_top_enterprises_id = (
            f"vl-nr-top-enterprises-{self.module_number}"
        )

        self.nr_drilldown_container_id = (
            f"vl-nr-drilldown-container-{self.module_number}"
        )

        self.nr_drilldown_table_id = (
            f"vl-nr-drilldown-table-{self.module_number}"
        )

        self.nr_drilldown_message_id = (
            f"vl-nr-drilldown-message-{self.module_number}"
        )

        # Opposite-direction controls
        self.opposite_year_id = (
            f"vl-opposite-year-{self.module_number}"
        )
        self.opposite_group_level_id = (
            f"vl-opposite-group-level-{self.module_number}"
        )
        self.opposite_view_id = (
            f"vl-opposite-view-{self.module_number}"
        )
        self.opposite_rule_id = (
            f"vl-opposite-rule-{self.module_number}"
        )
        self.opposite_min_count_id = (
            f"vl-opposite-min-count-{self.module_number}"
        )
        self.opposite_gap_threshold_id = (
            f"vl-opposite-gap-threshold-{self.module_number}"
        )
        self.opposite_absolute_threshold_id = (
            f"vl-opposite-absolute-threshold-{self.module_number}"
        )
        self.opposite_max_rows_id = (
            f"vl-opposite-max-rows-{self.module_number}"
        )

        # Breakdown controls
        self.breakdown_analysis_level_id = (
            f"vl-breakdown-analysis-level-{self.module_number}"
        )

        self.breakdown_year_id = (
            f"vl-breakdown-year-{self.module_number}"
        )

        self.breakdown_industry_controls_id = (
            f"vl-breakdown-industry-controls-{self.module_number}"
        )

        self.breakdown_group_level_id = (
            f"vl-breakdown-group-level-{self.module_number}"
        )

        self.breakdown_group_value_id = (
            f"vl-breakdown-group-value-{self.module_number}"
        )

        self.breakdown_enterprise_controls_id = (
            f"vl-breakdown-enterprise-controls-{self.module_number}"
        )

        self.breakdown_enterprise_search_id = (
            f"vl-breakdown-enterprise-search-{self.module_number}"
        )

        self.breakdown_enterprise_id = (
            f"vl-breakdown-enterprise-{self.module_number}"
        )

        self.breakdown_unit_level_id = (
            f"vl-breakdown-unit-level-{self.module_number}"
        )

        self.breakdown_business_id = (
            f"vl-breakdown-business-{self.module_number}"
        )

        self.breakdown_variable_id = (
            f"vl-breakdown-variable-{self.module_number}"
        )

        # MOMS controls
        self.moms_group_level_id = (
            f"vl-moms-group-level-{self.module_number}"
        )

        self.moms_naring_filter_id = (
            f"vl-moms-naring-filter-{self.module_number}"
        )

        self.moms_previous_year_id = (
            f"vl-moms-previous-year-{self.module_number}"
        )
        self.moms_current_year_id = (
            f"vl-moms-current-year-{self.module_number}"
        )

        # Movement controls
        self.movement_direction_id = (
            f"vl-movement-direction-{self.module_number}"
        )
        self.movement_variable_id = (
            f"vl-movement-variable-{self.module_number}"
        )
        self.movement_group_level_id = (
            f"vl-movement-group-level-{self.module_number}"
        )
        self.movement_code_filter_id = (
            f"vl-movement-code-filter-{self.module_number}"
        )
        self.movement_exact_match_id = (
            f"vl-movement-exact-match-{self.module_number}"
        )
        self.movement_top_n_id = (
            f"vl-movement-top-n-{self.module_number}"
        )

        # Method-analysis controls
        self.method_naring_level_id = (
            f"vl-method-naring-level-{self.module_number}"
        )
        self.method_naring_value_id = (
            f"vl-method-naring-value-{self.module_number}"
        )
        self.method_ratios_id = (
            f"vl-method-ratios-{self.module_number}"
        )
        self.method_reg_types_id = (
            f"vl-method-reg-types-{self.module_number}"
        )

        # Control containers
        self.single_naring_container_id = (
            f"vl-single-naring-container-{self.module_number}"
        )
        self.multi_naring_container_id = (
            f"vl-multi-naring-container-{self.module_number}"
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
        self.change_controls_container_id = (
            f"vl-change-controls-container-{self.module_number}"
        )
        self.noku_controls_container_id = (
            f"vl-noku-controls-container-{self.module_number}"
        )
        self.large_changes_controls_container_id = (
            f"vl-large-changes-controls-container-{self.module_number}"
        )
        self.negative_nopost_controls_container_id = (
            f"vl-negative-nopost-controls-container-{self.module_number}"
        )
        self.nr_controls_container_id = (
            f"vl-nr-controls-container-{self.module_number}"
        )
        self.opposite_controls_container_id = (
            f"vl-opposite-controls-container-{self.module_number}"
        )
        self.breakdown_controls_container_id = (
            f"vl-breakdown-controls-container-{self.module_number}"
        )
        self.moms_controls_container_id = (
            f"vl-moms-controls-container-{self.module_number}"
        )
        self.movement_controls_container_id = (
            f"vl-movement-controls-container-{self.module_number}"
        )
        self.method_controls_container_id = (
            f"vl-method-controls-container-{self.module_number}"
        )

        # Output elements
        self.graph_title_id = (
            f"vl-graph-title-{self.module_number}"
        )
        self.graph_description_id = (
            f"vl-graph-description-{self.module_number}"
        )
        self.graph_id = (
            f"vl-graph-{self.module_number}"
        )
        self.graph_container_id = (
            f"vl-graph-container-{self.module_number}"
        )
        self.table_id = (
            f"vl-table-{self.module_number}"
        )
        self.table_container_id = (
            f"vl-table-container-{self.module_number}"
        )

        self.large_changes_summary_id = (
            f"vl-large-changes-summary-{self.module_number}"
        )

        self.status_id = (
            f"vl-status-{self.module_number}"
        )
        self.graph_section_id = (
            f"vl-graph-section-{self.module_number}"
        )

        self.module_layout = self._create_layout()

        self.module_callbacks()
        module_validator(self)

    # ========================================================================
    # Layout construction
    # ========================================================================

    def _create_layout(self) -> html.Div:
        """
        Build the complete Dash layout for all VL visualisations.

        Controls for every visualisation are created once and placed in
        dedicated containers. Callbacks toggle those containers instead of
        rebuilding the layout when the selected visualisation changes.
        """
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
                                        TREND_SINGLE_LABEL,
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
                                            "repeat(auto-fit, minmax(240px, 1fr))"
                                        ),
                                        "gap": "16px",
                                        "marginBottom": "16px",
                                        "alignItems": "start",
                                    },
                                    children=[
                                        # -------------------------------------------------
                                        # Trend-analysis controls
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.single_naring_container_id,
                                            children=[
                                                html.Label("Næring"),
                                                dcc.Dropdown(
                                                    id=self.naring_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            id=self.multi_naring_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("N2-gruppe"),
                                                dcc.Dropdown(
                                                    id=self.multi_naring_group_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value="45",
                                                    clearable=True,
                                                    searchable=True,
                                                    placeholder="Velg en N2-gruppe",
                                                ),
                                                html.Label(
                                                    "Næringer",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.multi_naring_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value=[],
                                                    multi=True,
                                                    clearable=True,
                                                    searchable=True,
                                                    placeholder="Velg eller søk etter næringer",
                                                ),
                                            ],
                                        ),
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

                                        # -------------------------------------------------
                                        # Enterprise trend
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.enterprise_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Organisasjonsnummer"),
                                                dcc.Input(
                                                    id=self.enterprise_id,
                                                    type="text",
                                                    value="817209882",
                                                    placeholder="Skriv inn orgnr_foretak",
                                                    debounce=True,
                                                    style={
                                                        "width": "100%",
                                                        "marginBottom": "12px",
                                                    },
                                                ),
                                                html.Label("Eller søk etter navn"),
                                                dcc.Dropdown(
                                                    id=self.enterprise_name_search_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value=None,
                                                    placeholder=(
                                                        "Skriv minst to tegn i foretaksnavnet"
                                                    ),
                                                    clearable=True,
                                                    searchable=True,
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Change share
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.change_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.change_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Antall største foretak",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.change_top_n_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {"label": "5", "value": 5},
                                                        {"label": "10", "value": 10},
                                                        {"label": "15", "value": 15},
                                                        {"label": "20", "value": 20},
                                                    ],
                                                    value=10,
                                                    clearable=False,
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # NØKU table
                                        # -------------------------------------------------

                                        html.Div(
                                            id=self.noku_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Gruppe"),
                                                dcc.Dropdown(
                                                    id=self.noku_group_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Alle grupper",
                                                            "value": "Alle",
                                                        },
                                                        {
                                                            "label": "Industri",
                                                            "value": "Industri",
                                                        },
                                                        {
                                                            "label": "Varehandel",
                                                            "value": "Varehandel",
                                                        },
                                                        {
                                                            "label": "Bygg",
                                                            "value": "Bygg",
                                                        },
                                                        {
                                                            "label": "Tjenesteyting",
                                                            "value": "Tjenesteyting",
                                                        },
                                                    ],
                                                    value="Alle",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "År",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.noku_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Grense for prosentvis endring",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.noku_rate_id,
                                                    type="number",
                                                    value=20,
                                                    min=0,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                                html.Label(
                                                    "Historisk vindu",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.noku_window_id,
                                                    type="number",
                                                    value=5,
                                                    min=2,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                                html.Label(
                                                    "Antall standardavvik",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.noku_standard_deviations_id,
                                                    type="number",
                                                    value=2.5,
                                                    min=0,
                                                    step=0.1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Large changes
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.large_changes_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.large_changes_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringsnivå",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.large_changes_group_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {"label": "N2", "value": "n2"},
                                                        {"label": "N3", "value": "n3"},
                                                        {"label": "N4", "value": "n4"},
                                                        {"label": "N5", "value": "n5"},
                                                        {"label": "Næring", "value": "naring"},
                                                        {
                                                            "label": "Næring 1",
                                                            "value": "naring_1",
                                                        },
                                                    ],
                                                    value="n3",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringskode",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.large_changes_group_value_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Variabel",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.large_changes_variables_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value=None,
                                                    multi=False,
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Fylke",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.large_changes_fylke_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Hele landet",
                                                            "value": "Land",
                                                        }
                                                    ],
                                                    value="Land",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Antall rader",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.large_changes_top_n_id,
                                                    type="number",
                                                    value=50,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Negative NO posts
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.negative_nopost_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.negative_nopost_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Grupper",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.RadioItems(
                                                    id=self.negative_nopost_group_level_id,
                                                    className="ssb-radio-buttons",
                                                    options=[
                                                        {
                                                            "label": "5-siffer",
                                                            "value": "naring",
                                                        },
                                                        {
                                                            "label": "2-siffer",
                                                            "value": "naring_2",
                                                        },
                                                    ],
                                                    value="naring",
                                                    inline=True,
                                                ),
                                                html.Label(
                                                    "Negativ grense",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.negative_nopost_threshold_id,
                                                    type="number",
                                                    value=1000,
                                                    min=0,
                                                    step=100,
                                                    style={"width": "100%"},
                                                ),
                                                dcc.Checklist(
                                                    id=self.negative_nopost_hide_columns_id,
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Skjul kolonner uten negative verdier"
                                                            ),
                                                            "value": "hide",
                                                        }
                                                    ],
                                                    value=["hide"],
                                                    style={"marginTop": "12px"},
                                                ),
                                                html.Label(
                                                    "Maks antall rader",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.negative_nopost_max_rows_id,
                                                    type="number",
                                                    value=300,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # NR controls
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.nr_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.nr_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringsnivå",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.nr_group_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Næring 2",
                                                            "value": "naring_2",
                                                        },
                                                        {
                                                            "label": "Næring 3",
                                                            "value": "naring_3",
                                                        },
                                                        {
                                                            "label": "Næring 4",
                                                            "value": "naring_4",
                                                        },
                                                        {
                                                            "label": "Detaljert næring",
                                                            "value": "naring",
                                                        },
                                                    ],
                                                    value="naring",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Visning",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.RadioItems(
                                                    id=self.nr_view_id,
                                                    className="ssb-radio-buttons",
                                                    options=[
                                                        {"label": "Land", "value": "Land"},
                                                        {"label": "Fylke", "value": "Fylke"},
                                                    ],
                                                    value="Land",
                                                ),
                                                html.Label(
                                                    "Negativ grense",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.nr_threshold_id,
                                                    type="number",
                                                    value=1000,
                                                    min=0,
                                                    step=100,
                                                    style={"width": "100%"},
                                                ),
                                                dcc.Checklist(
                                                    id=self.nr_hide_columns_id,
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Skjul kontroller uten negative verdier"
                                                            ),
                                                            "value": "hide",
                                                        }
                                                    ],
                                                    value=["hide"],
                                                    style={"marginTop": "12px"},
                                                ),
                                                html.Label(
                                                    "Maks antall rader",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.nr_max_rows_id,
                                                    type="number",
                                                    value=300,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Opposite direction
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.opposite_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("År"),
                                                dcc.Dropdown(
                                                    id=self.opposite_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringsnivå",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.opposite_group_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "2-siffer næring",
                                                            "value": "naring_2",
                                                        },
                                                        {
                                                            "label": "3-siffer næring",
                                                            "value": "naring_4",
                                                        },
                                                        {
                                                            "label": "4-siffer næring",
                                                            "value": "naring_5",
                                                        },
                                                        {
                                                            "label": "Detaljert næring",
                                                            "value": "naring",
                                                        },
                                                    ],
                                                    value="naring_4",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Visning",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.RadioItems(
                                                    id=self.opposite_view_id,
                                                    className="ssb-radio-buttons",
                                                    options=[
                                                        {"label": "Land", "value": "Land"},
                                                        {"label": "Fylke", "value": "Fylke"},
                                                    ],
                                                    value="Land",
                                                ),
                                                html.Label(
                                                    "Kontrollregel",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.opposite_rule_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Begge regler",
                                                            "value": "both",
                                                        },
                                                        {
                                                            "label": (
                                                                "Produksjonsverdi mot produktinnsats"
                                                            ),
                                                            "value": "production-input",
                                                        },
                                                        {
                                                            "label": (
                                                                "Forbruk mot varekostnad"
                                                            ),
                                                            "value": "consumption-p4005",
                                                        },
                                                    ],
                                                    value="both",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Minimum antall bedrifter",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.opposite_min_count_id,
                                                    type="number",
                                                    value=50,
                                                    min=0,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                                html.Label(
                                                    "Minimum prosentgap",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.opposite_gap_threshold_id,
                                                    type="number",
                                                    value=10,
                                                    min=0,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                                html.Label(
                                                    "Minimum absolutt endring",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.opposite_absolute_threshold_id,
                                                    type="number",
                                                    value=0,
                                                    min=0,
                                                    step=100,
                                                    style={"width": "100%"},
                                                ),
                                                html.Label(
                                                    "Maks antall rader",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.opposite_max_rows_id,
                                                    type="number",
                                                    value=300,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),
                                        # -------------------------------------------------
                                        # Breakdown
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.breakdown_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Analysenivå"),
                                                dcc.RadioItems(
                                                    id=self.breakdown_analysis_level_id,
                                                    className="ssb-radio-buttons",
                                                    options=[
                                                        {
                                                            "label": "Næring",
                                                            "value": "industry",
                                                        },
                                                        {
                                                            "label": "Enkeltforetak",
                                                            "value": "enterprise",
                                                        },
                                                    ],
                                                    value="industry",
                                                    inline=True,
                                                ),

                                                html.Label(
                                                    "År",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.breakdown_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),

                                                # Existing industry-level controls
                                                html.Div(
                                                    id=self.breakdown_industry_controls_id,
                                                    style={
                                                        "display": "block",
                                                        "marginTop": "12px",
                                                    },
                                                    children=[
                                                        html.Label("Næringsnivå"),
                                                        dcc.Dropdown(
                                                            id=self.breakdown_group_level_id,
                                                            className="ssb-dropdown",
                                                            options=[
                                                                {
                                                                    "label": "N2",
                                                                    "value": "n2",
                                                                },
                                                                {
                                                                    "label": "N3",
                                                                    "value": "n3",
                                                                },
                                                                {
                                                                    "label": "N4",
                                                                    "value": "n4",
                                                                },
                                                                {
                                                                    "label": "Detaljert næring",
                                                                    "value": "naring",
                                                                },
                                                            ],
                                                            value="n4",
                                                            clearable=False,
                                                        ),

                                                        html.Label(
                                                            "Næringskode",
                                                            style={"marginTop": "12px"},
                                                        ),
                                                        dcc.Dropdown(
                                                            id=self.breakdown_group_value_id,
                                                            className="ssb-dropdown",
                                                            options=[],
                                                            clearable=False,
                                                        ),
                                                    ],
                                                ),

                                                # Enterprise-level breakdown controls
                                                html.Div(
                                                    id=self.breakdown_enterprise_controls_id,
                                                    style={
                                                        "display": "none",
                                                        "marginTop": "12px",
                                                    },
                                                    children=[
                                                        html.Label("Søk etter foretaksnavn"),
                                                        dcc.Dropdown(
                                                            id=self.breakdown_enterprise_search_id,
                                                            className="ssb-dropdown",
                                                            options=[],
                                                            value=None,
                                                            placeholder=(
                                                                "Skriv minst to tegn i foretaksnavnet"
                                                            ),
                                                            clearable=True,
                                                            searchable=True,
                                                        ),

                                                        html.Label(
                                                            "Organisasjonsnummer",
                                                            style={"marginTop": "12px"},
                                                        ),
                                                        dcc.Input(
                                                            id=self.breakdown_enterprise_id,
                                                            type="text",
                                                            value="",
                                                            placeholder="Skriv inn orgnr_foretak",
                                                            debounce=True,
                                                            style={"width": "100%"},
                                                        ),

                                                        html.Label(
                                                            "Vis nivå",
                                                            style={"marginTop": "12px"},
                                                        ),
                                                        dcc.RadioItems(
                                                            id=self.breakdown_unit_level_id,
                                                            className="ssb-radio-buttons",
                                                            options=[
                                                                {
                                                                    "label": "Begge",
                                                                    "value": "both",
                                                                },
                                                                {
                                                                    "label": "Kun foretak",
                                                                    "value": "enterprise",
                                                                },
                                                                {
                                                                    "label": "Kun bedrift",
                                                                    "value": "business",
                                                                },
                                                            ],
                                                            value="both",
                                                        ),

                                                        html.Label(
                                                            "Bedrift",
                                                            style={"marginTop": "12px"},
                                                        ),
                                                        dcc.Dropdown(
                                                            id=self.breakdown_business_id,
                                                            className="ssb-dropdown",
                                                            options=[],
                                                            value=None,
                                                            clearable=False,
                                                            searchable=True,
                                                            placeholder="Velg bedrift",
                                                        ),
                                                    ],
                                                ),

                                                html.Label(
                                                    "Sammensatt variabel",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.breakdown_variable_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Omsetning",
                                                            "value": "omsetning",
                                                        },
                                                        {
                                                            "label": "Driftskostnader",
                                                            "value": "nopost_driftskostnader",
                                                        },
                                                        {
                                                            "label": "Produktinnsats",
                                                            "value": "produktinnsats",
                                                        },
                                                        {
                                                            "label": "Produksjonsverdi",
                                                            "value": "produksjonsverdi",
                                                        },
                                                        {
                                                            "label": "Bearbeidingsverdi",
                                                            "value": "bearbeidingsverdi",
                                                        },
                                                    ],
                                                    value="omsetning",
                                                    clearable=False,
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # MOMS
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.moms_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Næringsnivå"),
                                                dcc.Dropdown(
                                                    id=self.moms_group_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {"label": "N2", "value": "n2"},
                                                        {"label": "N3", "value": "n3"},
                                                        {"label": "N4", "value": "n4"},
                                                        {"label": "N5", "value": "n5"},
                                                    ],
                                                    value="n2",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringer",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.moms_naring_filter_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value=[],
                                                    multi=True,
                                                    clearable=True,
                                                    searchable=True,
                                                    placeholder=(
                                                        "Søk, for eksempel 47, og velg næringer"
                                                    ),
                                                ),
                                                html.Label(
                                                    "Tidligere år",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.moms_previous_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Nåværende år",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.moms_current_year_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Movement
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.movement_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Retning"),
                                                dcc.RadioItems(
                                                    id=self.movement_direction_id,
                                                    className="ssb-radio-buttons",
                                                    options=[
                                                        {
                                                            "label": "Tilgang",
                                                            "value": "tilgang",
                                                        },
                                                        {
                                                            "label": "Avgang",
                                                            "value": "avgang",
                                                        },
                                                    ],
                                                    value="tilgang",
                                                ),
                                                html.Label(
                                                    "Variabel",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.movement_variable_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Omsetning",
                                                            "value": "omsetning",
                                                        },
                                                        {
                                                            "label": "Sysselsetting",
                                                            "value": "sysselsetting_syss",
                                                        },
                                                    ],
                                                    value="omsetning",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringsnivå",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.movement_group_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {"label": "N2", "value": "n2"},
                                                        {"label": "N3", "value": "n3"},
                                                        {"label": "N4", "value": "n4"},
                                                        {"label": "N5", "value": "n5"},
                                                    ],
                                                    value="n2",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringsfilter",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.movement_code_filter_id,
                                                    type="text",
                                                    value="",
                                                    placeholder="Eksempel: 47",
                                                    debounce=True,
                                                    style={"width": "100%"},
                                                ),
                                                dcc.Checklist(
                                                    id=self.movement_exact_match_id,
                                                    options=[
                                                        {
                                                            "label": "Krev eksakt kode",
                                                            "value": "exact",
                                                        }
                                                    ],
                                                    value=[],
                                                    style={"marginTop": "12px"},
                                                ),
                                                html.Label(
                                                    "Antall rader",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Input(
                                                    id=self.movement_top_n_id,
                                                    type="number",
                                                    value=100,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100%"},
                                                ),
                                            ],
                                        ),

                                        # -------------------------------------------------
                                        # Method analysis
                                        # -------------------------------------------------
                                        html.Div(
                                            id=self.method_controls_container_id,
                                            style={"display": "none"},
                                            children=[
                                                html.Label("Næringsnivå"),
                                                dcc.Dropdown(
                                                    id=self.method_naring_level_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Næring 2",
                                                            "value": "naring_2",
                                                        },
                                                        {
                                                            "label": "Næring 4",
                                                            "value": "naring_4",
                                                        },
                                                        {
                                                            "label": "Næring 5",
                                                            "value": "naring_5",
                                                        },
                                                        {
                                                            "label": "Detaljert næring",
                                                            "value": "naring",
                                                        },
                                                    ],
                                                    value="naring_4",
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Næringskode",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.method_naring_value_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    clearable=False,
                                                ),
                                                html.Label(
                                                    "Rater",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.method_ratios_id,
                                                    className="ssb-dropdown",
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Salgsinntekt / omsetning"
                                                            ),
                                                            "value": "salgsint_rate",
                                                        },
                                                        {
                                                            "label": (
                                                                "Forbruk / varekostnad"
                                                            ),
                                                            "value": "forbruk_rate",
                                                        },
                                                        {
                                                            "label": (
                                                                "Vikarutgifter / lønnskostnader"
                                                            ),
                                                            "value": "vikar_rate",
                                                        },
                                                    ],
                                                    value=[
                                                        "salgsint_rate",
                                                        "forbruk_rate",
                                                    ],
                                                    multi=True,
                                                    clearable=True,
                                                ),
                                                html.Label(
                                                    "Registreringstyper",
                                                    style={"marginTop": "12px"},
                                                ),
                                                dcc.Dropdown(
                                                    id=self.method_reg_types_id,
                                                    className="ssb-dropdown",
                                                    options=[],
                                                    value=[],
                                                    multi=True,
                                                    clearable=True,
                                                    placeholder="Alle registreringstyper",
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
                                html.Div(
                                    id=self.graph_container_id,
                                    style={
                                        "display": "block",
                                        "width": "100%",
                                    },
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
                                html.Div(
                                    id=self.table_container_id,
                                    style={
                                        "display": "none",
                                        "width": "100%",
                                        "padding": "16px",
                                    },
                                    children=[
                                        html.Div(
                                            id=self.large_changes_summary_id,
                                            style={
                                                "display": "none",
                                                "marginBottom": "16px",
                                            },
                                        ),
                                        dash_table.DataTable(
                                            id=self.table_id,
                                            data=[],
                                            columns=[],
                                            page_size=25,
                                            sort_action="native",
                                            filter_action="native",
                                            page_action="native",
                                            export_format="csv",
                                            export_headers="display",
                                            merge_duplicate_headers=True,
                                            style_table={
                                                "overflowX": "auto",
                                                "overflowY": "auto",
                                                "maxHeight": "72vh",
                                                "border": "1px solid #d9d9d9",
                                            },
                                            style_header={
                                                "fontWeight": "bold",
                                                "backgroundColor": "#f3f4f6",
                                                "border": "1px solid #d9d9d9",
                                                "whiteSpace": "normal",
                                            },
                                            style_cell={
                                                "padding": "8px",
                                                "textAlign": "left",
                                                "fontFamily": (
                                                    "system-ui, -apple-system, "
                                                    "Segoe UI, Roboto, Arial"
                                                ),
                                                "fontSize": "13px",
                                                "minWidth": "110px",
                                                "width": "140px",
                                                "maxWidth": "320px",
                                                "whiteSpace": "normal",
                                                "height": "auto",
                                                "border": "1px solid #e5e7eb",
                                            },
                                            style_data_conditional=[],
                                            tooltip_data=[],
                                            tooltip_duration=None,
                                        ),
                                        html.Div(
                                            id=self.negative_nopost_drilldown_container_id,
                                            style={
                                                "display": "none",
                                                "marginTop": "24px",
                                                "paddingTop": "20px",
                                                "borderTop": "1px solid #d9d9d9",
                                            },
                                            children=[
                                                html.H3(
                                                    "Undersøk en negativ celle",
                                                    style={"marginBottom": "16px"},
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "grid",
                                                        "gridTemplateColumns": (
                                                            "minmax(260px, 2fr) "
                                                            "minmax(220px, 1fr) "
                                                            "minmax(160px, 1fr)"
                                                        ),
                                                        "gap": "16px",
                                                        "alignItems": "end",
                                                        "marginBottom": "16px",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            children=[
                                                                html.Label("Rad"),
                                                                dcc.Dropdown(
                                                                    id=self.negative_nopost_selected_group_id,
                                                                    className="ssb-dropdown",
                                                                    options=[],
                                                                    value=None,
                                                                    clearable=False,
                                                                    placeholder="Velg næringsgruppe",
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            children=[
                                                                html.Label("Variabel"),
                                                                dcc.Dropdown(
                                                                    id=self.negative_nopost_variable_id,
                                                                    className="ssb-dropdown",
                                                                    options=[],
                                                                    value=None,
                                                                    clearable=False,
                                                                    placeholder="Velg negativ NO-post",
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            children=[
                                                                html.Label("Antall foretak"),
                                                                dcc.Input(
                                                                    id=self.negative_nopost_top_enterprises_id,
                                                                    type="number",
                                                                    value=50,
                                                                    min=1,
                                                                    max=500,
                                                                    step=10,
                                                                    style={"width": "100%"},
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    id=self.negative_nopost_drilldown_message_id,
                                                    style={
                                                        "marginBottom": "12px",
                                                        "fontSize": "13px",
                                                    },
                                                ),
                                                dash_table.DataTable(
                                                    id=self.negative_nopost_drilldown_table_id,
                                                    data=[],
                                                    columns=[],
                                                    page_size=25,
                                                    sort_action="native",
                                                    filter_action="native",
                                                    page_action="native",
                                                    export_format="csv",
                                                    export_headers="display",
                                                    style_table={
                                                        "overflowX": "auto",
                                                        "overflowY": "auto",
                                                        "maxHeight": "55vh",
                                                        "border": "1px solid #d9d9d9",
                                                    },
                                                    style_header={
                                                        "fontWeight": "bold",
                                                        "backgroundColor": "#f3f4f6",
                                                        "border": "1px solid #d9d9d9",
                                                        "whiteSpace": "normal",
                                                    },
                                                    style_cell={
                                                        "padding": "8px",
                                                        "textAlign": "left",
                                                        "fontFamily": (
                                                            "system-ui, -apple-system, "
                                                            "Segoe UI, Roboto, Arial"
                                                        ),
                                                        "fontSize": "13px",
                                                        "minWidth": "110px",
                                                        "width": "140px",
                                                        "maxWidth": "320px",
                                                        "whiteSpace": "normal",
                                                        "height": "auto",
                                                        "border": "1px solid #e5e7eb",
                                                    },
                                                    style_data_conditional=[],
                                                    tooltip_data=[],
                                                    tooltip_duration=None,
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            id=self.nr_drilldown_container_id,
                                            style={
                                                "display": "none",
                                                "marginTop": "24px",
                                                "paddingTop": "20px",
                                                "borderTop": "1px solid #d9d9d9",
                                            },
                                            children=[
                                                html.H3(
                                                    "Undersøk en negativ NR-kontroll",
                                                    style={"marginBottom": "16px"},
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "grid",
                                                        "gridTemplateColumns": (
                                                            "minmax(260px, 2fr) "
                                                            "minmax(220px, 1fr) "
                                                            "minmax(160px, 1fr)"
                                                        ),
                                                        "gap": "16px",
                                                        "alignItems": "end",
                                                        "marginBottom": "16px",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            children=[
                                                                html.Label("Rad"),
                                                                dcc.Dropdown(
                                                                    id=self.nr_selected_group_id,
                                                                    className="ssb-dropdown",
                                                                    options=[],
                                                                    value=None,
                                                                    clearable=False,
                                                                    placeholder="Velg næring",
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            children=[
                                                                html.Label("Kontroll"),
                                                                dcc.Dropdown(
                                                                    id=self.nr_variable_id,
                                                                    className="ssb-dropdown",
                                                                    options=[],
                                                                    value=None,
                                                                    clearable=False,
                                                                    placeholder="Velg negativ kontroll",
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            children=[
                                                                html.Label("Antall foretak"),
                                                                dcc.Input(
                                                                    id=self.nr_top_enterprises_id,
                                                                    type="number",
                                                                    value=50,
                                                                    min=1,
                                                                    max=500,
                                                                    step=10,
                                                                    style={"width": "100%"},
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    id=self.nr_drilldown_message_id,
                                                    style={
                                                        "marginBottom": "12px",
                                                        "fontSize": "13px",
                                                    },
                                                ),
                                                dash_table.DataTable(
                                                    id=self.nr_drilldown_table_id,
                                                    data=[],
                                                    columns=[],
                                                    page_size=25,
                                                    sort_action="native",
                                                    filter_action="native",
                                                    page_action="native",
                                                    export_format="csv",
                                                    export_headers="display",
                                                    style_table={
                                                        "overflowX": "auto",
                                                        "overflowY": "auto",
                                                        "maxHeight": "55vh",
                                                        "border": "1px solid #d9d9d9",
                                                    },
                                                    style_header={
                                                        "fontWeight": "bold",
                                                        "backgroundColor": "#f3f4f6",
                                                        "border": "1px solid #d9d9d9",
                                                        "whiteSpace": "normal",
                                                    },
                                                    style_cell={
                                                        "padding": "8px",
                                                        "textAlign": "left",
                                                        "fontFamily": (
                                                            "system-ui, -apple-system, "
                                                            "Segoe UI, Roboto, Arial"
                                                        ),
                                                        "fontSize": "13px",
                                                        "minWidth": "110px",
                                                        "width": "140px",
                                                        "maxWidth": "320px",
                                                        "whiteSpace": "normal",
                                                        "height": "auto",
                                                        "border": "1px solid #e5e7eb",
                                                    },
                                                    style_data_conditional=[],
                                                    tooltip_data=[],
                                                    tooltip_duration=None,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
            

    # ========================================================================
    # Dataset resolution and cached readers
    # ========================================================================

    def _parquet_path(
        self,
        data_version: str,
        dataset: str = "agg_naring4",
    ) -> str:
        """
        Resolve a logical VL dataset to its physical parquet path.

        Keeping path resolution outside the framework allows the same module
        to run against different storage layouts and environments.
        """
        return self.file_path_resolver(
            data_version,
            dataset,
        )


    @staticmethod
    @lru_cache(maxsize=4)
    def _read_data(parquet_path: str) -> pd.DataFrame:
        """
        Read, validate and cache the aggregated industry dataset.

        The cache key is the resolved parquet path, so consolidated and
        unconsolidated files are cached independently.
        """
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
        """
        Read, validate and cache the enterprise-level VL dataset.

        Organisation numbers are normalised to strings because parquet readers
        may otherwise expose identifier columns as floating-point values.
        """
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
    def _read_enterprise_lookup(
        parquet_path: str,
    ) -> pd.DataFrame:
        """
        Create and cache one searchable row per enterprise.

        The latest available non-missing name is retained for
        each organisation number.
        """
        df = VLModule._read_enterprise_data(
            parquet_path
        )

        if "navn" not in df.columns:
            return pd.DataFrame(
                columns=[
                    "orgnr_foretak",
                    "navn",
                    "search_text",
                ]
            )

        lookup = df.loc[
            df["navn"].notna(),
            [
                "orgnr_foretak",
                "year",
                "navn",
            ],
        ].copy()

        lookup["navn"] = (
            lookup["navn"]
            .astype(str)
            .str.strip()
        )

        lookup["orgnr_foretak"] = (
            lookup["orgnr_foretak"]
            .astype(str)
            .str.strip()
        )

        lookup = lookup.loc[
            lookup["navn"].ne("")
        ].copy()

        # Keep one searchable row per enterprise. The most recent available name
        # is preferred because enterprise names can change over time.
        lookup = (
            lookup.sort_values(
                "year",
                ascending=False,
            )
            .drop_duplicates(
                subset="orgnr_foretak",
                keep="first",
            )
            .reset_index(drop=True)
        )

        # Precompute a case-folded search field once per parquet path. Dropdown
        # callbacks can then perform cheap substring matching on every keypress.
        lookup["search_text"] = (
            lookup["navn"].str.casefold()
            + " "
            + lookup["orgnr_foretak"].str.casefold()
        )

        return lookup[
            [
                "orgnr_foretak",
                "navn",
                "search_text",
            ]
        ]
    @staticmethod
    @lru_cache(maxsize=4)
    def _read_business_data(
        parquet_path: str,
    ) -> pd.DataFrame:
        """
        Read, validate and cache the business-level VL dataset.

        Enterprise and business organisation numbers are normalised to stable
        string identifiers before the data is reused by callbacks.
        """
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
    @lru_cache(maxsize=12)
    def _read_generic_data(
        parquet_path: str,
    ) -> pd.DataFrame:
        """
        Read and cache a VL dataset without applying a fixed schema contract.

        This reader is used for specialised datasets such as MOMS and movement
        data, which have schemas that differ from the core aggregate, business
        and enterprise files.
        """
        df = pd.read_parquet(parquet_path)

        return df.copy()


    @staticmethod
    # ========================================================================
    # Figure builders
    # ========================================================================

    def _empty_figure(message: str) -> go.Figure:
        """Return a blank Plotly figure containing a user-facing message."""
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

        # Centre the interval for year t on the observed value from year t - 1.
        # Lagging annual changes prevents the current observation from affecting
        # the control limits against which that observation is evaluated.
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
        """
        Plot several variables through time for one selected industry.

        Values are displayed on a shared axis and are not rebased or indexed;
        users should therefore compare variables with compatible magnitudes.
        """
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
        """
        Plot one variable through time for several selected industries.

        Each industry is rendered as a separate trace using the same variable
        definition and year axis.
        """
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
        """
        Plot one variable through time for a selected enterprise.

        Enterprise rows are expected to have been normalised by
        ``_read_enterprise_data`` before this function is called.
        """
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
        """
        Show which enterprises contribute most to an annual industry change.

        Business rows are first aggregated to enterprise level. The chart uses
        absolute changes to calculate slice sizes while retaining signed change
        values in the hover information. Enterprises outside ``top_n`` are
        combined into a single ``Andre foretak`` category.
        """
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

    @staticmethod
    # ========================================================================
    # Analysis and table-data builders
    # ========================================================================

    def _create_noku_table_data(
        aggregate_df: pd.DataFrame,
        business_df: pd.DataFrame, 
        year: int,
        rate: float = 20.0,
        window: int = 5,
        standard_deviations: float = 2.5,
        naring_col: str = "naring_4",
    ) -> pd.DataFrame:
        """
        Identify large industry changes and explain their main contributors.

        For each supported variable, the selected year is compared with the
        previous year and evaluated against historical variation. Changes above
        ``rate`` are retained. When the historical control interval is breached,
        the largest contributing business and enterprise are identified from
        the underlying business dataset.

        The rolling expectation uses lagged changes, ensuring that the change
        being evaluated does not influence its own reference interval.
        """
        variables = [
            "omsetning",
            "nopost_driftskostnader",
            "ts_forbruk",
            "ts_salgsint",
            "bearbeidingsverdi",
            "produksjonsverdi",
            "produktinnsats",
        ]

        required_aggregate_columns = {
            "year",
            naring_col,
        }

        required_business_columns = {
            "year",
            naring_col,
            "orgnr_foretak",
            "orgnr_bedrift",
        }

        missing_aggregate = required_aggregate_columns.difference(
            aggregate_df.columns
        )
        missing_business = required_business_columns.difference(
            business_df.columns
        )

        if missing_aggregate:
            raise ValueError(
                "Aggregert datasett mangler kolonnene "
                f"{sorted(missing_aggregate)}."
            )

        if missing_business:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_business)}."
            )

        available_variables = [
            variable
            for variable in variables
            if variable in aggregate_df.columns
            and variable in business_df.columns
        ]

        if not available_variables:
            raise ValueError(
                "Fant ingen kontrollvariabler som finnes i begge datasettene."
            )

        aggregate = aggregate_df.copy()
        businesses = business_df.copy()

        aggregate["year"] = pd.to_numeric(
            aggregate["year"],
            errors="coerce",
        )
        businesses["year"] = pd.to_numeric(
            businesses["year"],
            errors="coerce",
        )

        aggregate[naring_col] = aggregate[naring_col].astype(str)
        businesses[naring_col] = businesses[naring_col].astype(str)

        businesses["orgnr_foretak"] = (
            businesses["orgnr_foretak"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
        )
        businesses["orgnr_bedrift"] = (
            businesses["orgnr_bedrift"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
        )

        all_results: list[pd.DataFrame] = []

        for variable in available_variables:
            analysis = aggregate[
                [
                    "year",
                    naring_col,
                    variable,
                ]
            ].copy()

            analysis[variable] = pd.to_numeric(
                analysis[variable],
                errors="coerce",
            )

            analysis = analysis.sort_values(
                [
                    naring_col,
                    "year",
                ]
            ).reset_index(drop=True)

            analysis["previous_value"] = (
                analysis.groupby(naring_col)[variable]
                .shift(1)
            )

            analysis["change"] = (
                analysis[variable]
                - analysis["previous_value"]
            )

            # Use only changes known before the evaluated year. This avoids
            # allowing a potential outlier to widen its own historical limits.
            lagged_change = (
                analysis.groupby(naring_col)["change"]
                .shift(1)
            )

            analysis["expected_change"] = (
                lagged_change.groupby(analysis[naring_col])
                .rolling(
                    window=window,
                    min_periods=2,
                )
                .mean()
                .reset_index(
                    level=0,
                    drop=True,
                )
            )

            analysis["change_standard_deviation"] = (
                lagged_change.groupby(analysis[naring_col])
                .rolling(
                    window=window,
                    min_periods=2,
                )
                .std()
                .reset_index(
                    level=0,
                    drop=True,
                )
                .abs()
            )

            analysis["expected_value"] = (
                analysis["previous_value"]
                + analysis["expected_change"]
            )

            analysis["percentage_change"] = (
                analysis["change"]
                / analysis["previous_value"]
                * 100
            )

            analysis["percentage_change"] = (
                analysis["percentage_change"]
                .replace(
                    [
                        np.inf,
                        -np.inf,
                    ],
                    np.nan,
                )
            )

            analysis["z_score"] = (
                analysis["change"]
                - analysis["expected_change"]
            ) / analysis["change_standard_deviation"]

            analysis["z_score"] = analysis["z_score"].replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )

            analysis["large_change"] = (
                analysis["percentage_change"].abs()
                > float(rate)
            )

            lower_limit = (
                analysis["expected_value"]
                - float(standard_deviations)
                * analysis["change_standard_deviation"]
            )

            upper_limit = (
                analysis["expected_value"]
                + float(standard_deviations)
                * analysis["change_standard_deviation"]
            )

            analysis["breach"] = (
                analysis["change_standard_deviation"].notna()
                & (
                    (analysis[variable] < lower_limit)
                    | (analysis[variable] > upper_limit)
                )
            )

            selected = analysis.loc[
                (analysis["year"] == int(year))
                & analysis["large_change"],
            ].copy()

            if selected.empty:
                continue

            selected["variable"] = variable
            selected["largest_business"] = ""
            selected["largest_enterprise"] = ""
            selected["business_contribution"] = np.nan
            selected["business_contribution_pct"] = np.nan
            selected["enterprise_contribution"] = np.nan
            selected["enterprise_contribution_pct"] = np.nan
            selected["explanation"] = ""

            for row_index, row in selected.iterrows():
                industry = str(row[naring_col])
                total_change = row["change"]

                if not bool(row["breach"]):
                    z_score = row["z_score"]

                    z_text = (
                        f"{z_score:.1f}"
                        if pd.notna(z_score)
                        else "ukjent"
                    )

                    selected.at[
                        row_index,
                        "explanation",
                    ] = (
                        f"Endring på "
                        f"{row['percentage_change']:.1f} %. "
                        f"Endringen er {z_text} standardavvik "
                        "fra historisk forventning, men bryter "
                        "ikke kontrollgrensen."
                    )

                    continue

                business_subset = businesses.loc[
                    (
                        businesses[naring_col].astype(str)
                        == industry
                    )
                    & businesses["year"].isin(
                        [
                            int(year) - 1,
                            int(year),
                        ]
                    ),
                    [
                        column
                        for column in [
                            "year",
                            "orgnr_foretak",
                            "orgnr_bedrift",
                            "navn",
                            variable,
                        ]
                        if column in businesses.columns
                    ],
                ].copy()

                if business_subset.empty:
                    selected.at[
                        row_index,
                        "explanation",
                    ] = (
                        "Avvik, men ingen bedriftsdata ble funnet "
                        "for de to aktuelle årene."
                    )
                    continue

                business_subset[variable] = pd.to_numeric(
                    business_subset[variable],
                    errors="coerce",
                )

                business_values = (
                    business_subset.groupby(
                        [
                            "orgnr_foretak",
                            "orgnr_bedrift",
                            "year",
                        ],
                        as_index=False,
                        dropna=False,
                    )[variable]
                    .sum(min_count=1)
                )

                business_wide = business_values.pivot_table(
                    index=[
                        "orgnr_foretak",
                        "orgnr_bedrift",
                    ],
                    columns="year",
                    values=variable,
                    aggfunc="sum",
                ).reset_index()

                previous_year = int(year) - 1
                current_year = int(year)

                if previous_year not in business_wide.columns:
                    business_wide[previous_year] = 0

                if current_year not in business_wide.columns:
                    business_wide[current_year] = 0

                business_wide["contribution"] = (
                    business_wide[current_year].fillna(0)
                    - business_wide[previous_year].fillna(0)
                )

                if business_wide["contribution"].dropna().empty:
                    selected.at[
                        row_index,
                        "explanation",
                    ] = (
                        "Avvik, men det var ikke mulig å beregne "
                        "bidrag fra bedriftene."
                    )
                    continue

                if pd.notna(total_change) and total_change < 0:
                    largest_business_row = business_wide.loc[
                        business_wide["contribution"].idxmin()
                    ]
                else:
                    largest_business_row = business_wide.loc[
                        business_wide["contribution"].idxmax()
                    ]

                enterprise_values = (
                    business_wide.groupby(
                        "orgnr_foretak",
                        as_index=False,
                        dropna=False,
                    )["contribution"]
                    .sum(min_count=1)
                )

                if pd.notna(total_change) and total_change < 0:
                    largest_enterprise_row = enterprise_values.loc[
                        enterprise_values["contribution"].idxmin()
                    ]
                else:
                    largest_enterprise_row = enterprise_values.loc[
                        enterprise_values["contribution"].idxmax()
                    ]

                business_contribution = largest_business_row[
                    "contribution"
                ]
                enterprise_contribution = largest_enterprise_row[
                    "contribution"
                ]

                if pd.notna(total_change) and total_change != 0:
                    business_percentage = (
                        business_contribution
                        / total_change
                        * 100
                    )
                    enterprise_percentage = (
                        enterprise_contribution
                        / total_change
                        * 100
                    )
                else:
                    business_percentage = np.nan
                    enterprise_percentage = np.nan

                largest_business = (
                    f"{largest_business_row['orgnr_bedrift']} "
                    f"(foretak "
                    f"{largest_business_row['orgnr_foretak']})"
                )

                largest_enterprise = str(
                    largest_enterprise_row["orgnr_foretak"]
                )

                selected.at[
                    row_index,
                    "largest_business",
                ] = largest_business

                selected.at[
                    row_index,
                    "largest_enterprise",
                ] = largest_enterprise

                selected.at[
                    row_index,
                    "business_contribution",
                ] = business_contribution

                selected.at[
                    row_index,
                    "business_contribution_pct",
                ] = business_percentage

                selected.at[
                    row_index,
                    "enterprise_contribution",
                ] = enterprise_contribution

                selected.at[
                    row_index,
                    "enterprise_contribution_pct",
                ] = enterprise_percentage

                selected.at[
                    row_index,
                    "explanation",
                ] = (
                    f"Avvik. Total endring: {total_change:,.0f}. "
                    f"Største bedrift bidrar med "
                    f"{business_contribution:,.0f} "
                    f"({business_percentage:.1f} %). "
                    f"Største foretak bidrar med "
                    f"{enterprise_contribution:,.0f} "
                    f"({enterprise_percentage:.1f} %)."
                )

            all_results.append(selected)

        output_columns = [
            naring_col,
            "variable",
            "percentage_change",
            "z_score",
            "breach",
            "largest_business",
            "largest_enterprise",
            "explanation",
            "business_contribution",
            "business_contribution_pct",
            "enterprise_contribution",
            "enterprise_contribution_pct",
        ]

        if not all_results:
            return pd.DataFrame(
                columns=output_columns
            )

        result = pd.concat(
            all_results,
            ignore_index=True,
        )

        result = result.sort_values(
            [
                naring_col,
                "variable",
            ]
        ).reset_index(drop=True)

        return result[output_columns]

    @staticmethod
    @lru_cache(maxsize=8)
    def _get_nace_section_mapping(
        year: int,
    ) -> dict[str, str]:
        """
        Return the official two-digit industry-code-to-section mapping.

        Klass classification 6 is the Standard Industrial Classification.
        The lookup is date-specific, allowing Klass to resolve the
        classification version that applies to the selected year.

        Results are cached by year so callbacks do not repeatedly request and
        transform the same Klass data.
        """
        klass_data = KlassClassification(6).get_codes(
            f"{int(year)}-12-31"
        ).data

        required_columns = {
            "level",
            "code",
            "parentCode",
        }

        missing_columns = required_columns.difference(
            klass_data.columns
        )

        if missing_columns:
            raise ValueError(
                "Klass-data mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        level_two = klass_data.loc[
            klass_data["level"].astype(str) == "2",
            [
                "code",
                "parentCode",
            ],
        ].copy()

        level_two["code"] = (
            level_two["code"]
            .astype(str)
            .str.strip()
            .str.zfill(2)
        )

        level_two["parentCode"] = (
            level_two["parentCode"]
            .astype(str)
            .str.strip()
        )

        level_two = level_two.loc[
            level_two["code"].ne("")
            & level_two["parentCode"].ne("")
        ].drop_duplicates(
            subset="code",
            keep="last",
        )

        return dict(
            zip(
                level_two["code"],
                level_two["parentCode"],
                strict=True,
            )
        )

    @staticmethod
    def _classify_noku_group(
        naring_value: Any,
        year: int,
    ) -> str:
        """
        Map an industry code to the operational NØKU grouping.

        Klass supplies the official relationship between two-digit industry
        codes and classification sections. NØKU-specific exceptions are kept
        locally because the operational groups do not correspond exactly to
        the official sections.

        Specific code-prefix exceptions are evaluated before the broader
        Klass-based section mapping. This ordering is significant and must be
        preserved.
        """
        if pd.isna(naring_value):
            return "Ikke klassifisert"

        code = str(naring_value).strip()

        if not code or code.lower() == "nan":
            return "Ikke klassifisert"

        # -------------------------------------------------------------
        # NØKU-specific exceptions
        # -------------------------------------------------------------
        # These rules do not follow directly from the official section
        # hierarchy and must therefore remain explicit.
        if code.startswith("09.1"):
            return "Varehandel"

        if code.startswith("09.9"):
            return "Industri"

        if code.startswith(
            (
                "50.101",
                "50.102",
                "50.109",
                "50.201",
                "50.202",
                "50.203",
                "50.204",
                "50.230",
            )
        ):
            return "Industri"

        # The NØKU table is currently aggregated at the three-digit level,
        # so the detailed 50-codes above normally appear as 50.1 or 50.2.
        if code.startswith(
            (
                "50.1",
                "50.2",
            )
        ):
            return "Industri"

        # Other 50-codes were not included in the previous NØKU mapping.
        if code.startswith("50"):
            return "Ikke klassifisert"

        # Code 09 is split by the detailed exceptions above. Any remaining
        # 09-code stays unclassified, matching the previous implementation.
        if code.startswith("09"):
            return "Ikke klassifisert"

        # Explicit operational assignments that differ from a simple
        # section-to-group relationship.
        if code.startswith("52"):
            return "Industri"

        if code.startswith("53"):
            return "Industri"

        if code.startswith(
            (
                "86",
                "87",
                "88",
            )
        ):
            return "Varehandel"

        two_digit_code = code[:2]

        section_mapping = (
            VLModule._get_nace_section_mapping(
                int(year)
            )
        )

        section = section_mapping.get(
            two_digit_code
        )

        # The broad section mapping reproduces the previous NØKU grouping.
        # Exceptions that split a section are handled above.
        section_to_noku_group = {
            "B": "Industri",
            "C": "Industri",
            "D": "Industri",
            "E": "Tjenesteyting",
            "F": "Bygg",
            "G": "Varehandel",
            "H": "Industri",
            "I": "Bygg",
            "J": "Tjenesteyting",
            "L": "Bygg",
            "M": "Tjenesteyting",
            "N": "Tjenesteyting",
            "P": "Bygg",
            "Q": "Varehandel",
            "R": "Tjenesteyting",
            "S": "Tjenesteyting",
        }

        # Section B contains code 06, which belongs to Varehandel in the
        # operational NØKU grouping rather than Industri.
        if two_digit_code == "06":
            return "Varehandel"

        return section_to_noku_group.get(
            section,
            "Ikke klassifisert",
        )

    @staticmethod
    def _create_large_changes_data(
        df: pd.DataFrame,
        year: int,
        group_level: str,
        group_value: str,
        variables: list[str],
        *,
        fylke: str | None = None,
        top_n: int = 50,
        drop_missing: bool = True,
    ) -> pd.DataFrame:
        """
        Create a ranked table of the largest year-over-year business changes.

        The selected industry group is derived from the detailed industry code.
        Current-year business rows are matched to previous-year values using the
        enterprise and business organisation numbers together as the unit key.
        One output row is produced per selected variable.

        Parameters such as county, row limit and missing-value handling are
        applied before the result is formatted for the shared Dash table.
        """
        required_columns = {
            "year",
            "naring",
            "orgnr_foretak",
            "orgnr_bedrift",
        }

        missing_columns = required_columns.difference(df.columns)

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        if not variables:
            return pd.DataFrame()

        missing_variables = [
            variable
            for variable in variables
            if variable not in df.columns
        ]

        if missing_variables:
            raise ValueError(
                "Bedriftsdatasettet mangler variablene "
                f"{sorted(missing_variables)}."
            )

        valid_group_levels = {
            "n2",
            "n3",
            "n4",
            "n5",
            "naring",
            "naring_1",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        if "antall" in data.columns:
            data = data.drop(columns=["antall"])

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.loc[
            data["year"].isin(
                [
                    int(year) - 1,
                    int(year),
                ]
            )
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["year"] = data["year"].astype(int)
        data["naring"] = data["naring"].astype("string")

        for column in [
            "orgnr_foretak",
            "orgnr_bedrift",
        ]:
            data[column] = (
                data[column]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
            )

        if fylke is not None and fylke != "Land":
            if "fylke" not in data.columns:
                raise ValueError(
                    "Fylkesfilter er valgt, men datasettet "
                    "mangler kolonnen 'fylke'."
                )

            data["fylke"] = data["fylke"].astype("string")

            data = data.loc[
                data["fylke"] == str(fylke)
            ].copy()

        if group_level == "naring_1":
            if "naring_1" not in data.columns:
                raise ValueError(
                    "Datasettet mangler kolonnen 'naring_1'."
                )

            data["group_value"] = (
                data["naring_1"]
                .astype("string")
            )

        elif group_level == "naring":
            data["group_value"] = data["naring"]

        else:
            slice_lengths = {
                "n2": 2,
                "n3": 4,
                "n4": 5,
                "n5": 6,
            }

            data["group_value"] = (
                data["naring"]
                .str.slice(
                    0,
                    slice_lengths[group_level],
                )
            )

        data = data.loc[
            data["group_value"].astype(str)
            == str(group_value)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        for variable in variables:
            data[variable] = pd.to_numeric(
                data[variable],
                errors="coerce",
            )

        key_columns = [
            "orgnr_foretak",
            "orgnr_bedrift",
        ]

        information_columns = [
            column
            for column in [
                "sfnr",
                "orgnr_foretak",
                "orgnr_bedrift",
                "navn",
                "type",
                "reg_type",
                "fylke",
                "naring",
                "naring_f",
            ]
            if column in data.columns
        ]

        current_year = int(year)
        previous_year = current_year - 1

        current = data.loc[
            data["year"] == current_year
        ].copy()

        previous = data.loc[
            data["year"] == previous_year
        ].copy()

        if current.empty or previous.empty:
            return pd.DataFrame()

        id_columns = list(
            dict.fromkeys(
                information_columns
                + key_columns
            )
        )

        keep_columns = list(
            dict.fromkeys(
                id_columns
                + ["year"]
                + variables
            )
        )

        current = current[keep_columns].copy()
        previous = previous[keep_columns].copy()

        current = current.rename(
            columns={
                variable: f"{variable}_current"
                for variable in variables
            }
        )

        previous = previous.rename(
            columns={
                variable: f"{variable}_previous"
                for variable in variables
            }
        )

        # Match each current business to one previous-year record. The combined
        # enterprise/business key identifies the statistical business unit.
        previous_values = (
            previous[
                key_columns
                + [
                    f"{variable}_previous"
                    for variable in variables
                ]
            ]
            .drop_duplicates(
                subset=key_columns,
                keep="last",
            )
        )

        merged = current.merge(
            previous_values,
            on=key_columns,
            how="left",
            validate="m:1",
        )

        if "naring" in data.columns:
            previous_naring = (
                previous[
                    key_columns
                    + ["naring"]
                ]
                .drop_duplicates(
                    subset=key_columns,
                    keep="last",
                )
                .rename(
                    columns={
                        "naring": "naring_previous"
                    }
                )
            )

            merged = merged.merge(
                previous_naring,
                on=key_columns,
                how="left",
                validate="m:1",
            )

        if "naring_f" in data.columns:
            previous_naring_f = (
                previous[
                    key_columns
                    + ["naring_f"]
                ]
                .drop_duplicates(
                    subset=key_columns,
                    keep="last",
                )
                .rename(
                    columns={
                        "naring_f": "naring_f_previous"
                    }
                )
            )

            merged = merged.merge(
                previous_naring_f,
                on=key_columns,
                how="left",
                validate="m:1",
            )

        result_rows: list[pd.DataFrame] = []

        for variable in variables:
            current_column = f"{variable}_current"
            previous_column = f"{variable}_previous"

            columns = list(id_columns)

            for extra_column in [
                "naring_previous",
                "naring_f_previous",
            ]:
                if (
                    extra_column in merged.columns
                    and extra_column not in columns
                ):
                    columns.append(extra_column)

            columns.extend(
                [
                    previous_column,
                    current_column,
                ]
            )

            variable_result = merged[columns].copy()

            variable_result = variable_result.rename(
                columns={
                    previous_column: "value_previous",
                    current_column: "value_current",
                }
            )

            variable_result["variable"] = variable

            variable_result["value_previous"] = pd.to_numeric(
                variable_result["value_previous"],
                errors="coerce",
            )

            variable_result["value_current"] = pd.to_numeric(
                variable_result["value_current"],
                errors="coerce",
            )

            variable_result["change"] = (
                variable_result["value_current"]
                - variable_result["value_previous"]
            )

            variable_result["absolute_change"] = (
                variable_result["change"].abs()
            )

            variable_result["percentage_change"] = np.where(
                variable_result["value_previous"].notna()
                & variable_result["value_previous"].ne(0),
                (
                    variable_result["change"]
                    / variable_result["value_previous"]
                    * 100
                ),
                np.nan,
            )

            change_values = (
                variable_result["change"]
                .to_numpy()
            )

            variable_result["direction"] = np.select(
                [
                    np.isfinite(change_values)
                    & (change_values > 0),
                    np.isfinite(change_values)
                    & (change_values < 0),
                ],
                [
                    "⬆️",
                    "⬇️",
                ],
                default="→",
            )

            result_rows.append(variable_result)

        if not result_rows:
            return pd.DataFrame()

        result = pd.concat(
            result_rows,
            ignore_index=True,
        )

        if drop_missing:
            result = result.dropna(
                subset=[
                    "value_previous",
                    "value_current",
                ]
            )

        result = (
            result.sort_values(
                "absolute_change",
                ascending=False,
                na_position="last",
            )
            .head(max(int(top_n), 1))
            .reset_index(drop=True)
        )

        ordered_columns: list[str] = []

        for column in information_columns:
            if column == "naring":
                ordered_columns.append("naring")

                if "naring_previous" in result.columns:
                    ordered_columns.append(
                        "naring_previous"
                    )

            elif column == "naring_f":
                ordered_columns.append("naring_f")

                if "naring_f_previous" in result.columns:
                    ordered_columns.append(
                        "naring_f_previous"
                    )

            else:
                ordered_columns.append(column)

        ordered_columns.extend(
            [
                "variable",
                "value_previous",
                "value_current",
                "change",
                "absolute_change",
                "percentage_change",
                "direction",
            ]
        )

        ordered_columns = [
            column
            for column in dict.fromkeys(
                ordered_columns
            )
            if column in result.columns
        ]

        return result[ordered_columns]

    @staticmethod
    def _create_large_changes_summary_data(
        df: pd.DataFrame,
        year: int,
        group_level: str,
        group_value: str,
        variable: str,
        *,
        fylke: str | None = None,
    ) -> tuple[
        dict[str, Any],
        pd.DataFrame,
    ]:
        """
        Create YoY totals and any special ratio analysis for
        the Store endringer summary card.
        """
        required_columns = {
            "year",
            "naring",
            variable,
        }

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "n2",
            "n3",
            "n4",
            "n5",
            "naring",
            "naring_1",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        current_year = int(year)
        previous_year = current_year - 1

        data = data.loc[
            data["year"].isin(
                [
                    previous_year,
                    current_year,
                ]
            )
        ].copy()

        if data.empty:
            return {}, pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        if fylke is not None and fylke != "Land":
            if "fylke" not in data.columns:
                raise ValueError(
                    "Fylkesfilter er valgt, men datasettet "
                    "mangler kolonnen 'fylke'."
                )

            data["fylke"] = data["fylke"].astype(
                "string"
            )

            data = data.loc[
                data["fylke"] == str(fylke)
            ].copy()

        if group_level == "naring_1":
            if "naring_1" not in data.columns:
                raise ValueError(
                    "Datasettet mangler kolonnen "
                    "'naring_1'."
                )

            data["group_value"] = (
                data["naring_1"].astype("string")
            )

        elif group_level == "naring":
            data["group_value"] = data["naring"]

        else:
            slice_lengths = {
                "n2": 2,
                "n3": 4,
                "n4": 5,
                "n5": 6,
            }

            data["group_value"] = (
                data["naring"]
                .str.slice(
                    0,
                    slice_lengths[group_level],
                )
            )

        data = data.loc[
            data["group_value"].astype(str)
            == str(group_value)
        ].copy()

        if data.empty:
            return {}, pd.DataFrame()

        data[variable] = pd.to_numeric(
            data[variable],
            errors="coerce",
        )

        previous = data.loc[
            data["year"] == previous_year
        ].copy()

        current = data.loc[
            data["year"] == current_year
        ].copy()

        previous_total = previous[variable].sum(
            min_count=1
        )

        current_total = current[variable].sum(
            min_count=1
        )

        if (
            pd.notna(previous_total)
            and pd.notna(current_total)
        ):
            absolute_change = (
                current_total
                - previous_total
            )
        else:
            absolute_change = np.nan

        if (
            pd.notna(previous_total)
            and previous_total != 0
            and pd.notna(absolute_change)
        ):
            percentage_change = (
                absolute_change
                / previous_total
                * 100
            )

        elif (
            pd.notna(previous_total)
            and previous_total == 0
            and pd.notna(current_total)
            and current_total != 0
        ):
            percentage_change = np.inf

        else:
            percentage_change = np.nan

        summary = {
            "variable": variable,
            "previous_year": previous_year,
            "current_year": current_year,
            "previous_total": previous_total,
            "current_total": current_total,
            "absolute_change": absolute_change,
            "percentage_change": percentage_change,
            "group_level": group_level,
            "group_value": str(group_value),
            "fylke": fylke or "Land",
        }

        ratio_definition: tuple[
            str,
            str,
            str,
        ] | None = None

        if variable == "ts_salgsint":
            ratio_definition = (
                "ts_salgsint",
                "omsetning",
                "ts_salgsint / omsetning",
            )

        elif variable == "ts_forbruk":
            ratio_definition = (
                "ts_forbruk",
                "nopost_p4005",
                "ts_forbruk / nopost_p4005",
            )

        elif variable == "ts_vikarutgifter":
            ratio_definition = (
                "ts_vikarutgifter",
                "nopost_lonnskostnader",
                (
                    "ts_vikarutgifter / "
                    "nopost_lonnskostnader"
                ),
            )

        elif variable.endswith("_akt"):
            ratio_definition = (
                variable,
                "basisx",
                f"{variable} / basisx",
            )

        elif variable.endswith("_utg"):
            ratio_definition = (
                variable,
                "nopost_driftskostnader",
                (
                    f"{variable} / "
                    "nopost_driftskostnader"
                ),
            )

        if ratio_definition is None:
            return summary, pd.DataFrame()

        numerator, denominator, ratio_label = (
            ratio_definition
        )

        if denominator not in data.columns:
            summary["ratio_error"] = (
                f"Kan ikke beregne {ratio_label}: "
                f"kolonnen {denominator} mangler."
            )

            return summary, pd.DataFrame()

        for column in [
            numerator,
            denominator,
        ]:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        has_type = "type" in data.columns
        has_reg_type = "reg_type" in data.columns

        if has_type:
            data["type"] = data["type"].astype(
                "string"
            )

        if has_reg_type:
            data["reg_type"] = data[
                "reg_type"
            ].astype("string")

        # Compute each ratio as sum(numerator) / sum(denominator). Averaging
        # unit-level ratios would overweight observations with small denominators.
        def calculate_ratio_row(
            label: str,
            previous_subset: pd.DataFrame,
            current_subset: pd.DataFrame,
        ) -> dict[str, Any]:
            previous_numerator = (
                previous_subset[numerator].sum(
                    min_count=1
                )
            )

            previous_denominator = (
                previous_subset[denominator].sum(
                    min_count=1
                )
            )

            current_numerator = (
                current_subset[numerator].sum(
                    min_count=1
                )
            )

            current_denominator = (
                current_subset[denominator].sum(
                    min_count=1
                )
            )

            if (
                pd.notna(previous_denominator)
                and previous_denominator != 0
            ):
                previous_ratio = (
                    previous_numerator
                    / previous_denominator
                )
            else:
                previous_ratio = np.nan

            if (
                pd.notna(current_denominator)
                and current_denominator != 0
            ):
                current_ratio = (
                    current_numerator
                    / current_denominator
                )
            else:
                current_ratio = np.nan

            if (
                pd.notna(previous_ratio)
                and pd.notna(current_ratio)
            ):
                percentage_point_change = (
                    current_ratio
                    - previous_ratio
                ) * 100
            else:
                percentage_point_change = np.nan

            return {
                "group": label,
                "previous_numerator": (
                    previous_numerator
                ),
                "previous_denominator": (
                    previous_denominator
                ),
                "previous_ratio": previous_ratio,
                "current_numerator": (
                    current_numerator
                ),
                "current_denominator": (
                    current_denominator
                ),
                "current_ratio": current_ratio,
                "percentage_point_change": (
                    percentage_point_change
                ),
                "ratio_label": ratio_label,
            }

        ratio_rows: list[dict[str, Any]] = []

        if has_type and has_reg_type:
            previous_type_s = (
                previous["type"] == "S"
            )

            current_type_s = (
                current["type"] == "S"
            )

            previous_reg_02 = (
                previous["reg_type"] == "02"
            )

            current_reg_02 = (
                current["reg_type"] == "02"
            )

            ratio_groups = [
                (
                    "type = S og reg_type = 02",
                    previous.loc[
                        previous_type_s
                        & previous_reg_02
                    ],
                    current.loc[
                        current_type_s
                        & current_reg_02
                    ],
                ),
                (
                    "type ≠ S og reg_type = 02",
                    previous.loc[
                        ~previous_type_s
                        & previous_reg_02
                    ],
                    current.loc[
                        ~current_type_s
                        & current_reg_02
                    ],
                ),
                (
                    "type = S og reg_type ≠ 02",
                    previous.loc[
                        previous_type_s
                        & ~previous_reg_02
                    ],
                    current.loc[
                        current_type_s
                        & ~current_reg_02
                    ],
                ),
                (
                    "type ≠ S og reg_type ≠ 02",
                    previous.loc[
                        ~previous_type_s
                        & ~previous_reg_02
                    ],
                    current.loc[
                        ~current_type_s
                        & ~current_reg_02
                    ],
                ),
                (
                    "Totalt",
                    previous,
                    current,
                ),
            ]

        elif has_type:
            ratio_groups = [
                (
                    "type = S",
                    previous.loc[
                        previous["type"] == "S"
                    ],
                    current.loc[
                        current["type"] == "S"
                    ],
                ),
                (
                    "type ≠ S",
                    previous.loc[
                        previous["type"] != "S"
                    ],
                    current.loc[
                        current["type"] != "S"
                    ],
                ),
                (
                    "Totalt",
                    previous,
                    current,
                ),
            ]

        else:
            ratio_groups = [
                (
                    "Totalt",
                    previous,
                    current,
                ),
            ]

        for (
            label,
            previous_subset,
            current_subset,
        ) in ratio_groups:
            ratio_rows.append(
                calculate_ratio_row(
                    label=label,
                    previous_subset=previous_subset,
                    current_subset=current_subset,
                )
            )

        ratio_df = pd.DataFrame(
            ratio_rows
        )

        return summary, ratio_df

    @staticmethod
    def _create_large_changes_summary_card(
        summary: dict[str, Any],
        ratio_df: pd.DataFrame,
    ) -> html.Div:
        """
        Build the summary card shown above the ``Store endringer`` table.

        The card displays previous and current totals, absolute and percentage
        change, and—where applicable—ratio analysis by unit and registration
        type. Ratios are based on aggregated numerators and denominators rather
        than averages of row-level ratios.
        """

        if not summary:
            return html.Div()

        def format_number(
            value: Any,
        ) -> str:
            if pd.isna(value):
                return "NA"

            try:
                return f"{float(value):,.0f}".replace(
                    ",",
                    " ",
                )
            except (
                TypeError,
                ValueError,
            ):
                return str(value)

        def format_percentage(
            value: Any,
        ) -> str:
            if pd.isna(value):
                return "NA"

            if value == np.inf:
                return "+∞"

            if value == -np.inf:
                return "-∞"

            return f"{float(value):+.2f} %"

        def format_ratio(
            value: Any,
        ) -> str:
            if pd.isna(value):
                return "NA"

            return f"{float(value):.4f}"

        def format_percentage_points(
            value: Any,
        ) -> str:
            if pd.isna(value):
                return "NA"

            return f"{float(value):+.2f} pp"

        percentage_change = summary.get(
            "percentage_change"
        )

        if (
            pd.notna(percentage_change)
            and percentage_change > 0
        ):
            direction_symbol = "⬆️"
            direction_colour = "#166534"

        elif (
            pd.notna(percentage_change)
            and percentage_change < 0
        ):
            direction_symbol = "⬇️"
            direction_colour = "#991b1b"

        else:
            direction_symbol = "→"
            direction_colour = "#525252"

        previous_year = summary.get(
            "previous_year"
        )

        current_year = summary.get(
            "current_year"
        )

        variable = summary.get(
            "variable",
            "",
        )

        group_level = summary.get(
            "group_level",
            "",
        )

        group_value = summary.get(
            "group_value",
            "",
        )

        fylke = summary.get(
            "fylke",
            "Land",
        )

        summary_line = html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": (
                    "minmax(180px, 1.5fr) "
                    "repeat(4, minmax(120px, 1fr))"
                ),
                "gap": "12px",
                "alignItems": "center",
                "padding": "10px 0",
                "borderTop": "1px solid #e5e7eb",
            },
            children=[
                html.Div(
                    variable,
                    style={
                        "fontWeight": "600",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            str(previous_year),
                            style={
                                "fontSize": "12px",
                                "color": "#666",
                            },
                        ),
                        html.Strong(
                            format_number(
                                summary.get(
                                    "previous_total"
                                )
                            )
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div(
                            str(current_year),
                            style={
                                "fontSize": "12px",
                                "color": "#666",
                            },
                        ),
                        html.Strong(
                            format_number(
                                summary.get(
                                    "current_total"
                                )
                            )
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div(
                            "Endring",
                            style={
                                "fontSize": "12px",
                                "color": "#666",
                            },
                        ),
                        html.Strong(
                            format_number(
                                summary.get(
                                    "absolute_change"
                                )
                            )
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Span(
                            direction_symbol,
                            style={
                                "marginRight": "6px",
                            },
                        ),
                        html.Strong(
                            format_percentage(
                                percentage_change
                            )
                        ),
                    ],
                    style={
                        "textAlign": "right",
                        "color": direction_colour,
                        "fontSize": "17px",
                    },
                ),
            ],
        )

        card_children: list[Any] = [
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "gap": "16px",
                    "flexWrap": "wrap",
                    "alignItems": "baseline",
                },
                children=[
                    html.Div(
                        (
                            "Oppsummering av endring – "
                            f"{group_level} {group_value}"
                        ),
                        style={
                            "fontSize": "16px",
                            "fontWeight": "700",
                        },
                    ),
                    html.Div(
                        (
                            f"Fylke: {fylke} · "
                            f"{previous_year}–{current_year}"
                        ),
                        style={
                            "fontSize": "13px",
                            "color": "#666",
                        },
                    ),
                ],
            ),
            summary_line,
        ]

        ratio_error = summary.get(
            "ratio_error"
        )

        if ratio_error:
            card_children.append(
                html.Div(
                    ratio_error,
                    style={
                        "marginTop": "12px",
                        "padding": "10px 12px",
                        "border": "1px solid #fecaca",
                        "borderRadius": "8px",
                        "backgroundColor": "#fef2f2",
                        "color": "#991b1b",
                    },
                )
            )

        elif not ratio_df.empty:
            ratio_label = str(
                ratio_df["ratio_label"].iloc[0]
            )

            ratio_rows: list[Any] = [
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": (
                            "minmax(210px, 1.5fr) "
                            "repeat(3, minmax(150px, 1fr))"
                        ),
                        "gap": "10px",
                        "padding": "8px 0",
                        "fontWeight": "600",
                        "color": "#555",
                        "borderBottom": "1px solid #e5e7eb",
                    },
                    children=[
                        html.Div("Gruppe"),
                        html.Div(str(previous_year)),
                        html.Div(str(current_year)),
                        html.Div("Endring"),
                    ],
                )
            ]

            for row in ratio_df.itertuples(
                index=False
            ):
                ratio_rows.append(
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": (
                                "minmax(210px, 1.5fr) "
                                "repeat(3, minmax(150px, 1fr))"
                            ),
                            "gap": "10px",
                            "padding": "9px 0",
                            "borderBottom": (
                                "1px solid #f0f0f0"
                            ),
                            "alignItems": "start",
                        },
                        children=[
                            html.Div(
                                str(row.group),
                                style={
                                    "fontWeight": "600",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        (
                                            "Rate: "
                                            f"{format_ratio(row.previous_ratio)}"
                                        ),
                                        style={
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        (
                                            "Teller "
                                            f"{format_number(row.previous_numerator)} "
                                            "/ nevner "
                                            f"{format_number(row.previous_denominator)}"
                                        ),
                                        style={
                                            "fontSize": "12px",
                                            "color": "#666",
                                        },
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        (
                                            "Rate: "
                                            f"{format_ratio(row.current_ratio)}"
                                        ),
                                        style={
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        (
                                            "Teller "
                                            f"{format_number(row.current_numerator)} "
                                            "/ nevner "
                                            f"{format_number(row.current_denominator)}"
                                        ),
                                        style={
                                            "fontSize": "12px",
                                            "color": "#666",
                                        },
                                    ),
                                ]
                            ),
                            html.Div(
                                format_percentage_points(
                                    row.percentage_point_change
                                ),
                                style={
                                    "fontWeight": "600",
                                },
                            ),
                        ],
                    )
                )

            card_children.append(
                html.Div(
                    style={
                        "marginTop": "14px",
                        "padding": "12px",
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "10px",
                        "overflowX": "auto",
                    },
                    children=[
                        html.Div(
                            f"Rateanalyse: {ratio_label}",
                            style={
                                "fontWeight": "700",
                                "marginBottom": "6px",
                            },
                        ),
                        *ratio_rows,
                        html.Div(
                            (
                                "Raten beregnes som summen av "
                                "telleren delt på summen av nevneren "
                                "innenfor hver gruppe."
                            ),
                            style={
                                "marginTop": "8px",
                                "fontSize": "12px",
                                "color": "#666",
                            },
                        ),
                    ],
                )
            )

        return html.Div(
            style={
                "border": "1px solid #d9d9d9",
                "borderRadius": "12px",
                "padding": "14px 16px",
                "backgroundColor": "#fafafa",
                "boxShadow": (
                    "0 1px 2px rgba(0, 0, 0, 0.06)"
                ),
            },
            children=card_children,
        )

    @staticmethod
    def _create_negative_nopost_data(
        df: pd.DataFrame,
        year: int,
        group_level: str = "naring",
        *,
        negative_threshold: float = 1000,
        hide_nonnegative_columns: bool = True,
        max_rows: int = 300,
    ) -> pd.DataFrame:
        """
        Aggregate NO-posts by industry and retain materially negative results.

        A row is included when at least one eligible NO-post is below the
        negative threshold. Columns with no negative observations can be hidden
        to keep the control table focused.
        """
        required_columns = {
            "year",
            "naring",
            "orgnr_foretak",
        }

        missing_columns = required_columns.difference(df.columns)

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "naring_2",
            "naring",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.loc[
            data["year"] == int(year)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype("string")

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        if "naring_3" not in data.columns:
            data["naring_3"] = (
                data["naring"].str.slice(0, 4)
            )

        if "naring_4" not in data.columns:
            data["naring_4"] = (
                data["naring"].str.slice(0, 5)
            )

        nopost_prefixes = (
            "nopost_p3000",
            "nopost_p3100",
            "nopost_p3200",
            "nopost_p3700",
            "nopost_p3900",
            "nopost_p4005",
            "nopost_p5000",
            "nopost_p6300",
            "nopost_p6400",
            "nopost_p6500",
            "nopost_p6700",
            "nopost_p6995",
            "nopost_p7700",
        )

        excluded_columns = {
            "nopost_p3300",
            "nopost_p3400",
            "nopost_p3880",
            "nopost_p4295",
            "nopost_p4995",
        }

        nopost_columns = [
            column
            for column in data.columns
            if any(
                column.startswith(prefix)
                for prefix in nopost_prefixes
            )
            and column not in excluded_columns
        ]

        if not nopost_columns:
            raise ValueError(
                "Fant ingen NO-postkolonner som skal kontrolleres."
            )

        for column in nopost_columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        threshold = abs(float(negative_threshold))

        aggregated = (
            data.groupby(
                group_level,
                dropna=False,
            )[nopost_columns]
            .sum(min_count=1)
            .reset_index()
        )

        if aggregated.empty:
            return pd.DataFrame()

        negative_mask = (
            aggregated[nopost_columns]
            < -threshold
        ).any(axis=1)

        aggregated = aggregated.loc[
            negative_mask
        ].copy()

        if aggregated.empty:
            return pd.DataFrame()

        if hide_nonnegative_columns:
            displayed_nopost_columns = [
                column
                for column in nopost_columns
                if (
                    aggregated[column]
                    < -threshold
                ).any()
            ]
        else:
            displayed_nopost_columns = nopost_columns

        aggregated["_sort_value"] = (
            aggregated[displayed_nopost_columns]
            .min(axis=1)
        )

        aggregated = (
            aggregated.sort_values(
                "_sort_value",
                ascending=True,
            )
            .head(max(int(max_rows), 1))
            .drop(columns="_sort_value")
            .reset_index(drop=True)
        )

        ordered_columns = [
            group_level,
            *displayed_nopost_columns,
        ]

        return aggregated[ordered_columns]

    @staticmethod
    def _create_negative_nopost_drilldown_data(
        df: pd.DataFrame,
        year: int,
        group_level: str,
        group_value: str,
        variable: str,
        *,
        negative_threshold: float = 1000,
        top_enterprises: int = 50,
    ) -> pd.DataFrame:
        """
        Create an enterprise drilldown for one negative NO-post cell.

        Business rows are aggregated to enterprise level, filtered by the same
        threshold as the summary table and ranked from most negative upward.
        """

        required_columns = {
            "year",
            "naring",
            "orgnr_foretak",
            variable,
        }

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "naring_2",
            "naring",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.loc[
            data["year"] == int(year)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        data = data.loc[
            data[group_level].astype(str)
            == str(group_value)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["orgnr_foretak"] = (
            data["orgnr_foretak"]
            .astype("string")
            .str.replace(r"\.0$", "", regex=True)
        )

        if "orgnr_bedrift" in data.columns:
            data["orgnr_bedrift"] = (
                data["orgnr_bedrift"]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
            )

        data[variable] = pd.to_numeric(
            data[variable],
            errors="coerce",
        )

        contributions = (
            data.groupby(
                "orgnr_foretak",
                dropna=False,
            )[variable]
            .sum(min_count=1)
            .reset_index()
        )

        contributions[variable] = pd.to_numeric(
            contributions[variable],
            errors="coerce",
        )

        if "type" in data.columns:
            type_mapping = (
                data.dropna(subset=["type"])
                .groupby("orgnr_foretak")["type"]
                .agg(
                    lambda values: (
                        values.value_counts().index[0]
                        if len(values)
                        else pd.NA
                    )
                )
                .reset_index()
            )

            contributions = contributions.merge(
                type_mapping,
                on="orgnr_foretak",
                how="left",
            )

        else:
            contributions["type"] = pd.NA

        if "orgnr_bedrift" in data.columns:
            counts = (
                data.groupby(
                    "orgnr_foretak"
                )["orgnr_bedrift"]
                .nunique()
                .reset_index(
                    name="n_bedrifter"
                )
            )

        else:
            counts = (
                data.groupby(
                    "orgnr_foretak"
                )
                .size()
                .reset_index(
                    name="n_rows"
                )
            )

        contributions = contributions.merge(
            counts,
            on="orgnr_foretak",
            how="left",
        )

        threshold = abs(
            float(negative_threshold)
        )

        contributions = contributions.loc[
            contributions[variable] < -threshold
        ].copy()

        if contributions.empty:
            return pd.DataFrame()

        contributions = (
            contributions.sort_values(
                variable,
                ascending=True,
            )
            .head(
                max(
                    int(top_enterprises),
                    1,
                )
            )
            .reset_index(drop=True)
        )

        ordered_columns = [
            "orgnr_foretak",
            "type",
        ]

        if "n_bedrifter" in contributions.columns:
            ordered_columns.append(
                "n_bedrifter"
            )

        elif "n_rows" in contributions.columns:
            ordered_columns.append(
                "n_rows"
            )

        ordered_columns.append(variable)

        return contributions[
            ordered_columns
        ]

    @staticmethod
    def _create_nr_controls_data(
        df: pd.DataFrame,
        year: int,
        group_level: str = "naring",
        *,
        view: str = "Land",
        negative_threshold: float = 1000,
        hide_nonnegative_columns: bool = True,
        max_rows: int = 300,
    ) -> pd.DataFrame:
        """
        Calculate and aggregate NR logical-control residuals by industry.

        Residuals are derived from the underlying accounting variables before
        aggregation. Only groups with at least one value below the selected
        negative threshold are returned.
        """
        required_columns = {
            "year",
            "orgnr_foretak",
            "naring",
            "nopost_p4005",
            "ts_forbruk",
            "nopost_driftskostnader",
            "nopost_lonnskostnader",
            "produktinnsats",
            "omsetning",
            "ts_salgsint",
            "nopost_p3000",
            "nopost_p3100",
            "nopost_p3200",
            "nopost_p3300",
        }

        if view == "Fylke":
            required_columns.add("fylke")

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "naring_2",
            "naring_3",
            "naring_4",
            "naring",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        if view not in {"Land", "Fylke"}:
            raise ValueError(
                "View må være enten 'Land' eller 'Fylke'."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.loc[
            data["year"] == int(year)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        if "naring_3" not in data.columns:
            data["naring_3"] = (
                data["naring"].str.slice(0, 4)
            )

        if "naring_4" not in data.columns:
            data["naring_4"] = (
                data["naring"].str.slice(0, 5)
            )

        if view == "Fylke":
            data["fylke"] = data["fylke"].astype(
                "string"
            )

        numeric_inputs = [
            "nopost_p4005",
            "ts_forbruk",
            "nopost_driftskostnader",
            "nopost_lonnskostnader",
            "produktinnsats",
            "omsetning",
            "ts_salgsint",
            "nopost_p3000",
            "nopost_p3100",
            "nopost_p3200",
            "nopost_p3300",
        ]

        for column in numeric_inputs:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        data["p4005_forb"] = (
            data["nopost_p4005"]
            - data["ts_forbruk"]
        )

        data["dr_vk_lo"] = (
            data["nopost_driftskostnader"]
            - data["nopost_p4005"]
            - data["nopost_lonnskostnader"]
        )

        data["dr_forb_lo"] = (
            data["nopost_driftskostnader"]
            - data["ts_forbruk"]
            - data["nopost_lonnskostnader"]
        )

        data["prins_vk_forb"] = (
            data["produktinnsats"]
            - data["p4005_forb"]
        )

        data["oms_salgsint"] = (
            data["omsetning"]
            - data["ts_salgsint"]
        )

        data["nosalg_tssalg"] = (
            data["nopost_p3000"]
            + data["nopost_p3100"]
            + data["nopost_p3200"]
            - data["nopost_p3300"]
            - data["ts_salgsint"]
        )

        check_columns = [
            "p4005_forb",
            "dr_vk_lo",
            "dr_forb_lo",
            "prins_vk_forb",
            "oms_salgsint",
            "nosalg_tssalg",
        ]

        if (
            view == "Land"
            and "bearbeidingsverdi" in data.columns
        ):
            data["bearbeidingsverdi"] = pd.to_numeric(
                data["bearbeidingsverdi"],
                errors="coerce",
            )
            check_columns.append(
                "bearbeidingsverdi"
            )

        group_columns = [group_level]

        if view == "Fylke":
            group_columns.append("fylke")

        aggregated = (
            data.groupby(
                group_columns,
                dropna=False,
            )[check_columns]
            .sum(min_count=1)
            .reset_index()
        )

        if aggregated.empty:
            return pd.DataFrame()

        threshold = abs(float(negative_threshold))

        negative_mask = (
            aggregated[check_columns]
            < -threshold
        ).any(axis=1)

        aggregated = aggregated.loc[
            negative_mask
        ].copy()

        if aggregated.empty:
            return pd.DataFrame()

        if hide_nonnegative_columns:
            displayed_check_columns = [
                column
                for column in check_columns
                if (
                    aggregated[column]
                    < -threshold
                ).any()
            ]
        else:
            displayed_check_columns = check_columns

        aggregated["negative_check_count"] = (
            aggregated[displayed_check_columns]
            .lt(-threshold)
            .sum(axis=1)
        )

        aggregated["most_negative_value"] = (
            aggregated[displayed_check_columns]
            .min(axis=1)
        )

        aggregated = (
            aggregated.sort_values(
                "most_negative_value",
                ascending=True,
            )
            .head(max(int(max_rows), 1))
            .reset_index(drop=True)
        )

        ordered_columns = [
            *group_columns,
            *displayed_check_columns,
        ]

        return aggregated[ordered_columns]

    @staticmethod
    def _create_nr_drilldown_data(
        df: pd.DataFrame,
        year: int,
        group_level: str,
        group_value: str,
        check: str,
        *,
        view: str = "Land",
        fylke: str | None = None,
        negative_threshold: float = 1000,
        top_enterprises: int = 50,
    ) -> pd.DataFrame:
        """
        Create an enterprise-level drilldown for one negative NR control.

        The residual is recalculated from source variables using the same formula
        as the summary table, then aggregated and ranked by enterprise.
        """

        required_columns = {
            "year",
            "orgnr_foretak",
            "naring",
            "nopost_p4005",
            "ts_forbruk",
            "nopost_driftskostnader",
            "nopost_lonnskostnader",
            "produktinnsats",
            "omsetning",
            "ts_salgsint",
            "nopost_p3000",
            "nopost_p3100",
            "nopost_p3200",
            "nopost_p3300",
        }

        if view == "Fylke":
            required_columns.add("fylke")

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "naring_2",
            "naring_3",
            "naring_4",
            "naring",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        valid_checks = {
            "p4005_forb",
            "dr_vk_lo",
            "dr_forb_lo",
            "prins_vk_forb",
            "oms_salgsint",
            "nosalg_tssalg",
            "bearbeidingsverdi",
        }

        if check not in valid_checks:
            raise ValueError(
                f"Ugyldig NR-kontroll: {check}."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.loc[
            data["year"] == int(year)
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        if "naring_3" not in data.columns:
            data["naring_3"] = (
                data["naring"].str.slice(0, 4)
            )

        if "naring_4" not in data.columns:
            data["naring_4"] = (
                data["naring"].str.slice(0, 5)
            )

        data = data.loc[
            data[group_level].astype(str)
            == str(group_value)
        ].copy()

        if view == "Fylke":
            data["fylke"] = data["fylke"].astype(
                "string"
            )

            data = data.loc[
                data["fylke"].astype(str)
                == str(fylke)
            ].copy()

        if data.empty:
            return pd.DataFrame()

        data["orgnr_foretak"] = (
            data["orgnr_foretak"]
            .astype("string")
            .str.replace(r"\.0$", "", regex=True)
        )

        if "orgnr_bedrift" in data.columns:
            data["orgnr_bedrift"] = (
                data["orgnr_bedrift"]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
            )

        numeric_inputs = [
            "nopost_p4005",
            "ts_forbruk",
            "nopost_driftskostnader",
            "nopost_lonnskostnader",
            "produktinnsats",
            "omsetning",
            "ts_salgsint",
            "nopost_p3000",
            "nopost_p3100",
            "nopost_p3200",
            "nopost_p3300",
        ]

        if "bearbeidingsverdi" in data.columns:
            numeric_inputs.append(
                "bearbeidingsverdi"
            )

        for column in numeric_inputs:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        # Same residual formulas as the main NR table.
        data["p4005_forb"] = (
            data["nopost_p4005"]
            - data["ts_forbruk"]
        )

        data["dr_vk_lo"] = (
            data["nopost_driftskostnader"]
            - data["nopost_p4005"]
            - data["nopost_lonnskostnader"]
        )

        data["dr_forb_lo"] = (
            data["nopost_driftskostnader"]
            - data["ts_forbruk"]
            - data["nopost_lonnskostnader"]
        )

        data["prins_vk_forb"] = (
            data["produktinnsats"]
            - data["p4005_forb"]
        )

        data["oms_salgsint"] = (
            data["omsetning"]
            - data["ts_salgsint"]
        )

        data["nosalg_tssalg"] = (
            data["nopost_p3000"]
            + data["nopost_p3100"]
            + data["nopost_p3200"]
            - data["nopost_p3300"]
            - data["ts_salgsint"]
        )

        if check == "bearbeidingsverdi":
            if "bearbeidingsverdi" not in data.columns:
                raise ValueError(
                    "Datasettet mangler kolonnen "
                    "'bearbeidingsverdi'."
                )

        contributions = (
            data.groupby(
                "orgnr_foretak",
                dropna=False,
            )[check]
            .sum(min_count=1)
            .reset_index()
        )

        contributions[check] = pd.to_numeric(
            contributions[check],
            errors="coerce",
        )

        if "type" in data.columns:
            type_mapping = (
                data.dropna(subset=["type"])
                .groupby("orgnr_foretak")["type"]
                .agg(
                    lambda values: (
                        values.value_counts().index[0]
                        if len(values)
                        else pd.NA
                    )
                )
                .reset_index()
            )

            contributions = contributions.merge(
                type_mapping,
                on="orgnr_foretak",
                how="left",
            )

        else:
            contributions["type"] = pd.NA

        if "orgnr_bedrift" in data.columns:
            counts = (
                data.groupby(
                    "orgnr_foretak"
                )["orgnr_bedrift"]
                .nunique()
                .reset_index(
                    name="n_bedrifter"
                )
            )

        else:
            counts = (
                data.groupby(
                    "orgnr_foretak"
                )
                .size()
                .reset_index(
                    name="n_rows"
                )
            )

        contributions = contributions.merge(
            counts,
            on="orgnr_foretak",
            how="left",
        )

        threshold = abs(
            float(negative_threshold)
        )

        contributions = contributions.loc[
            contributions[check] < -threshold
        ].copy()

        if contributions.empty:
            return pd.DataFrame()

        contributions = (
            contributions.sort_values(
                check,
                ascending=True,
            )
            .head(
                max(
                    int(top_enterprises),
                    1,
                )
            )
            .reset_index(drop=True)
        )

        ordered_columns = [
            "orgnr_foretak",
            "type",
        ]

        if "n_bedrifter" in contributions.columns:
            ordered_columns.append(
                "n_bedrifter"
            )

        elif "n_rows" in contributions.columns:
            ordered_columns.append(
                "n_rows"
            )

        ordered_columns.append(check)

        return contributions[
            ordered_columns
        ]

    @staticmethod
    def _create_opposite_direction_data(
        df: pd.DataFrame,
        year: int,
        group_level: str = "naring_4",
        *,
        view: str = "Land",
        rule: str = "both",
        min_count: int = 50,
        gap_threshold_pct: float = 10.0,
        absolute_change_threshold: float = 0.0,
        max_rows: int = 300,
    ) -> pd.DataFrame:
        """
        Find industry groups where related variables move in opposite directions.

        The function compares production value with intermediate consumption and
        reported consumption with merchandise cost. Optional thresholds limit the
        result by business count, percentage gap and absolute change.
        """
        required_columns = {
            "year",
            "naring",
            "produksjonsverdi",
            "produktinnsats",
            "ts_forbruk",
            "nopost_p4005",
        }

        if view == "Fylke":
            required_columns.add("fylke")

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "naring_2",
            "naring_3",
            "naring_4",
            "naring_5",
            "naring",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        if view not in {"Land", "Fylke"}:
            raise ValueError(
                "View må være enten 'Land' eller 'Fylke'."
            )

        if rule not in {
            "both",
            "production-input",
            "consumption-p4005",
        }:
            raise ValueError(
                f"Ugyldig regelvalg: {rule}."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        previous_year = int(year) - 1
        current_year = int(year)

        data = data.loc[
            data["year"].isin(
                [
                    previous_year,
                    current_year,
                ]
            )
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        if "naring_3" not in data.columns:
            data["naring_3"] = (
                data["naring"].str.slice(0, 4)
            )

        if "naring_4" not in data.columns:
            data["naring_4"] = (
                data["naring"].str.slice(0, 5)
            )

        if "naring_5" not in data.columns:
            data["naring_5"] = (
                data["naring"].str.slice(0, 5)
            )

        if view == "Fylke":
            data["fylke"] = data["fylke"].astype(
                "string"
            )

        variables = [
            "produksjonsverdi",
            "produktinnsats",
            "ts_forbruk",
            "nopost_p4005",
        ]

        for variable in variables:
            data[variable] = pd.to_numeric(
                data[variable],
                errors="coerce",
            )

        group_columns = [group_level]

        if view == "Fylke":
            group_columns.append("fylke")

        if "orgnr_bedrift" in data.columns:
            counts = (
                data.groupby(
                    group_columns + ["year"],
                    dropna=False,
                )["orgnr_bedrift"]
                .nunique(dropna=True)
                .reset_index(name="count")
            )
        else:
            counts = (
                data.groupby(
                    group_columns + ["year"],
                    dropna=False,
                )
                .size()
                .reset_index(name="count")
            )

        aggregated_values = (
            data.groupby(
                group_columns + ["year"],
                dropna=False,
            )[variables]
            .sum(min_count=1)
            .reset_index()
        )

        aggregated = aggregated_values.merge(
            counts,
            on=group_columns + ["year"],
            how="left",
        )

        wide = aggregated.pivot_table(
            index=group_columns,
            columns="year",
            values=variables + ["count"],
            aggfunc="sum",
        )

        if wide.empty:
            return pd.DataFrame()

        wide.columns = [
            f"{variable}_{int(column_year)}"
            for variable, column_year in wide.columns
        ]

        wide = wide.reset_index()

        for variable in variables + ["count"]:
            for required_year in [
                previous_year,
                current_year,
            ]:
                column = f"{variable}_{required_year}"

                if column not in wide.columns:
                    wide[column] = np.nan

        wide["count"] = (
            wide[f"count_{current_year}"]
            .fillna(wide[f"count_{previous_year}"])
        )

        wide = wide.loc[
            wide["count"].fillna(0)
            >= max(int(min_count), 0)
        ].copy()

        if wide.empty:
            return pd.DataFrame()

        for variable in variables:
            previous_column = (
                f"{variable}_{previous_year}"
            )
            current_column = (
                f"{variable}_{current_year}"
            )

            delta_column = f"{variable}_change"
            pct_column = f"{variable}_percentage_change"
            direction_column = f"{variable}_direction"

            wide[delta_column] = (
                wide[current_column]
                - wide[previous_column]
            )

            wide[pct_column] = np.where(
                wide[previous_column].notna()
                & wide[previous_column].ne(0),
                (
                    wide[delta_column]
                    / wide[previous_column]
                    * 100
                ),
                np.nan,
            )

            wide[direction_column] = np.select(
                [
                    wide[delta_column] > 0,
                    wide[delta_column] < 0,
                ],
                [
                    "⬆️",
                    "⬇️",
                ],
                default="→",
            )

        production_sign = np.sign(
            wide["produksjonsverdi_change"]
        )

        input_sign = np.sign(
            wide["produktinnsats_change"]
        )

        consumption_sign = np.sign(
            wide["ts_forbruk_change"]
        )

        p4005_sign = np.sign(
            wide["nopost_p4005_change"]
        )

        wide["production_input_opposite"] = (
            production_sign * input_sign
            == -1
        )

        wide["consumption_p4005_opposite"] = (
            consumption_sign * p4005_sign
            == -1
        )

        absolute_threshold = abs(
            float(absolute_change_threshold)
        )

        if absolute_threshold > 0:
            wide["production_input_opposite"] = (
                wide["production_input_opposite"]
                & (
                    wide["produksjonsverdi_change"]
                    .abs()
                    > absolute_threshold
                )
                & (
                    wide["produktinnsats_change"]
                    .abs()
                    > absolute_threshold
                )
            )

            wide["consumption_p4005_opposite"] = (
                wide["consumption_p4005_opposite"]
                & (
                    wide["ts_forbruk_change"]
                    .abs()
                    > absolute_threshold
                )
                & (
                    wide["nopost_p4005_change"]
                    .abs()
                    > absolute_threshold
                )
            )

        wide["production_input_gap_pct"] = (
            wide[
                "produksjonsverdi_percentage_change"
            ].abs()
            + wide[
                "produktinnsats_percentage_change"
            ].abs()
        )

        wide["consumption_p4005_gap_pct"] = (
            wide[
                "ts_forbruk_percentage_change"
            ].abs()
            + wide[
                "nopost_p4005_percentage_change"
            ].abs()
        )

        gap_threshold = max(
            float(gap_threshold_pct),
            0.0,
        )

        if gap_threshold > 0:
            wide["production_input_opposite"] = (
                wide["production_input_opposite"]
                & (
                    wide["production_input_gap_pct"]
                    >= gap_threshold
                )
            )

            wide["consumption_p4005_opposite"] = (
                wide["consumption_p4005_opposite"]
                & (
                    wide["consumption_p4005_gap_pct"]
                    >= gap_threshold
                )
            )

        if rule == "production-input":
            wide = wide.loc[
                wide["production_input_opposite"]
            ].copy()

        elif rule == "consumption-p4005":
            wide = wide.loc[
                wide["consumption_p4005_opposite"]
            ].copy()

        else:
            wide = wide.loc[
                wide["production_input_opposite"]
                | wide["consumption_p4005_opposite"]
            ].copy()

        if wide.empty:
            return pd.DataFrame()

        change_columns = [
            f"{variable}_change"
            for variable in variables
        ]

        wide["largest_absolute_change"] = (
            wide[change_columns]
            .abs()
            .max(axis=1)
        )

        wide = (
            wide.sort_values(
                "largest_absolute_change",
                ascending=False,
            )
            .head(max(int(max_rows), 1))
            .reset_index(drop=True)
        )

        ordered_columns = [
            *group_columns,
            "count",
            "production_input_opposite",
            "production_input_gap_pct",
            "consumption_p4005_opposite",
            "consumption_p4005_gap_pct",
        ]

        for variable in variables:
            ordered_columns.extend(
                [
                    f"{variable}_{previous_year}",
                    f"{variable}_{current_year}",
                    f"{variable}_change",
                    f"{variable}_percentage_change",
                    f"{variable}_direction",
                ]
            )

        return wide[
            [
                column
                for column in ordered_columns
                if column in wide.columns
            ]
        ]

    @staticmethod
    def _create_breakdown_data(
        df: pd.DataFrame,
        year: int,
        group_level: str | None,
        group_value: str | None,
        variable: str,
        *,
        orgnr_foretak: str | None = None,
        orgnr_bedrift: str | None = None,
    ) -> pd.DataFrame:
        """
        Break a composite VL variable into its accounting components.

        The analysis can be performed for an industry group, an enterprise or an
        individual business. Positive and negative components are aggregated for
        the selected and previous years, and the final row reconstructs the
        chosen composite variable.
        """
        if "year" not in df.columns:
            raise ValueError(
                "Datasettet mangler kolonnen 'year'."
            )

        unit_analysis = bool(
            orgnr_foretak
            or orgnr_bedrift
        )

        if not unit_analysis:
            if "naring" not in df.columns:
                raise ValueError(
                    "Datasettet mangler kolonnen 'naring'."
                )

            valid_group_levels = {
                "n2",
                "n3",
                "n4",
                "naring",
            }

            if group_level not in valid_group_levels:
                raise ValueError(
                    f"Ugyldig næringsnivå: {group_level}."
                )

            if not group_value:
                raise ValueError(
                    "Næringskode mangler."
                )

        if orgnr_foretak and "orgnr_foretak" not in df.columns:
            raise ValueError(
                "Datasettet mangler kolonnen "
                "'orgnr_foretak'."
            )

        if orgnr_bedrift and "orgnr_bedrift" not in df.columns:
            raise ValueError(
                "Datasettet mangler kolonnen "
                "'orgnr_bedrift'."
            )

        breakdown_definitions: dict[
            str,
            tuple[
                list[str],
                list[str],
                str,
            ],
        ] = {
            "omsetning": (
                [
                    "nopost_p3000",
                    "nopost_p3100",
                    "nopost_p3200",
                    "nopost_p3500",
                    "nopost_p3600",
                    "nopost_p3650",
                    "nopost_p3695",
                    "nopost_p3700",
                    "nopost_p3900",
                    "nopost_p3605",
                    "nopost_p3710",
                ],
                [
                    "nopost_p3300",
                ],
                "Omsetning",
            ),
            "nopost_driftskostnader": (
                [
                    "nopost_p4005",
                    "nopost_p4295",
                    "nopost_p4500",
                    "nopost_p5000",
                    "nopost_p5300",
                    "nopost_p5400",
                    "nopost_p5420",
                    "nopost_p5600",
                    "nopost_p5900",
                    "nopost_p5950",
                    "nopost_p5999",
                    "nopost_p6000",
                    "nopost_p6050",
                    "nopost_p6100",
                    "nopost_p6200",
                    "nopost_p6300",
                    "nopost_p6340",
                    "nopost_p6395",
                    "nopost_p6400",
                    "nopost_p6440",
                    "nopost_p6500",
                    "nopost_p6600",
                    "nopost_p6695",
                    "nopost_p6700",
                    "nopost_p6995",
                    "nopost_p7000",
                    "nopost_p7020",
                    "nopost_p7040",
                    "nopost_p7080",
                    "nopost_p7155",
                    "nopost_p7165",
                    "nopost_p7295",
                    "nopost_p7330",
                    "nopost_p7370",
                    "nopost_p7490",
                    "nopost_p7500",
                    "nopost_p7565",
                    "nopost_p7600",
                    "nopost_p7700",
                    "nopost_p7830",
                    "nopost_p7880",
                    "nopost_p7885",
                    "nopost_p4999",
                    "nopost_p5959",
                    "nopost_p7897",
                    "nopost_p7910",
                    "nopost_p7999",
                    "nopost_p7400",
                    "nopost_p7420",
                    "nopost_p7440",
                    "nopost_p7860",
                    "nopost_p7890",
                    "nopost_p7911",
                ],
                [
                    "nopost_p4995",
                    "nopost_p6998",
                    "nopost_p7099",
                    "nopost_p7098",
                ],
                "Driftskostnader",
            ),
            "produktinnsats": (
                [
                    "nopost_p4005",
                    "nopost_p4500",
                    "nopost_p5300",
                    "nopost_p5600",
                    "nopost_p6100",
                    "nopost_p6200",
                    "nopost_p6300",
                    "nopost_p6340",
                    "nopost_p6395",
                    "nopost_p6400",
                    "nopost_p6440",
                    "nopost_p6500",
                    "nopost_p6600",
                    "nopost_p6695",
                    "nopost_p6700",
                    "nopost_p6995",
                    "nopost_p7000",
                    "nopost_p7020",
                    "nopost_p7040",
                    "nopost_p7080",
                    "nopost_p7155",
                    "nopost_p7165",
                    "nopost_p7295",
                    "nopost_p7330",
                    "nopost_p7370",
                    "nopost_p7400",
                    "nopost_p7420",
                    "nopost_p7440",
                    "nopost_p7490",
                    "nopost_p7500",
                    "nopost_p7565",
                    "nopost_p7600",
                    "nopost_p7700",
                    "nopost_p6310",
                    "nopost_p7350",
                    "nopost_p7495",
                ],
                [
                    "nopost_p6998",
                    "nopost_p7099",
                    "nopost_p7098",
                    "ts_forbruk",
                ],
                "Produktinnsats",
            ),
            "produksjonsverdi": (
                [
                    "nopost_p3000",
                    "nopost_p3100",
                    "nopost_p3200",
                    "nopost_p3500",
                    "nopost_p3600",
                    "nopost_p3650",
                    "nopost_p3695",
                    "nopost_p3700",
                    "nopost_p3710",
                    "nopost_p3900",
                    "nopost_p3605",
                ],
                [
                    "ts_forbruk",
                    "nopost_p4295",
                    "nopost_p4995",
                    "nopost_p3300",
                ],
                "Produksjonsverdi",
            ),
            "bearbeidingsverdi": (
                [
                    "nopost_p3000",
                    "nopost_p3100",
                    "nopost_p3200",
                    "nopost_p3400",
                    "nopost_p3500",
                    "nopost_p3600",
                    "nopost_p3605",
                    "nopost_p3650",
                    "nopost_p3695",
                    "nopost_p3700",
                    "nopost_p3710",
                    "nopost_p3900",
                    "nopost_p6998",
                ],
                [
                    "nopost_p3300",
                    "nopost_p4295",
                    "nopost_p4995",
                    "nopost_p4005",
                    "nopost_p4500",
                    "nopost_p5300",
                    "nopost_p5600",
                    "nopost_p6100",
                    "nopost_p6200",
                    "nopost_p6300",
                    "nopost_p6310",
                    "nopost_p6340",
                    "nopost_p6395",
                    "nopost_p6400",
                    "nopost_p6440",
                    "nopost_p6500",
                    "nopost_p6600",
                    "nopost_p6695",
                    "nopost_p6700",
                    "nopost_p6995",
                    "nopost_p7000",
                    "nopost_p7020",
                    "nopost_p7040",
                    "nopost_p7080",
                    "nopost_p7155",
                    "nopost_p7165",
                    "nopost_p7295",
                    "nopost_p7330",
                    "nopost_p7350",
                    "nopost_p7370",
                    "nopost_p7400",
                    "nopost_p7420",
                    "nopost_p7440",
                    "nopost_p7490",
                    "nopost_p7495",
                    "nopost_p7500",
                    "nopost_p7565",
                    "nopost_p7600",
                    "nopost_p7700",
                ],
                "Bearbeidingsverdi",
            ),
        }

        if variable not in breakdown_definitions:
            raise ValueError(
                f"Variabelen {variable} støttes ikke "
                "i sammensatt analyse."
            )

        positive_columns, negative_columns, total_label = (
            breakdown_definitions[variable]
        )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        if "orgnr_foretak" in data.columns:
            data["orgnr_foretak"] = (
                data["orgnr_foretak"]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )

        if "orgnr_bedrift" in data.columns:
            data["orgnr_bedrift"] = (
                data["orgnr_bedrift"]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )

        if not unit_analysis:
            data["naring"] = data["naring"].astype(
                "string"
            )

            data["n2"] = data["naring"].str.slice(0, 2)
            data["n3"] = data["naring"].str.slice(0, 4)
            data["n4"] = data["naring"].str.slice(0, 5)

        current_year = int(year)
        previous_year = current_year - 1

        data = data.loc[
            data["year"].isin(
                [
                    previous_year,
                    current_year,
                ]
            )
        ].copy()

        if orgnr_foretak:
            cleaned_enterprise = (
                str(orgnr_foretak)
                .strip()
                .removesuffix(".0")
            )

            data = data.loc[
                data["orgnr_foretak"].astype(str)
                == cleaned_enterprise
            ].copy()

        if orgnr_bedrift:
            cleaned_business = (
                str(orgnr_bedrift)
                .strip()
                .removesuffix(".0")
            )

            data = data.loc[
                data["orgnr_bedrift"].astype(str)
                == cleaned_business
            ].copy()

        if not unit_analysis:
            data = data.loc[
                data[str(group_level)].astype(str)
                == str(group_value)
            ].copy()

        if data.empty:
            return pd.DataFrame(
                columns=[
                    "post",
                    str(current_year),
                    str(previous_year),
                    "change",
                ]
            )

        needed_columns = list(
            dict.fromkeys(
                positive_columns
                + negative_columns
            )
        )

        for column in needed_columns:
            if column not in data.columns:
                data[column] = 0.0

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            ).fillna(0)

        aggregated = (
            data.groupby(
                "year",
                as_index=False,
            )[needed_columns]
            .sum()
        )

        values_by_year = (
            aggregated.set_index("year")
        )

        rows: list[dict[str, object]] = []

        total_current = 0.0
        total_previous = 0.0

        for column in positive_columns:
            current_value = (
                float(
                    values_by_year.at[
                        current_year,
                        column,
                    ]
                )
                if current_year in values_by_year.index
                else 0.0
            )

            previous_value = (
                float(
                    values_by_year.at[
                        previous_year,
                        column,
                    ]
                )
                if previous_year in values_by_year.index
                else 0.0
            )

            rows.append(
                {
                    "post": f"+ {column.replace('nopost_', '')}",
                    str(current_year): current_value,
                    str(previous_year): previous_value,
                    "change": (
                        current_value
                        - previous_value
                    ),
                }
            )

            total_current += current_value
            total_previous += previous_value

        for column in negative_columns:
            current_value = (
                float(
                    values_by_year.at[
                        current_year,
                        column,
                    ]
                )
                if current_year in values_by_year.index
                else 0.0
            )

            previous_value = (
                float(
                    values_by_year.at[
                        previous_year,
                        column,
                    ]
                )
                if previous_year in values_by_year.index
                else 0.0
            )

            signed_current = -current_value
            signed_previous = -previous_value

            rows.append(
                {
                    "post": f"- {column.replace('nopost_', '')}",
                    str(current_year): signed_current,
                    str(previous_year): signed_previous,
                    "change": (
                        signed_current
                        - signed_previous
                    ),
                }
            )

            total_current += signed_current
            total_previous += signed_previous

        rows.append(
            {
                "post": f"= {total_label}",
                str(current_year): total_current,
                str(previous_year): total_previous,
                "change": (
                    total_current
                    - total_previous
                ),
            }
        )

        return pd.DataFrame(rows)

    @staticmethod
    def _create_moms_data(
        df: pd.DataFrame,
        group_level: str = "n2",
        *,
        previous_year: int = 2023,
        current_year: int = 2024,
        selected_naringer: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Create a year-over-year comparison between VL and MOMS measures.

        Results are restricted to industry codes stored at the exact selected
        level, then reshaped to one row per industry. Entry and exit measures for
        the current year are joined to the stock and value comparisons.
        """
        required_columns = {
            "aar",
            "naring",
            "antall",
            "sysselsetting_syss",
            "omsetning",
            "moms",
        }

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "MOMS-datasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_group_levels = {
            "n2",
            "n3",
            "n4",
            "n5",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        data["aar"] = pd.to_numeric(
            data["aar"],
            errors="coerce",
        )

        data = data.loc[
            data["aar"].isin(
                [
                    int(previous_year),
                    int(current_year),
                ]
            )
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["naring"] = data["naring"].astype(
            "string"
        )

        slice_lengths = {
            "n2": 2,
            "n3": 4,
            "n4": 5,
            "n5": 6,
        }

        exact_length = slice_lengths[group_level]

        data = data.loc[
            data["naring"].str.len()
            == exact_length
        ].copy()

        if data.empty:
            return pd.DataFrame()

        data["group_value"] = data["naring"]

        if selected_naringer:
            selected_values = {
                str(value)
                for value in selected_naringer
            }

            data = data.loc[
                data["group_value"]
                .astype(str)
                .isin(selected_values)
            ].copy()

            if data.empty:
                return pd.DataFrame()

        metrics = [
            "antall",
            "sysselsetting_syss",
            "omsetning",
            "moms",
        ]

        movement_columns = [
            "tilganger",
            "avganger",
            "tilganger_omsetning",
            "avganger_omsetning",
            "tilganger_sysselsetting_syss",
            "avganger_sysselsetting_syss",
        ]

        for column in metrics + movement_columns:
            if column not in data.columns:
                data[column] = 0.0

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        aggregated_metrics = (
            data.groupby(
                [
                    "aar",
                    "group_value",
                ],
                as_index=False,
            )[metrics]
            .sum(min_count=1)
        )

        wide = aggregated_metrics.pivot(
            index="group_value",
            columns="aar",
            values=metrics,
        )

        if wide.empty:
            return pd.DataFrame()

        wide.columns = [
            f"{metric}_{int(year)}"
            for metric, year in wide.columns
        ]

        wide = (
            wide.reset_index()
            .rename(
                columns={
                    "group_value": "naring"
                }
            )
        )

        for metric in metrics:
            for required_year in [
                int(previous_year),
                int(current_year),
            ]:
                column = f"{metric}_{required_year}"

                if column not in wide.columns:
                    wide[column] = np.nan

        for metric in metrics:
            previous_column = (
                f"{metric}_{int(previous_year)}"
            )
            current_column = (
                f"{metric}_{int(current_year)}"
            )

            previous_values = pd.to_numeric(
                wide[previous_column],
                errors="coerce",
            )

            current_values = pd.to_numeric(
                wide[current_column],
                errors="coerce",
            )

            change_column = f"{metric}_change"
            percentage_column = (
                f"{metric}_percentage_change"
            )

            wide[previous_column] = previous_values
            wide[current_column] = current_values

            wide[change_column] = (
                current_values
                - previous_values
            )

            wide[percentage_column] = np.where(
                previous_values.isna()
                | previous_values.eq(0),
                np.nan,
                (
                    current_values
                    - previous_values
                )
                / previous_values
                * 100.0,
            )

        movement = (
            data.loc[
                data["aar"]
                == int(current_year)
            ]
            .groupby(
                "group_value",
                as_index=False,
            )[movement_columns]
            .sum(min_count=1)
            .rename(
                columns={
                    "group_value": "naring"
                }
            )
        )

        wide = wide.merge(
            movement,
            on="naring",
            how="left",
        )

        for column in movement_columns:
            if column not in wide.columns:
                wide[column] = 0.0

            wide[column] = pd.to_numeric(
                wide[column],
                errors="coerce",
            ).fillna(0)

        wide["_sorting_value"] = pd.to_numeric(
            wide["naring"]
            .astype(str)
            .str.replace(
                ".",
                "",
                regex=False,
            ),
            errors="coerce",
        )

        wide = (
            wide.sort_values(
                [
                    "_sorting_value",
                    "naring",
                ]
            )
            .drop(columns="_sorting_value")
            .reset_index(drop=True)
        )

        ordered_columns = [
            "naring",

            f"antall_{int(previous_year)}",
            f"antall_{int(current_year)}",
            "tilganger",
            "avganger",

            f"sysselsetting_syss_{int(previous_year)}",
            f"sysselsetting_syss_{int(current_year)}",
            "tilganger_sysselsetting_syss",
            "avganger_sysselsetting_syss",

            f"omsetning_{int(previous_year)}",
            f"omsetning_{int(current_year)}",
            "tilganger_omsetning",
            "avganger_omsetning",

            f"moms_{int(previous_year)}",
            f"moms_{int(current_year)}",

            "antall_percentage_change",
            "sysselsetting_syss_percentage_change",
            "omsetning_percentage_change",
            "moms_percentage_change",
        ]

        return wide[
            [
                column
                for column in ordered_columns
                if column in wide.columns
            ]
        ]

    @staticmethod
    def _create_movement_data(
        df: pd.DataFrame,
        direction: str = "tilgang",
        variable: str = "omsetning",
        group_level: str = "n2",
        *,
        code_filter: str = "",
        exact_match: bool = False,
        top_n: int = 100,
    ) -> pd.DataFrame:
        """
        Create business-level entry, exit and industry-movement data.

        A business is treated as movement when it appears, disappears or changes
        industry group between the previous and current records. Industry levels
        are derived directly from the detailed codes using the decimal-aware
        character lengths documented at module level.

        ``tilgang`` ranks and filters on the current group and value, while
        ``avgang`` uses the previous group and value. The optional code filter can
        use either exact matching or prefix matching.
        """
        required_columns = {
            "orgnr_bedrift",
            "orgnr_foretak_prev",
            "orgnr_foretak_curr",
            "naring_prev",
            "naring_curr",
            "omsetning_prev",
            "omsetning_curr",
            "sysselsetting_syss_prev",
            "sysselsetting_syss_curr",
        }

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bevegelsesdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        if direction not in {
            "tilgang",
            "avgang",
        }:
            raise ValueError(
                "direction må være 'tilgang' eller 'avgang'."
            )

        if variable not in {
            "omsetning",
            "sysselsetting_syss",
        }:
            raise ValueError(
                "variable må være 'omsetning' eller "
                "'sysselsetting_syss'."
            )

        valid_group_levels = {
            "n2",
            "n3",
            "n4",
            "n5",
        }

        if group_level not in valid_group_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {group_level}."
            )

        data = df.copy()

        string_columns = [
            "orgnr_bedrift",
            "orgnr_foretak_prev",
            "orgnr_foretak_curr",
            "naring_prev",
            "naring_curr",
        ]
        for column in string_columns:
            if column in data.columns:
                data[column] = data[column].astype(
                    "string"
                )

        numeric_columns = [
            "omsetning_prev",
            "omsetning_curr",
            "sysselsetting_syss_prev",
            "sysselsetting_syss_curr",
        ]

        for column in numeric_columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )
        # The decimal point is part of the stored code, so displayed digit levels
        # do not equal Python string lengths for N3, N4 and N5.
        slice_lengths = {
            "n2": 2,
            "n3": 4,
            "n4": 5,
            "n5": 6,
        }

        slice_length = slice_lengths[group_level]

        data["naring_prev"] = (
            data["naring_prev"]
            .astype("string")
            .str.strip()
        )

        data["naring_curr"] = (
            data["naring_curr"]
            .astype("string")
            .str.strip()
        )

        data["group_previous"] = (
            data["naring_prev"]
            .str.slice(
                0,
                slice_length,
            )
        )

        data["group_current"] = (
            data["naring_curr"]
            .str.slice(
                0,
                slice_length,
            )
        )

        previous_exists = data[
            "group_previous"
        ].notna()

        current_exists = data[
            "group_current"
        ].notna()

        changed_code = (
            previous_exists
            & current_exists
            & (
                data["group_previous"]
                != data["group_current"]
            )
        )

        disappeared = (
            previous_exists
            & ~current_exists
        )

        appeared = (
            ~previous_exists
            & current_exists
        )

        movement_mask = (
            changed_code
            | disappeared
            | appeared
        )

        if direction == "tilgang":
            data = data.loc[
                movement_mask
                & current_exists
            ].copy()

            if variable == "omsetning":
                data["sort_value"] = (
                    data["omsetning_curr"]
                )
            else:
                data["sort_value"] = (
                    data["sysselsetting_syss_curr"]
                )

            target_group_column = "group_current"

        else:
            data = data.loc[
                movement_mask
                & previous_exists
            ].copy()

            if variable == "omsetning":
                data["sort_value"] = (
                    data["omsetning_prev"]
                )
            else:
                data["sort_value"] = (
                    data["sysselsetting_syss_prev"]
                )

            target_group_column = "group_previous"

        cleaned_filter = str(code_filter).strip()

        if cleaned_filter:
            if exact_match:
                data = data.loc[
                    data[target_group_column]
                    .astype("string")
                    == cleaned_filter
                ].copy()
            else:
                data = data.loc[
                    data[target_group_column]
                    .astype("string")
                    .str.startswith(
                        cleaned_filter,
                        na=False,
                    )
                ].copy()

        if data.empty:
            return pd.DataFrame()

        data["status"] = ""

        # Movement masks were calculated before direction and code filtering.
        # Reindex them to the surviving rows before assigning status labels.
        data.loc[
            changed_code.reindex(
                data.index,
                fill_value=False,
            ),
            "status",
        ] = "endret kode"

        data.loc[
            appeared.reindex(
                data.index,
                fill_value=False,
            ),
            "status",
        ] = "ny i år"

        data.loc[
            disappeared.reindex(
                data.index,
                fill_value=False,
            ),
            "status",
        ] = "borte i år"

        output_columns = [
            "orgnr_bedrift",
            "orgnr_foretak_prev",
            "orgnr_foretak_curr",
            "group_previous",
            "group_current",
            "naring_prev",
            "naring_curr",
            "omsetning_prev",
            "omsetning_curr",
            "sysselsetting_syss_prev",
            "sysselsetting_syss_curr",
            "status",
            "sort_value",
        ]

        output_columns = [
            column
            for column in output_columns
            if column in data.columns
        ]

        result = (
            data[output_columns]
            .sort_values(
                "sort_value",
                ascending=False,
                na_position="last",
            )
            .head(max(int(top_n), 1))
            .reset_index(drop=True)
        )

        return result

    @staticmethod
    def _create_method_analysis_figure(
        df: pd.DataFrame,
        naring_level: str,
        naring_value: str,
        ratios: list[str],
        *,
        reg_types: list[str] | None = None,
    ) -> go.Figure:
        """
        Create time-series plots for selected accounting ratios.

        Ratios are calculated from aggregated numerators and denominators rather
        than by averaging row-level ratios. Results are separated by unit type
        and, when requested, registration type.
        """
        required_columns = {
            "year",
            "type",
            "naring",
        }

        missing_columns = required_columns.difference(
            df.columns
        )

        if missing_columns:
            raise ValueError(
                "Bedriftsdatasettet mangler kolonnene "
                f"{sorted(missing_columns)}."
            )

        valid_naring_levels = {
            "naring_2",
            "naring_4",
            "naring_5",
            "naring",
        }

        if naring_level not in valid_naring_levels:
            raise ValueError(
                f"Ugyldig næringsnivå: {naring_level}."
            )

        if not ratios:
            return VLModule._empty_figure(
                "Velg minst én rate."
            )

        data = df.copy()

        data["year"] = pd.to_numeric(
            data["year"],
            errors="coerce",
        )

        data = data.dropna(
            subset=["year"]
        ).copy()

        data["year"] = data["year"].astype(int)
        data["type"] = data["type"].astype("string")
        data["naring"] = data["naring"].astype("string")

        if "reg_type" in data.columns:
            data["reg_type"] = data["reg_type"].astype(
                "string"
            )
        else:
            data["reg_type"] = pd.NA

        if "naring_2" not in data.columns:
            data["naring_2"] = (
                data["naring"].str.slice(0, 2)
            )

        if "naring_4" not in data.columns:
            data["naring_4"] = (
                data["naring"].str.slice(0, 4)
            )

        if "naring_5" not in data.columns:
            data["naring_5"] = (
                data["naring"].str.slice(0, 5)
            )

        data = data.loc[
            data[naring_level].astype(str)
            == str(naring_value)
        ].copy()

        if reg_types:
            selected_reg_types = {
                str(value)
                for value in reg_types
            }

            data = data.loc[
                data["reg_type"].astype(str)
                .isin(selected_reg_types)
            ].copy()

        if data.empty:
            return VLModule._empty_figure(
                "Fant ingen data for det valgte filteret."
            )

        ratio_definitions: dict[
            str,
            tuple[str, str],
        ] = {}

        def add_ratio(
            name: str,
            numerator: str,
            denominator: str,
        ) -> None:
            if (
                numerator in data.columns
                and denominator in data.columns
            ):
                ratio_definitions[name] = (
                    numerator,
                    denominator,
                )

        add_ratio(
            "salgsint_rate",
            "ts_salgsint",
            "omsetning",
        )

        add_ratio(
            "forbruk_rate",
            "ts_forbruk",
            "nopost_p4005",
        )

        add_ratio(
            "vikar_rate",
            "ts_vikarutgifter",
            "nopost_lonnskostnader",
        )

        activated_columns = sorted(
            column
            for column in data.columns
            if column.endswith("_akt")
        )

        expense_columns = sorted(
            column
            for column in data.columns
            if column.endswith("_utg")
        )

        for column in activated_columns:
            add_ratio(
                f"{column}_rate",
                column,
                "basisx",
            )

        for column in expense_columns:
            add_ratio(
                f"{column}_rate",
                column,
                "nopost_driftskostnader",
            )

        missing_ratios = [
            ratio
            for ratio in ratios
            if ratio not in ratio_definitions
        ]

        if missing_ratios:
            raise ValueError(
                "Kan ikke beregne ratene "
                f"{sorted(missing_ratios)} fordi teller "
                "eller nevner mangler."
            )

        needed_numeric_columns = set()

        for ratio in ratios:
            numerator, denominator = (
                ratio_definitions[ratio]
            )

            needed_numeric_columns.add(numerator)
            needed_numeric_columns.add(denominator)

        for column in needed_numeric_columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        data["type_group"] = np.where(
            data["type"].astype(str) == "S",
            "type = S",
            "type ≠ S",
        )

        grouping_columns = [
            "year",
            "type_group",
        ]

        if reg_types:
            grouping_columns.append("reg_type")

        aggregated_rows: list[pd.DataFrame] = []

        for ratio in ratios:
            numerator, denominator = (
                ratio_definitions[ratio]
            )

            grouped = (
                data.groupby(
                    grouping_columns,
                    dropna=False,
                )
                .agg(
                    numerator_sum=(
                        numerator,
                        lambda values: pd.to_numeric(
                            values,
                            errors="coerce",
                        ).sum(min_count=1),
                    ),
                    denominator_sum=(
                        denominator,
                        lambda values: pd.to_numeric(
                            values,
                            errors="coerce",
                        ).sum(min_count=1),
                    ),
                )
                .reset_index()
            )

            grouped["ratio"] = np.where(
                grouped["denominator_sum"].notna()
                & grouped["denominator_sum"].ne(0),
                (
                    grouped["numerator_sum"]
                    / grouped["denominator_sum"]
                ),
                np.nan,
            )

            grouped["ratio_name"] = ratio

            aggregated_rows.append(grouped)

        if not aggregated_rows:
            return VLModule._empty_figure(
                "Ingen rater kunne beregnes."
            )

        result = pd.concat(
            aggregated_rows,
            ignore_index=True,
        )

        result = result.replace(
            [np.inf, -np.inf],
            np.nan,
        )

        result = result.dropna(
            subset=["ratio"]
        ).copy()

        if result.empty:
            return VLModule._empty_figure(
                "Ingen gyldige rater kunne beregnes."
            )

        result = result.sort_values(
            [
                "ratio_name",
                "type_group",
                "year",
            ]
        )

        figure = go.Figure()

        trace_group_columns = [
            "ratio_name",
            "type_group",
        ]

        if reg_types:
            trace_group_columns.append("reg_type")

        for group_values, group in result.groupby(
            trace_group_columns,
            dropna=False,
        ):
            if not isinstance(group_values, tuple):
                group_values = (group_values,)

            ratio_name = str(group_values[0])
            type_group = str(group_values[1])

            if reg_types:
                reg_type = str(group_values[2])

                trace_name = (
                    f"{ratio_name} – {type_group} – "
                    f"reg_type {reg_type}"
                )
            else:
                trace_name = (
                    f"{ratio_name} – {type_group}"
                )

            group = group.sort_values("year")

            figure.add_trace(
                go.Scatter(
                    x=group["year"],
                    y=group["ratio"],
                    mode="lines+markers",
                    name=trace_name,
                    line={"width": 3},
                    marker={"size": 7},
                    customdata=np.column_stack(
                        [
                            group["numerator_sum"],
                            group["denominator_sum"],
                        ]
                    ),
                    hovertemplate=(
                        "År: %{x}<br>"
                        "Rate: %{y:.4f}<br>"
                        "Sum teller: %{customdata[0]:,.0f}<br>"
                        "Sum nevner: %{customdata[1]:,.0f}"
                        "<extra>%{fullData.name}</extra>"
                    ),
                )
            )

        figure.update_layout(
            autosize=True,
            width=None,
            height=None,
            title=(
                "Metodeanalyse – "
                f"{naring_level} {naring_value}"
            ),
            xaxis_title="År",
            yaxis_title="Rate",
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
                "t": 120,
                "b": 70,
            },
        )

        figure.update_xaxes(dtick=1)

        return figure

    @staticmethod
    # ========================================================================
    # Shared table formatting
    # ========================================================================

    def _prepare_table_output(
        df: pd.DataFrame,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        """
        Convert an analysis DataFrame into shared Dash DataTable properties.

        The function applies Norwegian display labels, numeric formatting,
        conditional styling, alignment and tooltips while preserving the source
        column IDs used by callbacks and filters.
        """
        if df.empty:
            return (
                [],
                [],
                [],
                [],
            )

        display_df = df.copy()

        column_labels = {
            "naring": "Detaljert næring",
            "naring_1": "Næringshovedområde",
            "naring_2": "2-siffer næring",
            "naring_3": "3-siffer næring",
            "naring_4": "3-siffer næring",
            "naring_5": "4-siffer næring",
            "nivå": "Nivå",
            "gruppe": "Gruppe",
            "naring_previous": "Næring året før",
            "naring_f": "Foretaksnæring",
            "naring_f_previous": "Foretaksnæring året før",
            "fylke": "Fylke",
            "year": "År",
            "aar": "År",
            "variable": "Variabel",
            "post": "Post",
            "orgnr_foretak": "Foretaksnummer",
            "orgnr_bedrift": "Bedriftsnummer",
            "n_bedrifter": "Antall bedrifter",
            "n_rows": "Antall rader",
            "orgnr_foretak_prev": "Foretak året før",
            "orgnr_foretak_curr": "Foretak valgt år",
            "navn": "Navn",
            "type": "Type",
            "reg_type": "Registreringstype",
            "value_previous": "Verdi året før",
            "value_current": "Verdi valgt år",
            "change": "Endring",
            "absolute_change": "Absolutt endring",
            "percentage_change": "Endring (%)",
            "direction": "Retning",
            "breach": "Kontrollbrudd",
            "z_score": "Z-verdi",
            "largest_business": "Største bedrift",
            "largest_enterprise": "Største foretak",
            "business_contribution": "Bidrag fra bedrift",
            "business_contribution_pct": "Bidrag fra bedrift (%)",
            "enterprise_contribution": "Bidrag fra foretak",
            "enterprise_contribution_pct": "Bidrag fra foretak (%)",
            "explanation": "Forklaring",
            "negative_column_count": "Antall negative poster",
            "negative_check_count": "Antall negative kontroller",
            "most_negative_value": "Mest negative verdi",
            "count": "Antall bedrifter",
            "group_previous": "Næring året før",
            "group_current": "Næring valgt år",
            "status": "Status",
            "sort_value": "Sorteringsverdi",

            "production_input_opposite": (
                "Produksjonsverdi og produktinnsats motsatt"
            ),
            "production_input_gap_pct": (
                "Gap produksjonsverdi/produktinnsats (%)"
            ),
            "consumption_p4005_opposite": (
                "Forbruk og varekostnad motsatt"
            ),
            "consumption_p4005_gap_pct": (
                "Gap forbruk/varekostnad (%)"
            ),

            "produksjonsverdi_2023": "Produksjonsverdi 2023",
            "produksjonsverdi_2024": "Produksjonsverdi 2024",
            "produksjonsverdi_change": "Endring i produksjonsverdi",
            "produksjonsverdi_percentage_change": (
                "Endring i produksjonsverdi (%)"
            ),
            "produksjonsverdi_direction": "Retning produksjonsverdi",

            "produktinnsats_2023": "Produktinnsats 2023",
            "produktinnsats_2024": "Produktinnsats 2024",
            "produktinnsats_change": "Endring i produktinnsats",
            "produktinnsats_percentage_change": (
                "Endring i produktinnsats (%)"
            ),
            "produktinnsats_direction": "Retning produktinnsats",

            "ts_forbruk_2023": "Forbruk 2023",
            "ts_forbruk_2024": "Forbruk 2024",
            "ts_forbruk_change": "Endring i forbruk",
            "ts_forbruk_percentage_change": (
                "Endring i forbruk (%)"
            ),
            "ts_forbruk_direction": "Retning forbruk",

            "nopost_p4005_2023": "Varekostnad 2023",
            "nopost_p4005_2024": "Varekostnad 2024",
            "nopost_p4005_change": "Endring i varekostnad",
            "nopost_p4005_percentage_change": (
                "Endring i varekostnad (%)"
            ),
            "nopost_p4005_direction": "Retning varekostnad",
        }

        percentage_columns = {
            column
            for column in display_df.columns
            if (
                column.endswith("_percentage_change")
                or column.endswith("_contribution_pct")
                or column.endswith("_gap_pct")
                or column == "percentage_change"
            )
        }

        numeric_columns = (
            display_df.select_dtypes(
                include=[np.number]
            )
            .columns
            .tolist()
        )

        for column in numeric_columns:
            display_df[column] = pd.to_numeric(
                display_df[column],
                errors="coerce",
            ).round(2)

        boolean_columns = (
            display_df.select_dtypes(
                include=["bool"]
            )
            .columns
            .tolist()
        )

        for column in boolean_columns:
            display_df[column] = (
                display_df[column]
                .map(
                    {
                        True: "Ja",
                        False: "Nei",
                    }
                )
            )

        if "breach" in display_df.columns:
            display_df["breach"] = (
                display_df["breach"]
                .replace(
                    {
                        True: "Ja",
                        False: "Nei",
                    }
                )
            )

        display_df = display_df.replace(
            {
                np.nan: None,
                np.inf: None,
                -np.inf: None,
            }
        )

        columns: list[dict[str, Any]] = []

        for column in display_df.columns:
            column_definition: dict[str, Any] = {
                "name": column_labels.get(
                    column,
                    column.replace(
                        "_",
                        " ",
                    ).capitalize(),
                ),
                "id": column,
            }

            if column in numeric_columns:
                column_definition["type"] = "numeric"

                column_definition["format"] = {
                    "specifier": ",.2f",
                }

            else:
                column_definition["type"] = "text"

            columns.append(
                column_definition
            )

        style_data_conditional: list[
            dict[str, Any]
        ] = []

        if "breach" in display_df.columns:
            style_data_conditional.append(
                {
                    "if": {
                        "filter_query": (
                            "{breach} = 'Ja'"
                        ),
                    },
                    "backgroundColor": "#fff1f0",
                    "fontWeight": "bold",
                }
            )

        direction_columns = [
            column
            for column in display_df.columns
            if (
                column == "direction"
                or column.endswith("_direction")
            )
        ]

        for direction_column in direction_columns:
            if direction_column == "direction":
                percentage_column = "percentage_change"
            else:
                percentage_column = direction_column.replace(
                    "_direction",
                    "_percentage_change",
                )

            if percentage_column not in display_df.columns:
                continue

            style_data_conditional.extend(
                [
                    {
                        "if": {
                            "column_id": percentage_column,
                            "filter_query": (
                                f"{{{direction_column}}} = '⬇️'"
                            ),
                        },
                        "color": "#b91c1c",
                        "fontWeight": "bold",
                    },
                    {
                        "if": {
                            "column_id": percentage_column,
                            "filter_query": (
                                f"{{{direction_column}}} = '⬆️'"
                            ),
                        },
                        "color": "#166534",
                        "fontWeight": "bold",
                    },
                ]
            )

        right_aligned_columns = [
            column
            for column in numeric_columns
            if column in display_df.columns
        ]

        for column in right_aligned_columns:
            style_data_conditional.append(
                {
                    "if": {
                        "column_id": column,
                    },
                    "textAlign": "right",
                }
            )

        wide_text_columns = {
            "navn",
            "explanation",
            "largest_business",
            "largest_enterprise",
        }

        for column in wide_text_columns:
            if column in display_df.columns:
                style_data_conditional.append(
                    {
                        "if": {
                            "column_id": column,
                        },
                        "minWidth": "220px",
                        "width": "280px",
                        "maxWidth": "450px",
                    }
                )

        tooltip_data: list[
            dict[str, Any]
        ] = []

        for row in display_df.to_dict(
            "records"
        ):
            tooltip_row: dict[str, Any] = {}

            for column, value in row.items():
                if value is None:
                    continue

                text = str(value)

                if len(text) > 30:
                    tooltip_row[column] = {
                        "value": text,
                        "type": "text",
                    }

            tooltip_data.append(
                tooltip_row
            )

        data = display_df.to_dict(
            "records"
        )

        return (
            data,
            columns,
            style_data_conditional,
            tooltip_data,
        )

    # ========================================================================
    # Dash callback registration
    # ========================================================================

    def module_callbacks(self) -> None:
        """
        Register all callbacks used by the VL module.

        Callback groups populate selectors, coordinate dependent controls,
        manage drilldowns and route the selected visualisation to the relevant
        figure or table builder. Registration happens once during construction.
        """

        @callback(
            Output(self.naring_id, "options"),
            Output(self.naring_id, "value"),
            Output(self.multi_naring_group_id, "options"),
            Output(self.multi_naring_group_id, "value"),
            Output(self.multi_naring_id, "options"),
            Output(self.variable_id, "options"),
            Output(self.variable_id, "value"),
            Output(self.multi_variable_id, "options"),
            Output(self.multi_variable_id, "value"),

            Output(self.change_year_id, "options"),
            Output(self.change_year_id, "value"),

            Output(self.noku_year_id, "options"),
            Output(self.noku_year_id, "value"),

            Output(self.large_changes_year_id, "options"),
            Output(self.large_changes_year_id, "value"),
            Output(self.large_changes_variables_id, "options"),
            Output(self.large_changes_variables_id, "value"),
            Output(self.large_changes_fylke_id, "options"),
            Output(self.large_changes_fylke_id, "value"),

            Output(self.negative_nopost_year_id, "options"),
            Output(self.negative_nopost_year_id, "value"),

            Output(self.nr_year_id, "options"),
            Output(self.nr_year_id, "value"),

            Output(self.opposite_year_id, "options"),
            Output(self.opposite_year_id, "value"),

            Output(self.breakdown_year_id, "options"),
            Output(self.breakdown_year_id, "value"),

            Output(self.moms_previous_year_id, "options"),
            Output(self.moms_previous_year_id, "value"),
            Output(self.moms_current_year_id, "options"),
            Output(self.moms_current_year_id, "value"),

            Output(self.method_reg_types_id, "options"),
            Output(self.method_reg_types_id, "value"),

            Output(self.status_id, "children"),
            Input(self.data_version_id, "value"),
        )
        def load_dropdown_options(
            data_version: str,
        ) -> tuple[Any, ...]:
            try:
                aggregate_path = self._parquet_path(
                    data_version,
                    dataset="agg_naring4",
                )
                aggregate_df = self._read_data(
                    aggregate_path
                )

                business_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter",
                )
                business_df = self._read_business_data(
                    business_path
                )

                enterprise_path = self._parquet_path(
                    data_version,
                    dataset="foretak",
                )
                enterprise_df = self._read_enterprise_data(
                    enterprise_path
                )

                # -------------------------------------------------
                # Næring options
                # -------------------------------------------------
                naring_values = sorted(
                    aggregate_df["naring_4"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                naring_options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in naring_values
                ]

                naring_value = (
                    naring_values[0]
                    if naring_values
                    else None
                )

                n2_values = sorted(
                    {
                        value[:2]
                        for value in naring_values
                        if len(value) >= 2
                    }
                )

                n2_options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in n2_values
                ]

                default_n2_value = (
                    "45"
                    if "45" in n2_values
                    else (
                        n2_values[0]
                        if n2_values
                        else None
                    )
                )

                # -------------------------------------------------
                # Aggregate variable options
                # -------------------------------------------------
                numeric_columns = (
                    aggregate_df.select_dtypes(
                        include=[np.number]
                    )
                    .columns
                    .tolist()
                )

                variable_values = sorted(
                    column
                    for column in numeric_columns
                    if column != "year"
                )

                variable_options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in variable_values
                ]

                preferred_variable = "omsetning"

                variable_value = (
                    preferred_variable
                    if preferred_variable in variable_values
                    else (
                        variable_values[0]
                        if variable_values
                        else None
                    )
                )

                preferred_multi_variables = [
                    "omsetning",
                    "nopost_driftskostnader",
                ]

                multi_variable_value = [
                    variable
                    for variable in preferred_multi_variables
                    if variable in variable_values
                ]

                if not multi_variable_value:
                    multi_variable_value = variable_values[:3]

                # -------------------------------------------------
                # General year options
                # -------------------------------------------------
                year_values = sorted(
                    aggregate_df["year"]
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

                latest_year = (
                    year_values[-1]
                    if year_values
                    else None
                )

                # -------------------------------------------------
                # Business variable options
                # -------------------------------------------------
                business_numeric_columns = (
                    business_df.select_dtypes(
                        include=[np.number]
                    )
                    .columns
                    .tolist()
                )

                excluded_business_variables = {
                    "year",
                }

                business_variable_values = sorted(
                    column
                    for column in business_numeric_columns
                    if column not in excluded_business_variables
                )

                business_variable_options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in business_variable_values
                ]

                preferred_large_change_variable = "omsetning"

                if preferred_large_change_variable in business_variable_values:
                    large_change_variable_value = (
                        preferred_large_change_variable
                    )
                elif business_variable_values:
                    large_change_variable_value = (
                        business_variable_values[0]
                    )
                else:
                    large_change_variable_value = None

                # -------------------------------------------------
                # County options
                # -------------------------------------------------
                if "fylke" in business_df.columns:
                    fylke_values = sorted(
                        business_df["fylke"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )
                else:
                    fylke_values = []

                fylke_options = [
                    {
                        "label": "Hele landet",
                        "value": "Land",
                    },
                    *[
                        {
                            "label": fylke,
                            "value": fylke,
                        }
                        for fylke in fylke_values
                    ],
                ]

                # -------------------------------------------------
                # MOMS years
                # -------------------------------------------------
                moms_year_options: list[dict[str, int]] = []
                moms_previous_year: int | None = None
                moms_current_year: int | None = None

                try:
                    moms_path = self._parquet_path(
                        data_version,
                        dataset="moms",
                    )
                    moms_df = pd.read_parquet(
                        moms_path
                    )

                    if "aar" in moms_df.columns:
                        moms_year_values = sorted(
                            pd.to_numeric(
                                moms_df["aar"],
                                errors="coerce",
                            )
                            .dropna()
                            .astype(int)
                            .unique()
                            .tolist()
                        )

                        moms_year_options = [
                            {
                                "label": str(year),
                                "value": year,
                            }
                            for year in moms_year_values
                        ]

                        if len(moms_year_values) >= 2:
                            moms_previous_year = (
                                moms_year_values[-2]
                            )
                            moms_current_year = (
                                moms_year_values[-1]
                            )

                        elif len(moms_year_values) == 1:
                            moms_previous_year = (
                                moms_year_values[0]
                            )
                            moms_current_year = (
                                moms_year_values[0]
                            )

                except Exception:
                    moms_year_options = year_options

                    if len(year_values) >= 2:
                        moms_previous_year = year_values[-2]
                        moms_current_year = year_values[-1]

                    elif len(year_values) == 1:
                        moms_previous_year = year_values[0]
                        moms_current_year = year_values[0]

                # -------------------------------------------------
                # Registration types
                # -------------------------------------------------
                if "reg_type" in enterprise_df.columns:
                    reg_type_values = sorted(
                        enterprise_df["reg_type"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )
                elif "reg_type" in business_df.columns:
                    reg_type_values = sorted(
                        business_df["reg_type"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )
                else:
                    reg_type_values = []

                reg_type_options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in reg_type_values
                ]

                status = html.P(
                    [
                        "Aggregert: ",
                        html.Code(aggregate_path),
                        html.Br(),
                        "Bedrifter: ",
                        html.Code(business_path),
                        html.Br(),
                        "Foretak: ",
                        html.Code(enterprise_path),
                    ],
                    style={"fontSize": "12px"},
                )

                return (
                    naring_options,
                    naring_value,
                    n2_options,
                    default_n2_value,
                    naring_options,
                    variable_options,
                    variable_value,
                    variable_options,
                    multi_variable_value,

                    year_options,
                    latest_year,

                    year_options,
                    latest_year,

                    year_options,
                    latest_year,
                    business_variable_options,
                    large_change_variable_value,
                    fylke_options,
                    "Land",

                    year_options,
                    latest_year,

                    year_options,
                    latest_year,

                    year_options,
                    latest_year,

                    year_options,
                    latest_year,

                    moms_year_options,
                    moms_previous_year,
                    moms_year_options,
                    moms_current_year,

                    reg_type_options,
                    [],

                    status,
                )

            except Exception as error:
                empty_options: list[dict[str, Any]] = []

                return (
                    empty_options,
                    None,
                    empty_options,
                    None,
                    empty_options,
                    empty_options,
                    None,
                    empty_options,
                    [],

                    empty_options,
                    None,

                    empty_options,
                    None,

                    empty_options,
                    None,
                    empty_options,
                    None,
                    [
                        {
                            "label": "Hele landet",
                            "value": "Land",
                        }
                    ],
                    "Land",

                    empty_options,
                    None,

                    empty_options,
                    None,

                    empty_options,
                    None,

                    empty_options,
                    None,

                    empty_options,
                    None,
                    empty_options,
                    None,

                    empty_options,
                    [],

                    html.Div(
                        f"Kunne ikke lese data: {error}",
                        className="alert alert-danger",
                    ),
                )

        @callback(
            Output(self.multi_naring_id, "value"),
            Input(self.multi_naring_group_id, "value"),
            Input(self.data_version_id, "value"),
        )
        def update_multi_naring_from_n2(
            selected_n2: str | None,
            data_version: str,
        ) -> list[str] | Any:
            """
            Select every available N3 industry belonging to the
            chosen N2 group.

            Clearing the N2 selector leaves the user's manual
            industry selection unchanged.
            """
            if not selected_n2:
                return no_update

            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="agg_naring4",
                )

                df = self._read_data(parquet_path)

                selected_narings = sorted(
                    df.loc[
                        df["naring_4"]
                        .astype(str)
                        .str.startswith(
                            str(selected_n2),
                            na=False,
                        ),
                        "naring_4",
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                return selected_narings

            except Exception:
                return no_update

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

            search_text = search_value.strip().casefold()

            if len(search_text) < 2:
                return []

            parquet_path = self._parquet_path(
                data_version,
                dataset="foretak",
            )

            lookup = self._read_enterprise_lookup(
                parquet_path
            )

            if lookup.empty:
                return []

            matches = lookup.loc[
                lookup["search_text"].str.contains(
                    search_text,
                    na=False,
                    regex=False,
                )
            ].head(25)

            return [
                {
                    "label": (
                        f"{str(row.navn)} — "
                        f"{str(row.orgnr_foretak)}"
                    ),
                    "value": str(row.orgnr_foretak),
                }
                for row in matches.itertuples()
            ]

        @callback(
            Output(self.enterprise_id, "value"),
            Input(self.enterprise_name_search_id, "value"),
            prevent_initial_call=True,
        )
        def select_enterprise_from_name(
            selected_enterprise: str | None,
        ) -> str | Any:
            """Copy the selected enterprise into the organisation-number input."""
            if not selected_enterprise:
                return no_update

            return str(selected_enterprise)

        @callback(
            Output(
                self.breakdown_enterprise_search_id,
                "options",
            ),
            Input(
                self.breakdown_enterprise_search_id,
                "search_value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )
        def search_breakdown_enterprise_names(
            search_value: str | None,
            data_version: str,
        ) -> list[dict[str, str]]:
            """Search enterprises by name or organisation number."""
            if not search_value:
                return []

            search_text = search_value.strip().casefold()

            if len(search_text) < 2:
                return []

            parquet_path = self._parquet_path(
                data_version,
                dataset="foretak",
            )

            lookup = self._read_enterprise_lookup(
                parquet_path
            )

            if lookup.empty:
                return []

            matches = lookup.loc[
                lookup["search_text"].str.contains(
                    search_text,
                    na=False,
                    regex=False,
                )
            ].head(25)

            return [
                {
                    "label": (
                        f"{str(row.navn)} — "
                        f"{str(row.orgnr_foretak)}"
                    ),
                    "value": str(row.orgnr_foretak),
                }
                for row in matches.itertuples()
            ]


        @callback(
            Output(
                self.breakdown_business_id,
                "options",
            ),
            Output(
                self.breakdown_business_id,
                "value",
            ),
            Input(
                self.breakdown_enterprise_id,
                "value",
            ),
            Input(
                self.breakdown_year_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )
        def update_breakdown_business_options(
            enterprise: str | None,
            year: int | None,
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate businesses belonging to the selected enterprise."""
            if not enterprise:
                return [], None

            enterprise_number = (
                str(enterprise)
                .strip()
                .replace(".0", "")
            )

            if not enterprise_number:
                return [], None

            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter",
                )

                business_df = self._read_business_data(
                    parquet_path
                )

                subset = business_df.loc[
                    business_df["orgnr_foretak"].astype(str)
                    == enterprise_number
                ].copy()

                if subset.empty:
                    return [], None

                # Prefer businesses present in the selected year or
                # the year before, since those are the years used in
                # the breakdown comparison.
                if year is not None:
                    relevant_years = {
                        int(year),
                        int(year) - 1,
                    }

                    relevant_subset = subset.loc[
                        subset["year"].isin(relevant_years)
                    ].copy()

                    if not relevant_subset.empty:
                        subset = relevant_subset

                subset["orgnr_bedrift"] = (
                    subset["orgnr_bedrift"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

                subset = subset.loc[
                    subset["orgnr_bedrift"].ne("")
                    & subset["orgnr_bedrift"].ne("nan")
                ].copy()

                if subset.empty:
                    return [], None

                # Keep the latest available row for each business.
                subset = (
                    subset.sort_values(
                        "year",
                        ascending=False,
                    )
                    .drop_duplicates(
                        subset="orgnr_bedrift",
                        keep="first",
                    )
                )

                options: list[dict[str, str]] = []

                for row in subset.itertuples():
                    business_number = str(
                        row.orgnr_bedrift
                    )

                    business_name = str(
                        getattr(row, "navn", "")
                    ).strip()

                    if (
                        business_name
                        and business_name.lower() != "nan"
                    ):
                        label = (
                            f"{business_name} — "
                            f"{business_number}"
                        )
                    else:
                        label = business_number

                    options.append(
                        {
                            "label": label,
                            "value": business_number,
                        }
                    )

                options = sorted(
                    options,
                    key=lambda option: option["label"].casefold(),
                )

                selected_value = (
                    options[0]["value"]
                    if options
                    else None
                )

                return options, selected_value

            except Exception:
                return [], None

        @callback(
            Output(
                self.breakdown_enterprise_id,
                "value",
            ),
            Input(
                self.breakdown_enterprise_search_id,
                "value",
            ),
            prevent_initial_call=True,
        )
        def select_breakdown_enterprise_from_name(
            selected_enterprise: str | None,
        ) -> str | Any:
            """Copy the selected enterprise into the organisation-number field."""
            if not selected_enterprise:
                return no_update

            return str(selected_enterprise)

        @callback(
            Output(
                self.large_changes_group_value_id,
                "options",
            ),
            Output(
                self.large_changes_group_value_id,
                "value",
            ),
            Input(
                self.large_changes_group_level_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )

        def update_large_changes_group_values(
            group_level: str,
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate industry values for the large-changes table."""
            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter",
                )

                df = self._read_business_data(
                    parquet_path
                )

                if "naring" not in df.columns:
                    return [], None

                data = df.copy()

                data["naring"] = (
                    data["naring"]
                    .astype("string")
                )

                if group_level == "naring_1":
                    if "naring_1" not in data.columns:
                        return [], None

                    group_values = (
                        data["naring_1"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                elif group_level == "naring":
                    group_values = (
                        data["naring"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                else:
                    slice_lengths = {
                        "n2": 2,
                        "n3": 4,
                        "n4": 5,
                        "n5": 6,
                    }

                    if group_level not in slice_lengths:
                        return [], None

                    group_values = (
                        data["naring"]
                        .str.slice(
                            0,
                            slice_lengths[group_level],
                        )
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                group_values = sorted(
                    value
                    for value in group_values
                    if value
                    and value.lower() != "nan"
                )

                options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in group_values
                ]

                selected_value = (
                    group_values[0]
                    if group_values
                    else None
                )

                return options, selected_value

            except Exception:
                return [], None


        @callback(
            Output(
                self.breakdown_group_value_id,
                "options",
            ),
            Output(
                self.breakdown_group_value_id,
                "value",
            ),
            Input(
                self.breakdown_group_level_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )
        def update_breakdown_group_values(
            group_level: str,
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate industry values for the breakdown table."""
            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter",
                )

                df = self._read_business_data(
                    parquet_path
                )

                if "naring" not in df.columns:
                    return [], None

                data = df.copy()

                data["naring"] = (
                    data["naring"]
                    .astype("string")
                )

                if group_level == "naring":
                    group_values = (
                        data["naring"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                else:
                    slice_lengths = {
                        "n2": 2,
                        "n3": 4,
                        "n4": 5,
                    }

                    if group_level not in slice_lengths:
                        return [], None

                    group_values = (
                        data["naring"]
                        .str.slice(
                            0,
                            slice_lengths[group_level],
                        )
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                group_values = sorted(
                    value
                    for value in group_values
                    if value
                    and value.lower() != "nan"
                )

                options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in group_values
                ]

                selected_value = (
                    group_values[0]
                    if group_values
                    else None
                )

                return options, selected_value

            except Exception:
                return [], None


        @callback(
            Output(
                self.moms_naring_filter_id,
                "options",
            ),
            Output(
                self.moms_naring_filter_id,
                "value",
            ),
            Input(
                self.moms_group_level_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )
        def update_moms_naring_options(
            group_level: str,
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            list[str],
        ]:
            """Populate available MOMS industries at the selected level."""
            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="moms",
                )

                df = self._read_generic_data(
                    parquet_path
                )

                if "naring" not in df.columns:
                    return [], []

                valid_lengths = {
                    "n2": 2,
                    "n3": 4,
                    "n4": 5,
                    "n5": 6,
                }

                if group_level not in valid_lengths:
                    return [], []

                exact_length = valid_lengths[group_level]

                naring_values = sorted(
                    df.loc[
                        df["naring"]
                        .astype("string")
                        .str.len()
                        .eq(exact_length),
                        "naring",
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in naring_values
                ]

                # Empty selection means show all.
                return options, []

            except Exception:
                return [], []


        @callback(
            Output(
                self.method_naring_value_id,
                "options",
            ),
            Output(
                self.method_naring_value_id,
                "value",
            ),
            Input(
                self.method_naring_level_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
        )
        def update_method_naring_values(
            naring_level: str,
            data_version: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate industry values for method analysis."""
            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter",
                )

                df = self._read_business_data(
                    parquet_path
                )

                if "naring" not in df.columns:
                    return [], None

                data = df.copy()

                data["naring"] = (
                    data["naring"]
                    .astype("string")
                )

                if naring_level == "naring":
                    group_values = (
                        data["naring"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                else:
                    slice_lengths = {
                        "naring_2": 2,
                        "naring_4": 4,
                        "naring_5": 5,
                    }

                    if naring_level not in slice_lengths:
                        return [], None

                    group_values = (
                        data["naring"]
                        .str.slice(
                            0,
                            slice_lengths[naring_level],
                        )
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                group_values = sorted(
                    value
                    for value in group_values
                    if value
                    and value.lower() != "nan"
                )

                options = [
                    {
                        "label": value,
                        "value": value,
                    }
                    for value in group_values
                ]

                selected_value = (
                    group_values[0]
                    if group_values
                    else None
                )

                return options, selected_value

            except Exception:
                return [], None

        @callback(
            Output(self.graph_title_id, "children"),
            Output(self.graph_description_id, "children"),
            Output(self.single_naring_container_id, "style"),
            Output(self.multi_naring_container_id, "style"),
            Output(self.enterprise_container_id, "style"),
            Output(self.change_controls_container_id, "style"),
            Output(self.single_variable_container_id, "style"),
            Output(self.multi_variable_container_id, "style"),
            Output(self.noku_controls_container_id, "style"),
            Output(
                self.large_changes_controls_container_id,
                "style",
            ),
            Output(
                self.negative_nopost_controls_container_id,
                "style",
            ),
            Output(self.nr_controls_container_id, "style"),
            Output(self.opposite_controls_container_id, "style"),
            Output(self.breakdown_controls_container_id, "style"),
            Output(self.moms_controls_container_id, "style"),
            Output(self.movement_controls_container_id, "style"),
            Output(self.method_controls_container_id, "style"),
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
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
            dict[str, str],
        ]:
            hidden = {"display": "none"}
            visible = {"display": "block"}

            visualisation_text = {
                "trend-single": (
                    TREND_SINGLE_LABEL,
                    (
                        "Viser utviklingen over tid sammen med forventet "
                        "variasjonsområde basert på historiske endringer."
                    ),
                ),
                "trend-multi": (
                    TREND_MULTI_LABEL,
                    (
                        "Sammenligner utviklingen i flere valgte variabler "
                        "for samme næring over tid."
                    ),
                ),
                "trend-industries": (
                    TREND_INDUSTRIES_LABEL,
                    (
                        "Sammenligner utviklingen i én valgt variabel "
                        "for flere næringer over tid."
                    ),
                ),
                "trend-enterprise": (
                    "Trendanalyse – enkeltforetak",
                    (
                        "Viser utviklingen i én valgt variabel "
                        "for ett foretak over tid."
                    ),
                ),
                "change-share": (
                    "Prosentandeler av endringene",
                    (
                        "Viser hvilke foretak som bidrar mest til "
                        "endringen i valgt variabel fra året før."
                    ),
                ),
                "noku-table": (
                    "NØKU-tabell",
                    (
                        "Viser store næringsendringer og vurderer dem mot "
                        "historisk variasjon. Ved avvik vises de største "
                        "bidragene fra bedrift og foretak."
                    ),
                ),
                "large-changes": (
                    "Store endringer",
                    (
                        "Viser bedrifter med de største endringene fra "
                        "året før for valgte variabler."
                    ),
                ),
                "negative-nopost": (
                    "Negative NO-poster",
                    (
                        "Viser næringsgrupper der en eller flere "
                        "NO-poster har en vesentlig negativ verdi."
                    ),
                ),
                "nr-controls": (
                    "NR-kontroller",
                    (
                        "Viser negative restverdier fra logiske "
                        "NR-kontroller aggregert etter næring."
                    ),
                ),
                "opposite-direction": (
                    "Motsatte bevegelser",
                    (
                        "Finner næringsgrupper der relaterte variabler "
                        "beveger seg i motsatt retning fra året før."
                    ),
                ),
                "breakdown": (
                    "Sammensatte variabler",
                    (
                        "Bryter en sammensatt variabel ned i postene som "
                        "inngår, og sammenligner valgt år med året før."
                    ),
                ),
                "moms": (
                    "Mot MOMS",
                    (
                        "Sammenligner antall, sysselsetting, omsetning og "
                        "MOMS mellom to år."
                    ),
                ),
                "movement": (
                    "Tilgang og avgang",
                    (
                        "Viser bedrifter som har kommet inn, gått ut eller "
                        "endret næringskode mellom to år."
                    ),
                ),
                "method-analysis": (
                    "Metodeanalyse",
                    (
                        "Sammenligner valgte rater over tid mellom "
                        "type S og øvrige typer."
                    ),
                ),
            }

            title, description = visualisation_text.get(
                visualisation,
                (
                    VL_VISUALISATIONS.get(
                        visualisation,
                        "VL-visualisering",
                    ),
                    "Velg kontroller for visualiseringen.",
                ),
            )

            styles = {
                "single_naring": hidden,
                "multi_naring": hidden,
                "enterprise": hidden,
                "change": hidden,
                "single_variable": hidden,
                "multi_variable": hidden,
                "noku": hidden,
                "large_changes": hidden,
                "negative_nopost": hidden,
                "nr": hidden,
                "opposite": hidden,
                "breakdown": hidden,
                "moms": hidden,
                "movement": hidden,
                "method": hidden,
            }

            if visualisation == "trend-single":
                styles["single_naring"] = visible
                styles["single_variable"] = visible

            elif visualisation == "trend-multi":
                styles["single_naring"] = visible
                styles["multi_variable"] = visible

            elif visualisation == "trend-industries":
                styles["multi_naring"] = visible
                styles["single_variable"] = visible

            elif visualisation == "trend-enterprise":
                styles["enterprise"] = visible
                styles["single_variable"] = visible

            elif visualisation == "change-share":
                styles["single_naring"] = visible
                styles["single_variable"] = visible
                styles["change"] = visible

            elif visualisation == "noku-table":
                styles["noku"] = visible

            elif visualisation == "large-changes":
                styles["large_changes"] = visible

            elif visualisation == "negative-nopost":
                styles["negative_nopost"] = visible

            elif visualisation == "nr-controls":
                styles["nr"] = visible

            elif visualisation == "opposite-direction":
                styles["opposite"] = visible

            elif visualisation == "breakdown":
                styles["breakdown"] = visible

            elif visualisation == "moms":
                styles["moms"] = visible

            elif visualisation == "movement":
                styles["movement"] = visible

            elif visualisation == "method-analysis":
                styles["method"] = visible

            return (
                title,
                description,
                styles["single_naring"],
                styles["multi_naring"],
                styles["enterprise"],
                styles["change"],
                styles["single_variable"],
                styles["multi_variable"],
                styles["noku"],
                styles["large_changes"],
                styles["negative_nopost"],
                styles["nr"],
                styles["opposite"],
                styles["breakdown"],
                styles["moms"],
                styles["movement"],
                styles["method"],
            )

###############################################################################

        @callback(
            Output(
                self.breakdown_industry_controls_id,
                "style",
            ),
            Output(
                self.breakdown_enterprise_controls_id,
                "style",
            ),
            Input(
                self.breakdown_analysis_level_id,
                "value",
            ),
        )
        def toggle_breakdown_analysis_level(
            analysis_level: str,
        ) -> tuple[
            dict[str, str],
            dict[str, str],
        ]:
            """Switch between industry and enterprise breakdown controls."""
            visible = {
                "display": "block",
                "marginTop": "12px",
            }

            hidden = {
                "display": "none",
                "marginTop": "12px",
            }

            if analysis_level == "enterprise":
                return hidden, visible

            return visible, hidden

################################################################################
        @callback(
            Output(
                self.negative_nopost_drilldown_container_id,
                "style",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
        )
        def toggle_negative_nopost_drilldown(
            visualisation: str,
        ) -> dict[str, str]:
            """Show the drilldown only for Negative NO-poster."""
            if visualisation == "negative-nopost":
                return {
                    "display": "block",
                    "marginTop": "24px",
                    "paddingTop": "20px",
                    "borderTop": "1px solid #d9d9d9",
                }

            return {
                "display": "none",
                "marginTop": "24px",
                "paddingTop": "20px",
                "borderTop": "1px solid #d9d9d9",
            }

        @callback(
            Output(
                self.nr_drilldown_container_id,
                "style",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
        )
        def toggle_nr_drilldown(
            visualisation: str,
        ) -> dict[str, str]:
            """Show the drilldown only for NR controls."""
            if visualisation == "nr-controls":
                return {
                    "display": "block",
                    "marginTop": "24px",
                    "paddingTop": "20px",
                    "borderTop": "1px solid #d9d9d9",
                }

            return {
                "display": "none",
                "marginTop": "24px",
                "paddingTop": "20px",
                "borderTop": "1px solid #d9d9d9",
            }

        @callback(
            Output(
                self.nr_selected_group_id,
                "options",
            ),
            Output(
                self.nr_selected_group_id,
                "value",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
            Input(
                self.table_id,
                "data",
            ),
            Input(
                self.nr_group_level_id,
                "value",
            ),
            Input(
                self.nr_view_id,
                "value",
            ),
            Input(
                self.nr_threshold_id,
                "value",
            ),
        )
        def update_nr_group_options(
            visualisation: str,
            table_data: list[dict[str, Any]] | None,
            group_level: str | None,
            view: str | None,
            negative_threshold: float | None,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate NR drilldown rows from the visible table."""
            if (
                visualisation != "nr-controls"
                or not table_data
            ):
                return [], None

            selected_group_level = (
                group_level or "naring"
            )

            selected_view = view or "Land"

            threshold = abs(
                float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )
            )

            check_columns = [
                "p4005_forb",
                "dr_vk_lo",
                "dr_forb_lo",
                "prins_vk_forb",
                "oms_salgsint",
                "nosalg_tssalg",
                "bearbeidingsverdi",
            ]

            options: list[dict[str, str]] = []

            for row in table_data:
                group_value = row.get(
                    selected_group_level
                )

                if group_value is None:
                    continue

                negative_checks = [
                    column
                    for column in check_columns
                    if (
                        row.get(column) is not None
                        and pd.to_numeric(
                            row.get(column),
                            errors="coerce",
                        )
                        < -threshold
                    )
                ]

                if not negative_checks:
                    continue

                if selected_view == "Fylke":
                    fylke_value = row.get("fylke")

                    if fylke_value is None:
                        continue

                    option_value = (
                        f"{group_value}||{fylke_value}"
                    )

                    label = (
                        f"{group_value} | fylke={fylke_value} "
                        f"({len(negative_checks)} negative kontroller)"
                    )

                else:
                    option_value = str(group_value)

                    label = (
                        f"{group_value} "
                        f"({len(negative_checks)} negative kontroller)"
                    )

                options.append(
                    {
                        "label": label,
                        "value": option_value,
                    }
                )

            selected_value = (
                options[0]["value"]
                if options
                else None
            )

            return options, selected_value

        @callback(
            Output(
                self.nr_variable_id,
                "options",
            ),
            Output(
                self.nr_variable_id,
                "value",
            ),
            Input(
                self.nr_selected_group_id,
                "value",
            ),
            Input(
                self.table_id,
                "data",
            ),
            Input(
                self.nr_group_level_id,
                "value",
            ),
            Input(
                self.nr_view_id,
                "value",
            ),
            Input(
                self.nr_threshold_id,
                "value",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
        )
        def update_nr_variable_options(
            selected_group: str | None,
            table_data: list[dict[str, Any]] | None,
            group_level: str | None,
            view: str | None,
            negative_threshold: float | None,
            visualisation: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Show only negative checks for the selected NR row."""
            if (
                visualisation != "nr-controls"
                or not selected_group
                or not table_data
            ):
                return [], None

            selected_group_level = (
                group_level or "naring"
            )

            selected_view = view or "Land"

            threshold = abs(
                float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )
            )

            if selected_view == "Fylke":
                try:
                    selected_group_value, selected_fylke = (
                        str(selected_group).split("||", 1)
                    )
                except ValueError:
                    return [], None

                selected_row = next(
                    (
                        row
                        for row in table_data
                        if (
                            str(
                                row.get(
                                    selected_group_level
                                )
                            )
                            == selected_group_value
                            and str(
                                row.get("fylke")
                            )
                            == selected_fylke
                        )
                    ),
                    None,
                )

            else:
                selected_row = next(
                    (
                        row
                        for row in table_data
                        if str(
                            row.get(
                                selected_group_level
                            )
                        )
                        == str(selected_group)
                    ),
                    None,
                )

            if selected_row is None:
                return [], None

            check_columns = [
                "p4005_forb",
                "dr_vk_lo",
                "dr_forb_lo",
                "prins_vk_forb",
                "oms_salgsint",
                "nosalg_tssalg",
                "bearbeidingsverdi",
            ]

            negative_checks = [
                check
                for check in check_columns
                if (
                    selected_row.get(check) is not None
                    and pd.to_numeric(
                        selected_row.get(check),
                        errors="coerce",
                    )
                    < -threshold
                )
            ]

            options = [
                {
                    "label": check,
                    "value": check,
                }
                for check in negative_checks
            ]

            selected_value = (
                negative_checks[0]
                if negative_checks
                else None
            )

            return options, selected_value

        @callback(
            Output(
                self.nr_drilldown_table_id,
                "data",
            ),
            Output(
                self.nr_drilldown_table_id,
                "columns",
            ),
            Output(
                self.nr_drilldown_table_id,
                "style_data_conditional",
            ),
            Output(
                self.nr_drilldown_table_id,
                "tooltip_data",
            ),
            Output(
                self.nr_drilldown_message_id,
                "children",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
            Input(
                self.nr_year_id,
                "value",
            ),
            Input(
                self.nr_group_level_id,
                "value",
            ),
            Input(
                self.nr_view_id,
                "value",
            ),
            Input(
                self.nr_selected_group_id,
                "value",
            ),
            Input(
                self.nr_variable_id,
                "value",
            ),
            Input(
                self.nr_threshold_id,
                "value",
            ),
            Input(
                self.nr_top_enterprises_id,
                "value",
            ),
        )
        def update_nr_drilldown(
            visualisation: str,
            data_version: str,
            year: int | None,
            group_level: str | None,
            view: str | None,
            selected_group: str | None,
            check: str | None,
            negative_threshold: float | None,
            top_enterprises: int | None,
        ) -> tuple[
            list[dict[str, Any]],
            list[dict[str, Any]],
            list[dict[str, Any]],
            list[dict[str, Any]],
            Any,
        ]:
            """Build the enterprise drilldown for a negative NR control."""

            empty_result = (
                [],
                [],
                [],
                [],
                "",
            )

            if visualisation != "nr-controls":
                return empty_result

            if year is None:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg et år.",
                )

            if not selected_group:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg en rad.",
                )

            if not check:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg en negativ kontroll.",
                )

            selected_view = view or "Land"
            selected_group_level = group_level or "naring"

            group_value = str(selected_group)
            fylke_value: str | None = None

            if selected_view == "Fylke":
                try:
                    group_value, fylke_value = (
                        str(selected_group).split("||", 1)
                    )
                except ValueError:
                    return (
                        [],
                        [],
                        [],
                        [],
                        "Kunne ikke tolke valgt næring og fylke.",
                    )

            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter_recent_med_nopost",
                )

                df = self._read_generic_data(
                    parquet_path
                )

                threshold = float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )

                table_df = self._create_nr_drilldown_data(
                    df=df,
                    year=int(year),
                    group_level=selected_group_level,
                    group_value=group_value,
                    check=check,
                    view=selected_view,
                    fylke=fylke_value,
                    negative_threshold=threshold,
                    top_enterprises=int(
                        top_enterprises or 50
                    ),
                )

                if table_df.empty:
                    location_text = (
                        f" og fylke {fylke_value}"
                        if fylke_value is not None
                        else ""
                    )

                    return (
                        [],
                        [],
                        [],
                        [],
                        (
                            "Fant ingen foretak med kontrollverdi "
                            f"under -{abs(threshold):,.0f} for "
                            f"{check} i næring {group_value}"
                            f"{location_text}."
                        ).replace(",", " "),
                    )

                (
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                ) = self._prepare_table_output(
                    table_df
                )

                message_parts: list[Any] = [
                    html.Strong(
                        f"Næring: {group_value}"
                    ),
                ]

                if fylke_value is not None:
                    message_parts.extend(
                        [
                            html.Span(" · "),
                            html.Strong(
                                f"Fylke: {fylke_value}"
                            ),
                        ]
                    )

                message_parts.extend(
                    [
                        html.Span(" · "),
                        html.Strong(
                            f"Kontroll: {check}"
                        ),
                        html.Span(" · "),
                        html.Span(
                            (
                                f"Viser {len(table_df)} foretak "
                                f"med verdi under "
                                f"-{abs(threshold):,.0f}"
                            ).replace(",", " ")
                        ),
                    ]
                )

                message = html.Div(
                    message_parts
                )

                return (
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                    message,
                )

            except Exception as error:
                return (
                    [],
                    [],
                    [],
                    [],
                    html.Div(
                        (
                            "Kunne ikke lage NR-drilldown: "
                            f"{error}"
                        ),
                        className="alert alert-danger",
                    ),
                )

        @callback(
            Output(
                self.negative_nopost_selected_group_id,
                "options",
            ),
            Output(
                self.negative_nopost_selected_group_id,
                "value",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
            Input(
                self.table_id,
                "data",
            ),
            Input(
                self.negative_nopost_group_level_id,
                "value",
            ),
            Input(
                self.negative_nopost_threshold_id,
                "value",
            ),
        )
        def update_negative_nopost_group_options(
            visualisation: str,
            table_data: list[dict[str, Any]] | None,
            group_level: str | None,
            negative_threshold: float | None,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Populate drilldown groups from the visible summary table."""
            if (
                visualisation != "negative-nopost"
                or not table_data
            ):
                return [], None

            selected_group_level = (
                group_level or "naring"
            )

            threshold = abs(
                float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )
            )

            options: list[dict[str, str]] = []

            for row in table_data:
                group_value = row.get(
                    selected_group_level
                )

                if group_value is None:
                    continue

                negative_columns = [
                    column
                    for column, value in row.items()
                    if (
                        column.startswith("nopost_")
                        and value is not None
                        and pd.to_numeric(
                            value,
                            errors="coerce",
                        )
                        < -threshold
                    )
                ]

                label = (
                    f"{group_value} "
                    f"(negative poster: "
                    f"{len(negative_columns)})"
                )

                options.append(
                    {
                        "label": label,
                        "value": str(group_value),
                    }
                )

            selected_value = (
                options[0]["value"]
                if options
                else None
            )

            return options, selected_value

        @callback(
            Output(
                self.negative_nopost_variable_id,
                "options",
            ),
            Output(
                self.negative_nopost_variable_id,
                "value",
            ),
            Input(
                self.negative_nopost_selected_group_id,
                "value",
            ),
            Input(
                self.table_id,
                "data",
            ),
            Input(
                self.negative_nopost_group_level_id,
                "value",
            ),
            Input(
                self.negative_nopost_threshold_id,
                "value",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
        )
        def update_negative_nopost_variable_options(
            selected_group: str | None,
            table_data: list[dict[str, Any]] | None,
            group_level: str | None,
            negative_threshold: float | None,
            visualisation: str,
        ) -> tuple[
            list[dict[str, str]],
            str | None,
        ]:
            """Show only negative NO-posts for the selected group."""
            if (
                visualisation != "negative-nopost"
                or not selected_group
                or not table_data
            ):
                return [], None

            selected_group_level = (
                group_level or "naring"
            )

            threshold = abs(
                float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )
            )

            selected_row = next(
                (
                    row
                    for row in table_data
                    if str(
                        row.get(
                            selected_group_level
                        )
                    )
                    == str(selected_group)
                ),
                None,
            )

            if selected_row is None:
                return [], None

            negative_variables = [
                column
                for column, value in selected_row.items()
                if (
                    column.startswith("nopost_")
                    and value is not None
                    and pd.to_numeric(
                        value,
                        errors="coerce",
                    )
                    < -threshold
                )
            ]

            options = [
                {
                    "label": variable,
                    "value": variable,
                }
                for variable in negative_variables
            ]

            selected_value = (
                negative_variables[0]
                if negative_variables
                else None
            )

            return options, selected_value

        @callback(
            Output(
                self.negative_nopost_drilldown_table_id,
                "data",
            ),
            Output(
                self.negative_nopost_drilldown_table_id,
                "columns",
            ),
            Output(
                self.negative_nopost_drilldown_table_id,
                "style_data_conditional",
            ),
            Output(
                self.negative_nopost_drilldown_table_id,
                "tooltip_data",
            ),
            Output(
                self.negative_nopost_drilldown_message_id,
                "children",
            ),
            Input(
                self.visualisation_id,
                "value",
            ),
            Input(
                self.data_version_id,
                "value",
            ),
            Input(
                self.negative_nopost_year_id,
                "value",
            ),
            Input(
                self.negative_nopost_group_level_id,
                "value",
            ),
            Input(
                self.negative_nopost_selected_group_id,
                "value",
            ),
            Input(
                self.negative_nopost_variable_id,
                "value",
            ),
            Input(
                self.negative_nopost_threshold_id,
                "value",
            ),
            Input(
                self.negative_nopost_top_enterprises_id,
                "value",
            ),
        )
        def update_negative_nopost_drilldown(
            visualisation: str,
            data_version: str,
            year: int | None,
            group_level: str | None,
            selected_group: str | None,
            variable: str | None,
            negative_threshold: float | None,
            top_enterprises: int | None,
        ) -> tuple[
            list[dict[str, Any]],
            list[dict[str, Any]],
            list[dict[str, Any]],
            list[dict[str, Any]],
            Any,
        ]:
            """Build the enterprise drilldown for a negative NO-post."""
            empty_result = (
                [],
                [],
                [],
                [],
                "",
            )

            if visualisation != "negative-nopost":
                return empty_result

            if year is None:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg et år.",
                )

            if not selected_group:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg en næringsgruppe.",
                )

            if not variable:
                return (
                    [],
                    [],
                    [],
                    [],
                    "Velg en negativ NO-post.",
                )

            try:
                parquet_path = self._parquet_path(
                    data_version,
                    dataset="bedrifter_recent_med_nopost",
                )

                df = self._read_generic_data(
                    parquet_path
                )

                threshold = float(
                    negative_threshold
                    if negative_threshold is not None
                    else 1000
                )

                table_df = (
                    self._create_negative_nopost_drilldown_data(
                        df=df,
                        year=int(year),
                        group_level=(
                            group_level or "naring"
                        ),
                        group_value=str(selected_group),
                        variable=variable,
                        negative_threshold=threshold,
                        top_enterprises=int(
                            top_enterprises or 50
                        ),
                    )
                )

                if table_df.empty:
                    return (
                        [],
                        [],
                        [],
                        [],
                        (
                            "Fant ingen foretak med verdier "
                            f"under -{abs(threshold):,.0f} "
                            f"for {variable} i næringsgruppe "
                            f"{selected_group}."
                        ).replace(",", " "),
                    )

                (
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                ) = self._prepare_table_output(
                    table_df
                )

                message = html.Div(
                    [
                        html.Strong(
                            f"Næringsgruppe: {selected_group}"
                        ),
                        html.Span(" · "),
                        html.Strong(
                            f"Variabel: {variable}"
                        ),
                        html.Span(" · "),
                        html.Span(
                            (
                                f"Viser {len(table_df)} foretak "
                                f"med verdi under "
                                f"-{abs(threshold):,.0f}"
                            ).replace(",", " ")
                        ),
                    ]
                )

                return (
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                    message,
                )

            except Exception as error:
                return (
                    [],
                    [],
                    [],
                    [],
                    html.Div(
                        (
                            "Kunne ikke lage drilldown: "
                            f"{error}"
                        ),
                        className="alert alert-danger",
                    ),
                )


################################################################################            
########
        @callback(
            Output(self.graph_id, "figure"),
            Output(self.graph_container_id, "style"),
            Output(self.table_id, "data"),
            Output(self.table_id, "columns"),
            Output(
                self.table_id,
                "style_data_conditional",
            ),
            Output(self.table_id, "tooltip_data"),
            Output(self.table_container_id, "style"),
            Output(
                self.large_changes_summary_id,
                "children",
            ),
            Output(
                self.large_changes_summary_id,
                "style",
            ),
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

            Input(self.noku_group_id, "value"),
            Input(self.noku_year_id, "value"),
            Input(self.noku_rate_id, "value"),
            Input(self.noku_window_id, "value"),
            Input(
                self.noku_standard_deviations_id,
                "value",
            ),

            Input(
                self.large_changes_year_id,
                "value",
            ),
            Input(
                self.large_changes_group_level_id,
                "value",
            ),
            Input(
                self.large_changes_group_value_id,
                "value",
            ),
            Input(
                self.large_changes_variables_id,
                "value",
            ),
            Input(
                self.large_changes_fylke_id,
                "value",
            ),
            Input(
                self.large_changes_top_n_id,
                "value",
            ),

            Input(
                self.negative_nopost_year_id,
                "value",
            ),
            Input(
                self.negative_nopost_group_level_id,
                "value",
            ),
            Input(
                self.negative_nopost_threshold_id,
                "value",
            ),
            Input(
                self.negative_nopost_hide_columns_id,
                "value",
            ),
            Input(
                self.negative_nopost_max_rows_id,
                "value",
            ),

            Input(self.nr_year_id, "value"),
            Input(self.nr_group_level_id, "value"),
            Input(self.nr_view_id, "value"),
            Input(self.nr_threshold_id, "value"),
            Input(self.nr_hide_columns_id, "value"),
            Input(self.nr_max_rows_id, "value"),

            Input(self.opposite_year_id, "value"),
            Input(
                self.opposite_group_level_id,
                "value",
            ),
            Input(self.opposite_view_id, "value"),
            Input(self.opposite_rule_id, "value"),
            Input(
                self.opposite_min_count_id,
                "value",
            ),
            Input(
                self.opposite_gap_threshold_id,
                "value",
            ),
            Input(
                self.opposite_absolute_threshold_id,
                "value",
            ),
            Input(
                self.opposite_max_rows_id,
                "value",
            ),

            Input(
                self.breakdown_analysis_level_id,
                "value",
            ),
            Input(self.breakdown_year_id, "value"),
            Input(
                self.breakdown_group_level_id,
                "value",
            ),
            Input(
                self.breakdown_group_value_id,
                "value",
            ),
            Input(
                self.breakdown_enterprise_id,
                "value",
            ),
            Input(
                self.breakdown_unit_level_id,
                "value",
            ),
            Input(
                self.breakdown_business_id,
                "value",
            ),
            Input(
                self.breakdown_variable_id,
                "value",
            ),

            Input(self.moms_group_level_id, "value"),

            Input(self.moms_naring_filter_id, "value"),

            Input(
                self.moms_previous_year_id,
                "value",
            ),
            Input(
                self.moms_current_year_id,
                "value",
            ),

            Input(
                self.movement_direction_id,
                "value",
            ),
            Input(
                self.movement_variable_id,
                "value",
            ),
            Input(
                self.movement_group_level_id,
                "value",
            ),
            Input(
                self.movement_code_filter_id,
                "value",
            ),
            Input(
                self.movement_exact_match_id,
                "value",
            ),
            Input(
                self.movement_top_n_id,
                "value",
            ),

            Input(
                self.method_naring_level_id,
                "value",
            ),
            Input(
                self.method_naring_value_id,
                "value",
            ),
            Input(self.method_ratios_id, "value"),
            Input(
                self.method_reg_types_id,
                "value",
            ),
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

            noku_group: str | None,
            noku_year: int | None,
            noku_rate: float | None,
            noku_window: int | None,
            noku_standard_deviations: float | None,

            large_changes_year: int | None,
            large_changes_group_level: str | None,
            large_changes_group_value: str | None,
            large_changes_variable: str | None,
            large_changes_fylke: str | None,
            large_changes_top_n: int | None,

            negative_nopost_year: int | None,
            negative_nopost_group_level: str | None,
            negative_nopost_threshold: float | None,
            negative_nopost_hide_columns: list[str] | None,
            negative_nopost_max_rows: int | None,

            nr_year: int | None,
            nr_group_level: str | None,
            nr_view: str | None,
            nr_threshold: float | None,
            nr_hide_columns: list[str] | None,
            nr_max_rows: int | None,

            opposite_year: int | None,
            opposite_group_level: str | None,
            opposite_view: str | None,
            opposite_rule: str | None,
            opposite_min_count: int | None,
            opposite_gap_threshold: float | None,
            opposite_absolute_threshold: float | None,
            opposite_max_rows: int | None,

            breakdown_analysis_level: str | None,
            breakdown_year: int | None,
            breakdown_group_level: str | None,
            breakdown_group_value: str | None,
            breakdown_enterprise: str | None,
            breakdown_unit_level: str | None,
            breakdown_business: str | None,
            breakdown_variable: str | None,

            moms_group_level: str | None,
            moms_naring_filter: list[str] | None,
            moms_previous_year: int | None,
            moms_current_year: int | None,

            movement_direction: str | None,
            movement_variable: str | None,
            movement_group_level: str | None,
            movement_code_filter: str | None,
            movement_exact_match: list[str] | None,
            movement_top_n: int | None,

            method_naring_level: str | None,
            method_naring_value: str | None,
            method_ratios: list[str] | None,
            method_reg_types: list[str] | None,
        ) -> tuple[Any, ...]:
            graph_visible_style = {
                "display": "block",
                "width": "100%",
            }

            graph_hidden_style = {
                "display": "none",
                "width": "100%",
            }

            table_visible_style = {
                "display": "block",
                "width": "100%",
                "padding": "16px",
            }

            table_hidden_style = {
                "display": "none",
                "width": "100%",
                "padding": "16px",
            }

            section_style = {
                "display": "block",
                "width": "100%",
                "maxWidth": "none",
            }

            def figure_result(
                figure: go.Figure,
            ) -> tuple[Any, ...]:
                return (
                    figure,
                    graph_visible_style,
                    [],
                    [],
                    [],
                    [],
                    table_hidden_style,
                    [],
                    {
                        "display": "none",
                        "marginBottom": "16px",
                    },
                    section_style,
                )
            def table_result(
                table_df: pd.DataFrame,
                empty_message: str,
                summary_card: Any | None = None,
                extra_styles: list[dict[str, Any]] | None = None,
            ) -> tuple[Any, ...]:
                if table_df.empty:
                    figure = self._empty_figure(
                        empty_message
                    )

                    return figure_result(figure)

                (
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                ) = self._prepare_table_output(
                    table_df
                )

                if extra_styles:
                    table_styles.extend(extra_styles)

                if summary_card is None:
                    summary_children: Any = []

                    summary_style = {
                        "display": "none",
                        "marginBottom": "16px",
                    }

                else:
                    summary_children = summary_card

                    summary_style = {
                        "display": "block",
                        "marginBottom": "16px",
                    }

                return (
                    go.Figure(),
                    graph_hidden_style,
                    table_data,
                    table_columns,
                    table_styles,
                    table_tooltips,
                    table_visible_style,
                    summary_children,
                    summary_style,
                    section_style,
                )

            try:
                # -----------------------------------------
                # Trend: one variable
                # -----------------------------------------
                if visualisation == "trend-single":
                    if not naring:
                        return figure_result(
                            self._empty_figure(
                                "Velg en næring."
                            )
                        )

                    if not variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en variabel."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="agg_naring4",
                    )

                    df = self._read_data(
                        parquet_path
                    )

                    if variable not in df.columns:
                        return figure_result(
                            self._empty_figure(
                                (
                                    f"Variabelen {variable} "
                                    "finnes ikke i datasettet."
                                )
                            )
                        )

                    figure = self._create_trend_figure(
                        df=df,
                        naring=naring,
                        variable=variable,
                    )

                    return figure_result(figure)

                # -----------------------------------------
                # Trend: multiple variables
                # -----------------------------------------
                if visualisation == "trend-multi":
                    if not naring:
                        return figure_result(
                            self._empty_figure(
                                "Velg en næring."
                            )
                        )

                    if not multi_variables:
                        return figure_result(
                            self._empty_figure(
                                "Velg minst én variabel."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="agg_naring4",
                    )

                    df = self._read_data(
                        parquet_path
                    )

                    missing_variables = [
                        selected_variable
                        for selected_variable
                        in multi_variables
                        if selected_variable
                        not in df.columns
                    ]

                    if missing_variables:
                        return figure_result(
                            self._empty_figure(
                                (
                                    "Disse variablene finnes "
                                    "ikke i datasettet: "
                                    f"{missing_variables}"
                                )
                            )
                        )

                    figure = (
                        self._create_multi_trend_figure(
                            df=df,
                            naring=naring,
                            variables=multi_variables,
                        )
                    )

                    return figure_result(figure)

                # -----------------------------------------
                # Trend: multiple industries
                # -----------------------------------------
                if visualisation == "trend-industries":
                    if not multi_narings:
                        return figure_result(
                            self._empty_figure(
                                "Velg minst én næring."
                            )
                        )

                    if not variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en variabel."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="agg_naring4",
                    )

                    df = self._read_data(
                        parquet_path
                    )

                    if variable not in df.columns:
                        return figure_result(
                            self._empty_figure(
                                (
                                    f"Variabelen {variable} "
                                    "finnes ikke i datasettet."
                                )
                            )
                        )

                    figure = (
                        self._create_industry_trend_figure(
                            df=df,
                            narings=multi_narings,
                            variable=variable,
                        )
                    )

                    return figure_result(figure)

                # -----------------------------------------
                # Trend: enterprise
                # -----------------------------------------
                if visualisation == "trend-enterprise":
                    if not enterprise:
                        return figure_result(
                            self._empty_figure(
                                "Velg et foretak."
                            )
                        )

                    if not variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en variabel."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="foretak",
                    )

                    df = self._read_enterprise_data(
                        parquet_path
                    )

                    if variable not in df.columns:
                        return figure_result(
                            self._empty_figure(
                                (
                                    f"Variabelen {variable} "
                                    "finnes ikke i foretaksdataene."
                                )
                            )
                        )

                    figure = (
                        self._create_enterprise_trend_figure(
                            df=df,
                            enterprise=str(enterprise),
                            variable=variable,
                        )
                    )

                    return figure_result(figure)

                # -----------------------------------------
                # Change share
                # -----------------------------------------
                if visualisation == "change-share":
                    if not naring:
                        return figure_result(
                            self._empty_figure(
                                "Velg en næring."
                            )
                        )

                    if not variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en variabel."
                            )
                        )

                    if change_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )

                    df = self._read_business_data(
                        parquet_path
                    )

                    if variable not in df.columns:
                        return figure_result(
                            self._empty_figure(
                                (
                                    f"Variabelen {variable} "
                                    "finnes ikke i bedriftsdataene."
                                )
                            )
                        )

                    figure = (
                        self._create_change_share_figure(
                            df=df,
                            naring=naring,
                            variable=variable,
                            year=int(change_year),
                            top_n=int(
                                change_top_n or 10
                            ),
                        )
                    )

                    return figure_result(figure)

                # -----------------------------------------
                # NØKU table
                # -----------------------------------------
                if visualisation == "noku-table":
                    if noku_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    aggregate_path = self._parquet_path(
                        data_version,
                        dataset="agg_naring4",
                    )

                    business_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )

                    aggregate_df = self._read_data(
                        aggregate_path
                    )

                    business_df = (
                        self._read_business_data(
                            business_path
                        )
                    )

                    table_df = (
                        self._create_noku_table_data(
                            aggregate_df=aggregate_df,
                            business_df=business_df,
                            year=int(noku_year),
                            rate=float(
                                noku_rate
                                if noku_rate is not None
                                else 20
                            ),
                            window=int(
                                noku_window
                                if noku_window is not None
                                else 5
                            ),
                            standard_deviations=float(
                                noku_standard_deviations
                                if (
                                    noku_standard_deviations
                                    is not None
                                )
                                else 2.5
                            ),
                            naring_col="naring_4",
                        )
                    )

                    if not table_df.empty:
                        table_df = table_df.copy()

                        table_df.insert(
                            1,
                            "gruppe",
                            table_df["naring_4"].map(
                                lambda naring_value: (
                                    self._classify_noku_group(
                                        naring_value,
                                        int(noku_year),
                                    )
                                )
                            ),
                        )

                        if (
                            noku_group
                            and noku_group != "Alle"
                        ):
                            table_df = (
                                table_df.loc[
                                    table_df["gruppe"]
                                    == noku_group
                                ]
                                .reset_index(drop=True)
                            )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen store endringer "
                            "for de valgte grensene."
                        ),
                    )

                # -----------------------------------------
                # Large changes
                # -----------------------------------------
                if visualisation == "large-changes":
                    if large_changes_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    if not large_changes_group_level:
                        return figure_result(
                            self._empty_figure(
                                "Velg et næringsnivå."
                            )
                        )

                    if not large_changes_group_value:
                        return figure_result(
                            self._empty_figure(
                                "Velg en næringskode."
                            )
                        )

                    if not large_changes_variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en variabel."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )

                    df = self._read_business_data(
                        parquet_path
                    )

                    table_df = (
                        self._create_large_changes_data(
                            df=df,
                            year=int(
                                large_changes_year
                            ),
                            group_level=(
                                large_changes_group_level
                            ),
                            group_value=(
                                large_changes_group_value
                            ),
                            variables=[
                                large_changes_variable
                            ],
                            fylke=(
                                large_changes_fylke
                                or "Land"
                            ),
                            top_n=int(
                                large_changes_top_n
                                or 50
                            ),
                        )
                    )

                    summary_data, ratio_df = (
                        self._create_large_changes_summary_data(
                            df=df,
                            year=int(
                                large_changes_year
                            ),
                            group_level=(
                                large_changes_group_level
                            ),
                            group_value=(
                                large_changes_group_value
                            ),
                            variable=(
                                large_changes_variable
                            ),
                            fylke=(
                                large_changes_fylke
                                or "Land"
                            ),
                        )
                    )

                    summary_card = (
                        self._create_large_changes_summary_card(
                            summary=summary_data,
                            ratio_df=ratio_df,
                        )
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen bedrifter med "
                            "beregnbare endringer."
                        ),
                        summary_card=summary_card,
                    )

                # -----------------------------------------
                # Negative NO posts
                # -----------------------------------------
                if visualisation == "negative-nopost":
                    if negative_nopost_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset=(
                            "bedrifter_recent_med_nopost"
                        ),
                    )

                    df = self._read_generic_data(
                        parquet_path
                    )

                    table_df = (
                        self._create_negative_nopost_data(
                            df=df,
                            year=int(
                                negative_nopost_year
                            ),
                            group_level=(
                                negative_nopost_group_level
                                or "naring"
                            ),
                            negative_threshold=float(
                                negative_nopost_threshold
                                if (
                                    negative_nopost_threshold
                                    is not None
                                )
                                else 1000
                            ),
                            hide_nonnegative_columns=(
                                "hide"
                                in (
                                    negative_nopost_hide_columns
                                    or []
                                )
                            ),
                            max_rows=int(
                                negative_nopost_max_rows
                                or 300
                            ),
                        )
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen næringsgrupper "
                            "med negative NO-poster."
                        ),
                    )

                # -----------------------------------------
                # NR controls
                # -----------------------------------------
                if visualisation == "nr-controls":
                    if nr_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter_recent_med_nopost",
                    )

                    df = self._read_generic_data(
                        parquet_path
                    )

                    table_df = (
                        self._create_nr_controls_data(
                            df=df,
                            year=int(nr_year),
                            group_level=(
                                nr_group_level
                                or "naring"
                            ),
                            view=nr_view or "Land",
                            negative_threshold=float(
                                nr_threshold
                                if nr_threshold is not None
                                else 1000
                            ),
                            hide_nonnegative_columns=(
                                "hide"
                                in (
                                    nr_hide_columns
                                    or []
                                )
                            ),
                            max_rows=int(
                                nr_max_rows or 300
                            ),
                        )
                    )

                    nr_note = None

                    if (nr_view or "Land") == "Fylke":
                        nr_note = html.Div(
                            children=[
                                html.Strong("Merk: "),
                                (
                                    "Negative verdier for bearbeidingsverdi på "
                                    "fylkesnivå er normalt. Foretakets "
                                    "bearbeidingsverdi kan fordeles mellom bedrifter "
                                    "i ulike fylker, og enkelte fylkesbidrag kan "
                                    "derfor være negative uten at dette innebærer "
                                    "en feil."
                                ),
                            ],
                            style={
                                "padding": "12px 16px",
                                "border": "1px solid #b8d4e8",
                                "borderRadius": "8px",
                                "backgroundColor": "#f0f7fc",
                                "fontSize": "14px",
                            },
                        )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen negative "
                            "NR-kontroller."
                        ),
                        summary_card=nr_note,
                    )

                # -----------------------------------------
                # Opposite direction
                # -----------------------------------------
                if visualisation == "opposite-direction":
                    if opposite_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )

                    df = self._read_business_data(
                        parquet_path
                    )

                    table_df = (
                        self._create_opposite_direction_data(
                            df=df,
                            year=int(opposite_year),
                            group_level=(
                                opposite_group_level
                                or "naring_4"
                            ),
                            view=(
                                opposite_view
                                or "Land"
                            ),
                            rule=(
                                opposite_rule
                                or "both"
                            ),
                            min_count=int(
                                opposite_min_count
                                if (
                                    opposite_min_count
                                    is not None
                                )
                                else 50
                            ),
                            gap_threshold_pct=float(
                                opposite_gap_threshold
                                if (
                                    opposite_gap_threshold
                                    is not None
                                )
                                else 10
                            ),
                            absolute_change_threshold=(
                                float(
                                    opposite_absolute_threshold
                                    if (
                                        opposite_absolute_threshold
                                        is not None
                                    )
                                    else 0
                                )
                            ),
                            max_rows=int(
                                opposite_max_rows
                                or 300
                            ),
                        )
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen grupper med "
                            "motsatte bevegelser."
                        ),
                    )
                # -----------------------------------------
                # Breakdown
                # -----------------------------------------
                if visualisation == "breakdown":
                    if breakdown_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg et år."
                            )
                        )

                    if not breakdown_variable:
                        return figure_result(
                            self._empty_figure(
                                "Velg en sammensatt variabel."
                            )
                        )

                    analysis_level = (
                        breakdown_analysis_level
                        or "industry"
                    )

                    # -------------------------------------
                    # Industry-level breakdown
                    # -------------------------------------
                    if analysis_level == "industry":
                        if not breakdown_group_level:
                            return figure_result(
                                self._empty_figure(
                                    "Velg et næringsnivå."
                                )
                            )

                        if not breakdown_group_value:
                            return figure_result(
                                self._empty_figure(
                                    "Velg en næringskode."
                                )
                            )

                        business_path = self._parquet_path(
                            data_version,
                            dataset="bedrifter",
                        )

                        business_df = self._read_business_data(
                            business_path
                        )

                        table_df = self._create_breakdown_data(
                            df=business_df,
                            year=int(breakdown_year),
                            group_level=breakdown_group_level,
                            group_value=breakdown_group_value,
                            variable=breakdown_variable,
                        )

                        return table_result(
                            table_df,
                            (
                                "Fant ingen data for "
                                "den valgte nedbrytningen."
                            ),
                        )

                    # -------------------------------------
                    # Enterprise/business breakdown
                    # -------------------------------------
                    if not breakdown_enterprise:
                        return figure_result(
                            self._empty_figure(
                                "Velg eller skriv inn et foretak."
                            )
                        )

                    enterprise_number = (
                        str(breakdown_enterprise)
                        .strip()
                        .removesuffix(".0")
                    )

                    unit_level = (
                        breakdown_unit_level
                        or "both"
                    )

                    result_frames: list[pd.DataFrame] = []

                    if unit_level in {
                        "both",
                        "enterprise",
                    }:
                        enterprise_path = self._parquet_path(
                            data_version,
                            dataset="foretak",
                        )

                        enterprise_df = (
                            self._read_enterprise_data(
                                enterprise_path
                            )
                        )

                        enterprise_result = (
                            self._create_breakdown_data(
                                df=enterprise_df,
                                year=int(breakdown_year),
                                group_level=None,
                                group_value=None,
                                variable=breakdown_variable,
                                orgnr_foretak=enterprise_number,
                            )
                        )

                        if not enterprise_result.empty:
                            enterprise_result.insert(
                                0,
                                "nivå",
                                "Foretak",
                            )

                            result_frames.append(
                                enterprise_result
                            )

                    if unit_level in {
                        "both",
                        "business",
                    }:
                        if not breakdown_business:
                            if unit_level == "business":
                                return figure_result(
                                    self._empty_figure(
                                        "Velg en bedrift."
                                    )
                                )

                        else:
                            business_number = (
                                str(breakdown_business)
                                .strip()
                                .removesuffix(".0")
                            )

                            business_path = self._parquet_path(
                                data_version,
                                dataset="bedrifter",
                            )

                            business_df = (
                                self._read_business_data(
                                    business_path
                                )
                            )

                            business_result = (
                                self._create_breakdown_data(
                                    df=business_df,
                                    year=int(breakdown_year),
                                    group_level=None,
                                    group_value=None,
                                    variable=breakdown_variable,
                                    orgnr_foretak=enterprise_number,
                                    orgnr_bedrift=business_number,
                                )
                            )

                            if not business_result.empty:
                                business_result.insert(
                                    0,
                                    "nivå",
                                    "Bedrift",
                                )

                                result_frames.append(
                                    business_result
                                )

                    if not result_frames:
                        return table_result(
                            pd.DataFrame(),
                            (
                                "Fant ingen data for det valgte "
                                "foretaket eller bedriften."
                            ),
                        )

                    table_df = pd.concat(
                        result_frames,
                        ignore_index=True,
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen data for det valgte "
                            "foretaket eller bedriften."
                        ),
                    )

                # -----------------------------------------
                # MOMS
                # -----------------------------------------
                if visualisation == "moms":
                    if moms_previous_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg tidligere år."
                            )
                        )

                    if moms_current_year is None:
                        return figure_result(
                            self._empty_figure(
                                "Velg nåværende år."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="moms",
                    )

                    df = self._read_generic_data(
                        parquet_path
                    )

                    table_df = self._create_moms_data(
                        df=df,
                        group_level=(
                            moms_group_level or "n2"
                        ),
                        previous_year=int(
                            moms_previous_year
                        ),
                        current_year=int(
                            moms_current_year
                        ),
                        selected_naringer=(
                            moms_naring_filter or None
                        ),
                    )

                    yellow_columns = [
                        f"omsetning_{int(moms_previous_year)}",
                        f"omsetning_{int(moms_current_year)}",
                        "omsetning_percentage_change",
                        f"moms_{int(moms_previous_year)}",
                        f"moms_{int(moms_current_year)}",
                        "moms_percentage_change",
                    ]

                    blue_columns = [
                        "tilganger",
                        "avganger",
                        "tilganger_omsetning",
                        "avganger_omsetning",
                        "tilganger_sysselsetting_syss",
                        "avganger_sysselsetting_syss",
                    ]

                    moms_styles = [
                        {
                            "if": {
                                "column_id": column,
                            },
                            "backgroundColor": "#fff6d6",
                        }
                        for column in yellow_columns
                        if column in table_df.columns
                    ]

                    moms_styles.extend(
                        [
                            {
                                "if": {
                                    "column_id": column,
                                },
                                "backgroundColor": "#e8f1ff",
                            }
                            for column in blue_columns
                            if column in table_df.columns
                        ]
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen MOMS-data for "
                            "de valgte årene."
                        ),
                        extra_styles=moms_styles,
                    )

                # -----------------------------------------
                # Movement
                # -----------------------------------------
                if visualisation == "movement":
                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="movement_base",
                    )

                    df = self._read_generic_data(
                        parquet_path
                    )

                    table_df = (
                        self._create_movement_data(
                            df=df,
                            direction=(
                                movement_direction
                                or "tilgang"
                            ),
                            variable=(
                                movement_variable
                                or "omsetning"
                            ),
                            group_level=(
                                movement_group_level
                                or "n2"
                            ),
                            code_filter=(
                                movement_code_filter
                                or ""
                            ),
                            exact_match=(
                                "exact"
                                in (
                                    movement_exact_match
                                    or []
                                )
                            ),
                            top_n=int(
                                movement_top_n
                                or 100
                            ),
                        )
                    )

                    return table_result(
                        table_df,
                        (
                            "Fant ingen tilganger eller "
                            "avganger for filteret."
                        ),
                    )

                # -----------------------------------------
                # Method analysis
                # -----------------------------------------
                if visualisation == "method-analysis":
                    if not method_naring_level:
                        return figure_result(
                            self._empty_figure(
                                "Velg et næringsnivå."
                            )
                        )

                    if not method_naring_value:
                        return figure_result(
                            self._empty_figure(
                                "Velg en næringskode."
                            )
                        )

                    if not method_ratios:
                        return figure_result(
                            self._empty_figure(
                                "Velg minst én rate."
                            )
                        )

                    parquet_path = self._parquet_path(
                        data_version,
                        dataset="bedrifter",
                    )

                    df = self._read_business_data(
                        parquet_path
                    )

                    figure = (
                        self._create_method_analysis_figure(
                            df=df,
                            naring_level=(
                                method_naring_level
                            ),
                            naring_value=(
                                method_naring_value
                            ),
                            ratios=method_ratios,
                            reg_types=(
                                method_reg_types
                                or None
                            ),
                        )
                    )

                    return figure_result(figure)

                label = VL_VISUALISATIONS.get(
                    visualisation,
                    visualisation,
                )

                return figure_result(
                    self._empty_figure(
                        (
                            "Visualiseringen "
                            f"{label} er ikke konfigurert."
                        )
                    )
                )

            except Exception as error:
                return figure_result(
                    self._empty_figure(
                        (
                            "Kunne ikke lage "
                            f"visualiseringen: {error}"
                        )
                    )
                )

# ============================================================================
# Framework adapters
# ============================================================================

class VLModuleTab(TabImplementation, VLModule):
    """Expose ``VLModule`` through the framework's tab implementation."""

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
    """Expose ``VLModule`` through the framework's sidebar window implementation."""

    def __init__(
        self,
        file_path_resolver: Callable[[str, str], str],
    ) -> None:
        VLModule.__init__(
            self,
            file_path_resolver=file_path_resolver,
        )
        WindowImplementation.__init__(self)