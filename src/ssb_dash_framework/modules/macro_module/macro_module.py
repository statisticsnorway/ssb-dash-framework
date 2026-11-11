"""A generic macro module for drilling down from aggregated values to observations.

The module shows a macro table with value variables summed per group for the selected
period and a comparison period. Clicking a value cell lists the observations behind it,
and confirming an observation sends its ident to the variable selector.

All data access goes through a MacroModuleDataHandler. See README.md in this folder.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash import no_update
from dash.exceptions import PreventUpdate
from dash_ag_grid import AgGrid
from dash_iconify import DashIconify

from ...config.models import get_from_module_registry
from ...setup.variableselector import TimeUnit
from ...setup.variableselector import VariableSelector
from ...utils import ModuleBase
from ...utils.alert_handler import AlertHandler
from .data_handler import MacroModuleDataHandler

logger = logging.getLogger(__name__)

UNKNOWN = "Ukjent"
PREV = "__prev"
DIFF = "__diff"
SHOWN = "__shown"
TOOLTIP = "__tooltip"
CHANGED = "__changed"
COUNT = "__count"
STATUS = "status"
DISPLAY_MODES = {
    "pct": "Prosentendring",
    "current": "Periodens sum",
    "diff": "Differanse",
}
GRID_OPTIONS = {
    "enableCellTextSelection": True,
    "enableBrowserTooltips": True,
    "suppressFieldDotNotation": True,
}


def comparison_period(time_unit: TimeUnit, period: str, lag: int) -> str:
    """Return the period `lag` periods before `period`."""
    return str(TimeUnit.parse(time_unit, period).subtract(lag).to_str())


def prepare(
    data: pd.DataFrame,
    grouping_variables: list[str],
    value_variables: list[str],
    codelists: dict[str, dict[str, str]],
) -> tuple[pd.DataFrame, int]:
    """Replace missing codes and codes outside the codelist with "Ukjent".

    Args:
        data: Observations for one period.
        grouping_variables: The grouping variables to check.
        value_variables: The value variables, cast to float.
        codelists: {grouping variable: {code: label}}.

    Returns:
        The prepared copy, and how many observations got at least one "Ukjent" code.
    """
    data = data.copy()
    unknown = pd.Series(False, index=data.index)
    for variable in grouping_variables:
        invalid = data[variable].isna()
        if variable in codelists:
            invalid |= ~data[variable].isin(list(codelists[variable]))
        data[variable] = data[variable].astype(object).where(~invalid, UNKNOWN)
        unknown |= invalid
    data[value_variables] = data[value_variables].astype("float64")
    return data, int(unknown.sum())


def apply_filters(data: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    """Keep observations whose grouping codes match every filter."""
    for variable, code in filters.items():
        data = data[data[variable] == code]
    return data


def category_order(
    variable: str, codelists: dict[str, dict[str, str]], *frames: pd.DataFrame
) -> list[str]:
    """Return the display order of codes: codelist order, or sorted codes, then "Ukjent"."""
    present = set().union(*(set(frame[variable]) for frame in frames))
    codes = list(codelists.get(variable, sorted(present - {UNKNOWN})))
    return [*codes, UNKNOWN] if UNKNOWN in present else codes


def macro_table(
    current: pd.DataFrame,
    comparison: pd.DataFrame,
    group_by: list[str],
    value_variables: list[str],
    codelists: dict[str, dict[str, str]],
    show_empty: bool = False,
) -> pd.DataFrame:
    """Sum value variables per group for both periods.

    Args:
        current: Prepared observations for the selected period.
        comparison: Prepared observations for the comparison period.
        group_by: The grouping variables that make up the rows.
        value_variables: The value variables to sum.
        codelists: {grouping variable: {code: label}}, deciding the row order.
        show_empty: Include every combination of codes, also without observations.

    Returns:
        One row per group with the group codes, the observation count in the selected
        period (COUNT), and each value variable's sum in the selected period (`name`)
        and the comparison period (`name` + PREV), in category order.
    """
    columns = [*group_by, COUNT, *value_variables, *(v + PREV for v in value_variables)]
    if not group_by:
        return pd.DataFrame(columns=columns)
    order = {v: category_order(v, codelists, current, comparison) for v in group_by}

    def summarise(data: pd.DataFrame) -> pd.DataFrame:
        data = data.astype({v: pd.CategoricalDtype(order[v]) for v in group_by})
        grouped = data.groupby(group_by, observed=not show_empty)
        return grouped[value_variables].sum().assign(**{COUNT: grouped.size()})

    before = summarise(comparison)[value_variables].add_suffix(PREV)
    table = summarise(current).join(before, how="outer").fillna(0).reset_index()
    for variable in group_by:
        table[variable] = table[variable].astype(str)
    rank = {v: {code: i for i, code in enumerate(order[v])} for v in group_by}
    table = table.sort_values(group_by, key=lambda codes: codes.map(rank[codes.name]))
    return table.astype({COUNT: int})[columns].reset_index(drop=True)


def totals(
    current: pd.DataFrame, comparison: pd.DataFrame, value_variables: list[str]
) -> pd.DataFrame:
    """Sum value variables over all observations, in the same layout as `macro_table`."""
    row: dict[str, float] = {COUNT: len(current)}
    for variable in value_variables:
        row[variable] = current[variable].sum()
        row[variable + PREV] = comparison[variable].sum()
    return pd.DataFrame([row])


def add_display_columns(
    table: pd.DataFrame,
    value_variables: list[str],
    mode: str,
    period: str,
    previous: str,
) -> pd.DataFrame:
    """Add the shown value (SHOWN) and a tooltip (TOOLTIP) for each value variable."""
    table = table.copy()
    for variable in value_variables:
        now, before = table[variable], table[variable + PREV]
        change = now - before
        if mode == "pct":
            shown = (change / before.abs()).replace([np.inf, -np.inf], np.nan)
        elif mode == "diff":
            shown = change
        else:
            shown = now
        table[variable + SHOWN] = shown
        table[variable + TOOLTIP] = [
            f"{period}: {a:,.0f}\n{previous}: {b:,.0f}\nEndring: {a - b:+,.0f}"
            for a, b in zip(now, before, strict=True)
        ]
    return table


def add_group_labels(
    table: pd.DataFrame, group_by: list[str], codelists: dict[str, dict[str, str]]
) -> pd.DataFrame:
    """Add a shown text (SHOWN) per grouping column: the code and its codelist label."""
    table = table.copy()
    for variable in group_by:
        labels = codelists.get(variable, {})
        table[variable + SHOWN] = [
            f"{code} {labels[code]}" if labels.get(code, code) != code else code
            for code in table[variable]
        ]
    return table


def observation_list(
    current: pd.DataFrame,
    comparison: pd.DataFrame,
    key: list[str],
    group: dict[str, str],
    value_variables: list[str],
    clicked: str,
    reverse: bool = False,
) -> pd.DataFrame:
    """List the observations that contribute to a group in either period.

    Columns from the comparison period get the PREV suffix. Each value variable gets a
    DIFF column with the observation's contribution to the change of the group's sum.
    STATUS is "Ny" (new in the data), "Borte" (gone from the data), "Inn" (moved into
    the group), "Ut" (moved out of the group) or "" (unchanged).

    Args:
        current: Prepared observations for the selected period.
        comparison: Prepared observations for the comparison period.
        key: The columns identifying an observation.
        group: {grouping variable: code} of the clicked row.
        value_variables: The value variables.
        clicked: The value variable of the clicked cell.
        reverse: Reverse the sort order.

    Returns:
        The observations, sorted by contribution to `clicked`: largest first if the
        group's sum increased, smallest first if it decreased, or the opposite if
        `reverse` is True.
    """
    merged = current.merge(
        comparison, on=key, how="outer", suffixes=("", PREV), indicator=True
    )
    in_now = merged["_merge"] != "right_only"
    in_before = merged["_merge"] != "left_only"
    for variable, code in group.items():
        in_now &= merged[variable] == code
        in_before &= merged[variable + PREV] == code
    merged[STATUS] = np.select(
        [
            merged["_merge"] == "left_only",
            merged["_merge"] == "right_only",
            in_now & ~in_before,
            ~in_now & in_before,
        ],
        ["Ny", "Borte", "Inn", "Ut"],
        default="",
    )
    for variable in value_variables:
        merged[variable + DIFF] = merged[variable].where(in_now, 0).fillna(0) - merged[
            variable + PREV
        ].where(in_before, 0).fillna(0)
    merged = merged[in_now | in_before].drop(columns="_merge")
    increased = merged[clicked + DIFF].sum() >= 0
    return merged.sort_values(
        clicked + DIFF, ascending=increased == reverse, kind="stable"
    )


def records(data: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to grid rows, with missing values as None."""
    return data.astype(object).where(data.notna(), None).to_dict("records")  # type: ignore[no-any-return]


class MacroModule(ModuleBase):
    """Drill down from aggregated values to the observations behind them.

    The macro table sums value variables per group for the selected period and a
    comparison period. Clicking a value cell lists the observations in that group, and
    confirming an observation sends its ident (and any secondary idents present in the
    data) to the variable selector.

    Grouping variables that also exist as variable selector grouping variables act as
    filters: a value in the selector limits the module to that code.

    Requires the variable selector to have a time unit and an ident.
    """

    def __init__(
        self,
        data_handler: MacroModuleDataHandler,
        grouping_variables: list[str] | None = None,
        comparison_lag: int = 1,
        label: str = "Makromodul",
    ) -> None:
        """Initialize the MacroModule.

        Args:
            data_handler: Supplies observations in the MacroModule's data model.
            grouping_variables: The grouping variables to offer, in display order.
                Defaults to every grouping variable declared by the data handler.
            comparison_lag: How many periods back the comparison period starts out as.
            label: The label of the tab or window.
        """
        self.label = label
        self.icon = DashIconify(icon="feather:globe", width=24)
        self.data_handler = data_handler
        self.grouping_variables = list(
            grouping_variables or getattr(data_handler, "grouping_variables", [])
        )
        self.comparison_lag = comparison_lag
        self._is_valid()
        self.value_variables: dict[str, str] = dict(data_handler.value_variables)
        self.filter_variables = [
            v
            for v in self.grouping_variables
            if v in (VariableSelector._grouping_variables or [])
        ]
        super().__init__()

    def _is_valid(self) -> None:
        """Check the configuration, so mistakes fail when the app starts.

        Raises:
            TypeError: If the data handler is not a MacroModuleDataHandler.
            ValueError: If the data model, the grouping variables, the comparison lag
                or the variable selector is not set up as required.
        """
        super()._is_valid()
        handler = self.data_handler
        name = type(handler).__name__
        if not isinstance(handler, MacroModuleDataHandler):
            raise TypeError(
                f"data_handler must be a MacroModuleDataHandler, got {name}."
            )
        values = getattr(handler, "value_variables", None)
        declared = getattr(handler, "grouping_variables", None)
        if not isinstance(values, dict) or not values:
            raise ValueError(f"{name} must declare at least one value variable.")
        if not isinstance(declared, list) or not self.grouping_variables:
            raise ValueError(f"{name} must declare at least one grouping variable.")
        fixed = {handler.ident_column, handler.instance_column, handler.name_column}
        clashes = (fixed | {STATUS}) & {*values, *declared}
        if clashes or set(values) & set(declared):
            raise ValueError(
                f"{name}: variable names must be unique and not one of {sorted(fixed | {STATUS})}."
            )
        unknown = [v for v in self.grouping_variables if v not in declared]
        if unknown:
            raise ValueError(
                f"{name} does not declare the grouping variable(s) {unknown}. Declared: {declared}."
            )
        if not isinstance(self.comparison_lag, int) or self.comparison_lag < 1:
            raise ValueError("comparison_lag must be a whole number of at least 1.")
        if VariableSelector._time_unit is None or VariableSelector._ident is None:
            raise ValueError(
                "MacroModule requires 'time_units' and 'ident' in the VariableSelectorConfig."
            )

    @classmethod
    def from_yaml(cls, *args: Any, **kwargs: Any) -> "MacroModule":
        """Create the module from yaml, building the data handler from its own block.

        `data_handler` is either the class name of a data handler without arguments, or
        a block with `type` set to the class name and the handler's arguments.

        Args:
            *args: Positional arguments.
            **kwargs: The module's arguments.

        Returns:
            The configured MacroModule.

        Raises:
            TypeError: If `data_handler` is not a registered MacroModuleDataHandler.
        """
        kwargs.pop("as_type", None)
        kwargs.pop("window_scrollable", None)
        spec = kwargs.pop("data_handler")
        handler_args = dict(spec) if isinstance(spec, dict) else {"type": spec}
        handler_type = get_from_module_registry(handler_args.pop("type")).type
        if not issubclass(handler_type, MacroModuleDataHandler):
            raise TypeError(f"{handler_type.__name__} is not a MacroModuleDataHandler.")
        handler = handler_type.from_yaml(**handler_args)
        return cls(handler, *args, **kwargs)

    def _id(self, name: str) -> str:
        return f"{self.module_id}-{name}"

    def layout(self) -> html.Div:
        """Create the layout of the module."""

        def label(text: str) -> html.Label:
            return html.Label(text, className="macromodule-label")

        sidebar = html.Div(
            className="macromodule-sidebar",
            children=[
                html.Div(id=self._id("last-updated"), style={"fontSize": 13}),
                label("Grupper etter"),
                dcc.Dropdown(
                    id=self._id("group-by"),
                    options=self.grouping_variables,
                    value=self.grouping_variables[:1],
                    multi=True,
                ),
                label("Verdivariabler"),
                dcc.Dropdown(
                    id=self._id("value-variables"),
                    options=[
                        {"label": text, "value": name}
                        for name, text in self.value_variables.items()
                    ],
                    value=list(self.value_variables),
                    multi=True,
                ),
                label("Visning"),
                dcc.RadioItems(
                    id=self._id("display-mode"),
                    className="ssb-radio-buttons",
                    options=[
                        {"label": t, "value": m} for m, t in DISPLAY_MODES.items()
                    ],
                    value="pct",
                ),
                label("Sammenlign med N perioder tilbake"),
                dcc.Input(
                    id=self._id("lag"),
                    type="number",
                    min=1,
                    step=1,
                    value=self.comparison_lag,
                    debounce=True,
                ),
                dcc.Checklist(
                    id=self._id("show-empty"),
                    options=[{"label": " Vis tomme rader", "value": "show"}],
                    value=[],
                    style={"paddingTop": 20},
                ),
            ],
        )
        macro_grid = AgGrid(
            id=self._id("macro-grid"),
            getRowId="params.data.id",
            defaultColDef={"sortable": True, "filter": True, "resizable": True},
            dashGridOptions=GRID_OPTIONS,
            style={"height": "100%", "width": "100%"},
        )
        observation_grid = AgGrid(
            id=self._id("observation-grid"),
            getRowId="params.data.id",
            defaultColDef={"sortable": True, "filter": True, "resizable": True},
            dashGridOptions={
                **GRID_OPTIONS,
                "pagination": True,
                "paginationPageSize": 20,
            },
            style={"height": "650px", "width": "100%"},
        )
        popup = html.Div(
            id=self._id("popup"),
            className="macromodule-click-popup",
            style={"display": "none"},
            children=[
                html.Span(
                    id=self._id("popup-label"),
                    className="macromodule-click-popup-label",
                ),
                html.Button(
                    "Velg",
                    id=self._id("select-button"),
                    className="ssb-btn primary-btn",
                ),
            ],
        )
        return html.Div(
            className="macromodule",
            children=[
                html.Div(
                    className="macromodule-container",
                    children=[
                        sidebar,
                        html.Div(
                            className="macromodule-heatmap-grid-container",
                            style={"height": "600px"},
                            children=macro_grid,
                        ),
                    ],
                ),
                html.Div(
                    className="macromodule-detail-grid-container",
                    children=[
                        html.H5(id=self._id("observation-title")),
                        html.Div(
                            [
                                popup,
                                html.Button(
                                    "Snu sortering",
                                    id=self._id("reverse"),
                                    className="ssb-btn secondary-btn",
                                ),
                            ],
                            style={"display": "flex", "gap": 10, "marginBottom": 10},
                        ),
                        dcc.Loading(observation_grid),
                    ],
                ),
                dcc.Store(id=self._id("context")),
                dcc.Store(id=self._id("selected-cell")),
                dcc.Store(id=self._id("pending")),
            ],
        )

    def _load(
        self, period: str, previous: str, filters: dict[str, str]
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, str]], int]:
        """Fetch, prepare and filter the observations for both periods.

        Args:
            period: The selected period.
            previous: The comparison period.
            filters: {grouping variable: code} from the variable selector.

        Returns:
            The selected period's observations, the comparison period's observations,
            the codelists and the number of observations with an "Ukjent" code.
        """
        codelists = self.data_handler.get_codelists(period)
        frames, unknown = [], 0
        for p in (period, previous):
            data, count = prepare(
                self.data_handler.get_observations(p),
                self.grouping_variables,
                list(self.value_variables),
                codelists,
            )
            frames.append(apply_filters(data, filters))
            unknown += count
        return frames[0], frames[1], codelists, unknown

    def _report_error(self, error: Exception, period: str) -> None:
        logger.exception(f"{self.module_id} failed for period {period}")
        AlertHandler.error(
            f"{self.label}: {type(self.data_handler).__name__} failed for period {period}: {error}"
        )

    def _macro_columns(
        self, group_by: list[str], value_variables: list[str], mode: str
    ) -> list[dict[str, Any]]:
        columns: list[dict[str, Any]] = [
            {"field": v + SHOWN, "colId": v, "headerName": v, "pinned": "left"}
            for v in group_by
        ]
        columns.append({"field": COUNT, "headerName": "Antall", "type": "rightAligned"})
        for variable in value_variables:
            columns.append(
                {
                    "field": variable + SHOWN,
                    "colId": variable,
                    "headerName": self.value_variables[variable],
                    "type": "rightAligned",
                    "filter": "agNumberColumnFilter",
                    "tooltipField": variable + TOOLTIP,
                    "valueFormatter": {
                        "function": f"MacroTable.formatValue(params, '{mode}')"
                    },
                    "cellStyle": {
                        "function": f"MacroTable.heatmapStyle(params, '{mode}')"
                    },
                }
            )
        return columns

    def _observation_columns(
        self, data: pd.DataFrame, clicked: str, period: str, previous: str
    ) -> list[dict[str, Any]]:
        handler = self.data_handler
        headers = {
            handler.ident_column: "Ident",
            handler.instance_column: "Instans",
            handler.name_column: "Navn",
        }
        columns: list[dict[str, Any]] = [
            {"field": field, "headerName": header, "pinned": "left"}
            for field, header in headers.items()
            if field in data.columns
        ]
        columns.append(
            {
                "field": STATUS,
                "headerName": "Status",
                "cellStyle": {"function": "MacroTable.statusStyle(params)"},
            }
        )
        columns += [
            {
                "field": variable,
                "headerName": variable,
                "tooltipField": variable + TOOLTIP,
                "cellStyle": {"function": "MacroTable.changedStyle(params)"},
            }
            for variable in self.grouping_variables
        ]
        ordered = [clicked, *(v for v in self.value_variables if v != clicked)]
        number = {
            "type": "rightAligned",
            "filter": "agNumberColumnFilter",
            "valueFormatter": {"function": "MacroTable.formatValue(params, 'current')"},
        }
        for variable in ordered:
            text = self.value_variables[variable]
            columns += [
                {**number, "field": variable, "headerName": f"{text} {period}"},
                {
                    **number,
                    "field": variable + PREV,
                    "headerName": f"{text} {previous}",
                    "cellStyle": {"backgroundColor": "#e8e9eb", "color": "black"},
                },
                {
                    **number,
                    "field": variable + DIFF,
                    "headerName": f"{text} bidrag",
                    "cellStyle": {"function": "MacroTable.statusStyle(params)"},
                },
            ]
        return columns

    def _observation_rows(self, data: pd.DataFrame) -> list[dict[str, Any]]:
        data = data.copy()
        name = self.data_handler.name_column
        for variable in [*self.grouping_variables, name]:
            if variable not in data.columns:
                continue
            before = data[variable + PREV]
            changed = (
                data[variable].notna() & before.notna() & (data[variable] != before)
            )
            data[variable + CHANGED] = changed
            data[variable + TOOLTIP] = (
                "Sammenligningsperiode: " + before.astype(str)
            ).where(changed)
            data[variable] = data[variable].fillna(before)
        data["id"] = [str(i) for i in range(len(data))]
        return records(data)

    def module_callbacks(self) -> None:
        """Define the callbacks of the module."""
        filter_inputs = [
            VariableSelector.get_input(v)[0] for v in self.filter_variables
        ]
        empty: tuple[Any, ...] = ([], [], GRID_OPTIONS, "", None)

        @callback(
            Output(self._id("macro-grid"), "rowData"),
            Output(self._id("macro-grid"), "columnDefs"),
            Output(self._id("macro-grid"), "dashGridOptions"),
            Output(self._id("last-updated"), "children"),
            Output(self._id("context"), "data"),
            VariableSelector.get_timevar(Input),
            Input(self._id("group-by"), "value"),
            Input(self._id("value-variables"), "value"),
            Input(self._id("display-mode"), "value"),
            Input(self._id("lag"), "value"),
            Input(self._id("show-empty"), "value"),
            *filter_inputs,
        )
        def update_macro_table(
            period: str | None,
            group_by: list[str] | None,
            value_variables: list[str] | None,
            mode: str,
            lag: int | None,
            show_empty: list[str] | None,
            *filter_values: str | None,
        ) -> tuple[Any, ...]:
            """Build the macro table for the selected period."""
            if not period or not value_variables:
                return empty
            group_by = [v for v in self.grouping_variables if v in (group_by or [])]
            value_variables = [v for v in self.value_variables if v in value_variables]
            filters = {
                v: code
                for v, code in zip(self.filter_variables, filter_values, strict=True)
                if code
            }
            try:
                previous = comparison_period(
                    VariableSelector._time_unit, period, int(lag or 1)  # type: ignore[arg-type]
                )
                current, comparison, codelists, unknown = self._load(
                    period, previous, filters
                )
                updated = self.data_handler.last_updated(period)
            except Exception as error:
                self._report_error(error, period)
                return empty
            if unknown:
                AlertHandler.warning(
                    f"{self.label}: {unknown} observation(s) have a missing code or a code "
                    f"outside the codelist, shown as '{UNKNOWN}'."
                )
            table = macro_table(
                current,
                comparison,
                group_by,
                value_variables,
                codelists,
                bool(show_empty),
            )
            table = add_display_columns(table, value_variables, mode, period, previous)
            table = add_group_labels(table, group_by, codelists)
            table["id"] = [str(i) for i in range(len(table))]
            total = add_display_columns(
                totals(current, comparison, value_variables),
                value_variables,
                mode,
                period,
                previous,
            )
            total["id"] = "total"
            if group_by:
                total[group_by[0] + SHOWN] = "Totalt"
            context = {
                "period": period,
                "previous": previous,
                "filters": filters,
                "group_by": group_by,
            }
            last_updated = f"Sist oppdatert: {updated}" if updated else ""
            return (
                records(table),
                self._macro_columns(group_by, value_variables, mode),
                {**GRID_OPTIONS, "pinnedTopRowData": records(total)},
                last_updated,
                context,
            )

        @callback(
            Output(self._id("selected-cell"), "data"),
            Input(self._id("macro-grid"), "cellClicked"),
            Input(self._id("macro-grid"), "rowData"),
            State(self._id("context"), "data"),
        )
        def select_cell(
            cell: dict[str, Any] | None,
            rows: list[dict[str, Any]] | None,
            context: dict[str, Any] | None,
        ) -> dict[str, Any] | None:
            """Remember the clicked value cell, or forget it when the table changes."""
            clicked = f"{self._id('macro-grid')}.cellClicked" in ctx.triggered_prop_ids
            if not clicked or not cell or not context:
                return None
            row = next(
                (r for r in rows or [] if r.get("id") == cell.get("rowId")), None
            )
            if row is None or cell.get("colId") not in self.value_variables:
                return None
            group = {v: row[v] for v in context["group_by"]}
            return {**context, "group": group, "variable": cell["colId"]}

        @callback(
            Output(self._id("observation-grid"), "rowData"),
            Output(self._id("observation-grid"), "columnDefs"),
            Output(self._id("observation-title"), "children"),
            Input(self._id("selected-cell"), "data"),
            Input(self._id("reverse"), "n_clicks"),
        )
        def update_observation_list(
            selected: dict[str, Any] | None, reverse_clicks: int | None
        ) -> tuple[Any, ...]:
            """List the observations behind the selected cell."""
            if not selected:
                return [], [], ""
            period, previous = selected["period"], selected["previous"]
            try:
                current, comparison, _, _ = self._load(
                    period, previous, selected["filters"]
                )
            except Exception as error:
                self._report_error(error, period)
                return [], [], ""
            key = self.data_handler.key_columns(current)
            data = observation_list(
                current,
                comparison,
                key,
                selected["group"],
                list(self.value_variables),
                selected["variable"],
                reverse=bool((reverse_clicks or 0) % 2),
            )
            group = ", ".join(f"{v} {c}" for v, c in selected["group"].items())
            title = f"{self.value_variables[selected['variable']]}: {group or 'alle'} ({period} mot {previous})"
            return (
                self._observation_rows(data),
                self._observation_columns(data, selected["variable"], period, previous),
                title,
            )

        @callback(
            Output(self._id("pending"), "data"),
            Output(self._id("popup-label"), "children"),
            Output(self._id("popup"), "style"),
            Input(self._id("observation-grid"), "cellClicked"),
            Input(self._id("observation-grid"), "rowData"),
            prevent_initial_call=True,
        )
        def show_popup(
            cell: dict[str, Any] | None, rows: list[dict[str, Any]] | None
        ) -> tuple[Any, ...]:
            """Ask for confirmation before sending an observation to the variable selector."""
            hidden = (None, "", {"display": "none"})
            clicked = (
                f"{self._id('observation-grid')}.cellClicked" in ctx.triggered_prop_ids
            )
            if not clicked or not cell:
                return hidden
            row = next(
                (r for r in rows or [] if r.get("id") == cell.get("rowId")), None
            )
            if row is None:
                return hidden
            handler = self.data_handler
            text = " ".join(
                str(row[c])
                for c in (handler.ident_column, handler.name_column)
                if row.get(c)
            )
            return row, f"Send {text} til variabelvelgeren?", {"display": "flex"}

        secondary = [
            v
            for v in (VariableSelector._secondary_ident or [])
            if v != self.data_handler.ident_column
        ]

        @callback(
            VariableSelector.get_ident(Output),
            *(VariableSelector.get_output_object(v) for v in secondary),
            Output(self._id("pending"), "data", allow_duplicate=True),
            Output(self._id("popup"), "style", allow_duplicate=True),
            Input(self._id("select-button"), "n_clicks"),
            State(self._id("pending"), "data"),
            prevent_initial_call=True,
        )
        def send_to_variable_selector(
            n_clicks: int | None, row: dict[str, Any] | None
        ) -> tuple[Any, ...]:
            """Write the confirmed observation's idents to the variable selector."""
            if not n_clicks or not row:
                raise PreventUpdate
            ident = row[self.data_handler.ident_column]
            AlertHandler.info(f"{self.label}: valgte {ident}", ephemeral=True)
            others = [
                str(row[v]) if row.get(v) is not None else no_update for v in secondary
            ]
            return (str(ident), *others, None, {"display": "none"})
