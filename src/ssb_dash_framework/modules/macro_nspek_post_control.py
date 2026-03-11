import logging
from collections.abc import Hashable
from typing import Any
from typing import ClassVar
from typing import Literal

import ibis
import pandas as pd
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from dash_ag_grid import AgGrid
from ibis.backends import BaseBackend
from ibis.expr.types.relations import Table
from pandas.core.frame import DataFrame

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator
from ..modules.macro_module_consolidated import MacroModuleConsolidated_ParquetReader

ibis.options.interactive = True
logger = logging.getLogger(__name__)

# variables used in the heatmap-grid
positive_fem_siffer = {
    # må vere positive på femsiffer nivå, frå leverandøravtalen med nasjonalregnskapet
    "nopost_p3000": "NO3000",
    "nopost_p3100": "NO3100",
    "nopost_p3200": "NO3200",
    "nopost_p3700": "NO3700",
    "nopost_p3900": "NO3900",
    "nopost_p4005": "NO4005",
    "nopost_p4500": "NO4500",
    "nopost_p5000": "NO5000",
    "nopost_p6300": "NO6300",
    "nopost_p6400": "NO6400",
    "nopost_p6500": "NO6500",
    "nopost_p6700": "NO6700",
    "nopost_p6995": "NO6995",
    "nopost_p7700": "NO7700",
}

positive_to_siffer = {
    # må vere positive på tosiffernivå, frå leverandøravtalen med nasjonalregnskapet
    "nopost_p3600": "NO3600",
    "nopost_p3605": "NO3605",
    "nopost_p3650": "NO3650",
    "nopost_p3695": "NO3695",
    "nopost_p5300": "NO5300",
    "nopost_p5400": "NO5400",
    "nopost_p5420": "NO5420",
    "nopost_p5900": "NO5900",
    "nopost_p6100": "NO6100",
    "nopost_p6200": "NO6200",
    "nopost_p6340": "NO6340",
    "nopost_p6395": "NO6395",
    "nopost_p6600": "NO6600",
    "nopost_p6695": "NO6695",
    "nopost_p7000": "NO7000",
    "nopost_p7020": "NO7020",
    "nopost_p7040": "NO7040",
    "nopost_p7080": "NO7080",
    "nopost_p7098": "NO7098",
    "nopost_p7155": "NO7155",
    "nopost_p7165": "NO7165",
    "nopost_p7295": "NO7295",
    "nopost_p7330": "NO7330",
    "nopost_p7350": "NO7350",
    "nopost_p7370": "NO7370",
    "nopost_p7490": "NO7490",
    "nopost_p7495": "NO7495",
    "nopost_p7500": "NO7500",
    "nopost_p7565": "NO7565",
    "nopost_p7600": "NO7600",
}

variabel_valg = {**positive_fem_siffer, **positive_to_siffer}
# sort descending by nopost for nice UI
HEATMAP_VARIABLES = dict(
    sorted(variabel_valg.items(), key=lambda item: int(item[0][-4:]))
)

DETAIL_GRID_ID_COLS = [
    "navn",
    "sfnr",
    "orgnr_f",
    "orgnr_b",
    "naring_f",
    "naring_b",
    "reg_type_f",
    "reg_type_b",
    "type",
    "kommune_f",
    "kommune_b",
]

FORETAK_OR_BEDRIFT: dict[str, str] = {"Foretak": "foretak", "Bedrifter": "bedrifter"}
MACRO_FILTER_OPTIONS: dict[str, Any] = {
    "Se valgene under, samlet": HEATMAP_VARIABLES,
    "Må være positive på 2-siffer": positive_to_siffer,
    "Må være positive på 5-siffer": positive_fem_siffer,
}
NACE_LEVEL_OPTIONS: dict[str, int] = {
    "2-siffer": 2,
    "3-siffer": 4,
    "4-siffer": 5,
    "5-siffer": 6,
}


class MacroNspekPostControl:
    """The MacroNspekPostControl module lets you view macro values for your variables and directly get a micro view for selected macro field.

    This module requires some adjustment to fit your data structure and requires specific variables defined in the variable selector.

    Note:
        Current implementation is locked into a specific data structure.
    """

    # TODO: Loosen constraints on datastructure.

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the callbacks.
            "ident",
            "foretak",
            "bedrift",
            "valgt_tabell",
            "altinnskjema",
        ]
    )

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroNspekPostControl.

        The MacroNspekPostControl allows viewing macro values and getting micro-level views for selected fields.
        The base_path is used by load_year to locate parquet files.

        Args:
            time_units: Your time variables used in the variable selector. Example year, quarter, month, etc.
            conn: A connection object to a database (kept for compatibility, but DuckDB is used internally).
                Currently designed with parquet files in GC in mind.
            base_path: Base path to parquet files
                (e.g., "/buckets/produkt/naringer/klargjorte-data/statistikkfiler").
        """
        # if not isinstance(base_path, str):
        #     raise TypeError(
        #         f"'base_path' must be str and refer to the start of your parquet file path, got: {type(base_path)}"
        #     )

        if time_units != ["aar"]:
            raise ValueError(f"'time-units' must be ['aar'], got: {time_units}")

        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        # TODO: Add functionality for EimerDB
        # if not isinstance(conn, EimerDBInstance) and conn.__class__.__name__ != "Backend":
        #     raise TypeError("Argument 'conn' must be an 'EimerDBInstance' or Ibis backend. Received: {type(conn)}")

        self.module_number = MacroNspekPostControl._id_number
        self.module_name = self.__class__.__name__
        MacroNspekPostControl._id_number += 1

        self.icon = "🗹"
        self.label = "Negative NO-poster"
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        logger.debug("TIME UNITS ", self.time_units)

        self.conn = conn
        self.base_path = base_path
        self.parquet_reader = MacroModuleConsolidated_ParquetReader()

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in MacroNspekPostControl._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"MacroNspekPostControl requires the variable selector option '{var}' to be set."
                ) from e

    def _create_layout(self) -> html.Div:
        """Generates the layout for the MacroNspekPostControl."""
        layout = html.Div(
            className="macromodule",
            children=[
                html.Div(
                    className="macromodule-container",
                    children=[
                        # Left column: filters stacked vertically
                        html.Div(
                            className="macromodule-sidebar",
                            children=[
                                html.H1(
                                    [
                                        "Sjekk aggregerte",
                                        html.Br(),
                                        "næringsoppgaveposter",
                                    ],
                                ),
                                html.Label(
                                    "Velg foretak eller bedrift",
                                    className="macromodule-label",
                                ),
                                dcc.RadioItems(
                                    id="macromodule-nopost-foretak-or-bedrift",
                                    className="macromodule-radio-buttons",
                                    options=[
                                        {"label": k, "value": v}
                                        for k, v in FORETAK_OR_BEDRIFT.items()
                                    ],
                                    value=FORETAK_OR_BEDRIFT["Bedrifter"],
                                ),
                                html.Label(
                                    "Velg NO-oversikt",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    className="macromodule-dropdown",
                                    options=[
                                        {"label": k, "value": k}
                                        for k in MACRO_FILTER_OPTIONS.keys()
                                    ],
                                    value="Må være positive på 2-siffer",
                                    id="macromodule-nopost-filter-velger",
                                ),
                                html.Label(
                                    "Velg næring(er)",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    id="macromodule-nopost-naring-velger",
                                    className="macromodule-naring-dropdown",
                                    options=[],
                                    multi=True,
                                    value=[],
                                    placeholder="Velg næring(er) ...",
                                    maxHeight=300,
                                ),
                                html.Label(
                                    "Velg NACE-siffernivå",
                                    className="macromodule-label",
                                ),
                                dcc.RadioItems(
                                    id="macromodule-nopost-nace-siffer-velger",
                                    className="macromodule-radio-buttons",
                                    options=[
                                        {"label": k, "value": v}
                                        for k, v in NACE_LEVEL_OPTIONS.items()
                                    ],
                                    value=NACE_LEVEL_OPTIONS["2-siffer"],
                                ),
                            ],
                        ),
                        # Right column: AG Grid table container
                        html.Div(
                            className="macromodule-heatmap-grid-container",
                            children=[
                                AgGrid(
                                    id="macromodule-nopost-heatmap-grid",
                                    getRowId="params.data.id",  # Add id to each row
                                    defaultColDef={
                                        "sortable": True,
                                        "filter": True,
                                        "resizable": True,
                                    },
                                    columnSize=None,
                                    rowData=[],
                                    columnDefs=[],
                                    dashGridOptions={
                                        "rowSelection": "single",
                                        "enableCellTextSelection": True,
                                        "enableBrowserTooltips": True,
                                    },
                                    style={"height": "100%", "width": "100%"},
                                )
                            ],
                        ),
                    ],
                ),
                # Full-width "micro" detail grid
                html.Div(
                    className="macromodule-detail-grid-container",
                    children=[
                        html.H5(id="macromodule-nopost-detail-grid-title"),
                        dcc.Loading(
                            type="circle",
                            color="#454545",
                            children=[
                                AgGrid(
                                    id="macromodule-nopost-detail-grid",
                                    defaultColDef={
                                        "sortable": True,
                                        "filter": True,
                                        "resizable": True,
                                    },
                                    columnSize=None,
                                    rowData=[],
                                    columnDefs=[],
                                    rowClassRules={
                                        "macromodule-naring-mismatch": {
                                            "function": "MacroModule.displayNaringRowMismatch(params)"
                                        }
                                    },
                                    dashGridOptions={
                                        "enableCellTextSelection": True,
                                        "pagination": True,
                                        "paginationPageSize": 15,
                                        "tooltipInteraction": True,
                                    },
                                    style={"height": "750px", "width": "100%"},
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
        logger.debug("Layout generated.")
        return layout

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

    def _get_nace_options(self, base_path: str, aar: str) -> list[str]:
        """Get distinct NACE codes for a given year."""
        if int(aar) > 2023:  # new nedtrekk in Dapla has a specific file path
            file_path = f"{base_path}/p{aar}/temp/nedtrekk_dapla/statistiske_foretak_bedrifter.parquet"
        elif int(aar) == 2023:
            file_path = f"{base_path}/p{aar}/statistiske_foretak_bedrifter_v2.parquet"
        else:
            file_path = (
                f"{base_path}/p{aar}/statistiske_foretak_bedrifter.parquet"
            )
        t: ibis.TableExpr = self.parquet_reader.conn.read_parquet(file_path).select("naring")
        naring_filter = t.naring.substr(0, length=2).name("nace2")
        t = t.select(naring_filter).distinct()
        df: DataFrame = t.to_pandas()
        return sorted(df["nace2"].astype(str))

    def module_callbacks(self) -> None:
        """Defines the callbacks for the MacroNspekPostControl module."""
        # dynamic_states = self.variableselector.get_all_inputs()

        @callback(
            Output("macromodule-nopost-naring-velger", "options"),
            Input("var-aar", "value"),
        )
        def _update_nace_options(aar: str) -> list[str] | list[dict[str, str]]:
            """Populate NACE dropdown with options from selected year."""
            if not aar:
                return []
            try:
                nace_options = self._get_nace_options(self.base_path, aar)
                return [{"label": n, "value": n} for n in nace_options]
            except Exception as e:
                logger.error(f"Error loading NACE options: {e}")
                return []

        @callback(
            Output("macromodule-nopost-heatmap-grid", "rowData"),
            Output("macromodule-nopost-heatmap-grid", "columnDefs"),
            Output("macromodule-nopost-heatmap-grid", "pinnedTopRowData"),
            Input("var-aar", "value"),
            Input("macromodule-nopost-foretak-or-bedrift", "value"),
            Input("macromodule-nopost-filter-velger", "value"),
            Input("macromodule-nopost-nace-siffer-velger", "value"),
            Input("macromodule-nopost-naring-velger", "value"),
            allow_duplicate=True,
        )
        def update_graph(
            variabelvelger_aar: str,
            foretak_or_bedrift: str,
            macro_level: str,
            nace_siffer_level: int,
            nace_list: list[str],
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            """Creates a colour-coordinated matrix heatmap of aggregated values based on their %-change from the previous year."""
            if not nace_list or not macro_level or not variabelvelger_aar:
                return [], [], []

            if not isinstance(variabelvelger_aar, str):
                raise TypeError(
                    f"'var-aar' must be str, got: {type(variabelvelger_aar)}"
                )

            aar: int = int(variabelvelger_aar)

            t: ibis.TableExpr = self.parquet_reader.load_year(
                aar,
                self.base_path,
                foretak_or_bedrift,
                nace_list,
                nace_siffer_level,
                detail_grid=False,
            )

            var_dict = MACRO_FILTER_OPTIONS[macro_level]

            # count units
            unit_type: Literal["orgnr_foretak", "orgnr_bedrift"] = (
                "orgnr_foretak" if foretak_or_bedrift == "foretak" else "orgnr_bedrift"
            )
            count_distinct: Table = t.filter(t.aar == f"{aar}").select(
                unit_type, "selected_nace"
            )
            distinct_counts = (
                count_distinct.group_by("selected_nace")
                .aggregate(unique_units=count_distinct[unit_type].nunique())
                .order_by("selected_nace")
            )
            distinct_df = distinct_counts.execute()

            # safe column names
            count_row: dict[str, Any] = {
                col.replace(".", "_"): int(row["unique_units"])
                for _, row in distinct_df.iterrows()
                for col in [row["selected_nace"]]
            }

            category_column = "nopost"

            cols = [*list(var_dict.keys()), "naring", "aar"]

            t = t.select([*cols, "selected_nace"])

            # rename and cast numerics to float in case of yearly type mismatches
            for col in var_dict.keys():
                if col in t.columns:
                    t = t.mutate(**{col: t[col].cast("float64")})

            agg_dict = {alias: t[db_col].sum() for db_col, alias in var_dict.items()}

            df = t.group_by("selected_nace").aggregate(**agg_dict)

            df = df.pivot_longer(
                var_dict.values(), names_to="nopost", values_to="value"
            )

            df = df.rename(nace="selected_nace").execute()
            df.columns = df.columns.astype(str)  # set to str in case aar loaded as int

            matrix = df.pivot(
                index=category_column, columns="nace", values="value"
            ).reset_index()
            matrix[category_column] = matrix[category_column].fillna("UKJENT")
            matrix.iloc[:, 1:] = matrix.iloc[:, 1:].fillna(0)

            custom_order = list(var_dict.values())
            matrix = matrix.set_index(category_column).loc[custom_order].reset_index()

            # safe column names for NACE keys by replacing '.' with '_'
            original_cols: list[str] = matrix.columns.astype(str).tolist()
            safe_cols: list[str] = [c.replace(".", "_") for c in original_cols]
            matrix.columns = safe_cols

            # add count units & ID columns
            count_row[category_column] = "antall enheter"
            count_row["id"] = "count_row"

            matrix["id"] = matrix.index.astype(dtype=str)
            matrix[category_column] = matrix[category_column].astype(dtype=str)

            row_data: list[dict[str, Any]] | Any = matrix.to_dict("records")

            def _create_column_defs(
                original_cols: list[str], safe_cols: list[str], category_column: str
            ) -> list[Any]:
                """Create column definitions to include styling, tooltips and cell coloring to create the heatmap."""
                col_defs = []
                for orig_col, safe_col in zip(original_cols, safe_cols, strict=True):
                    col_def = {
                        "headerName": orig_col,
                        "field": safe_col,
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                        "filterParams": {"buttons": ["reset"]},
                    }

                    if safe_col != category_column:

                        formatter_func = f"MacroModule.formatHeatmapValue(params, 2)"
                        style_func = "MacroModule.displaySimpleHeatMap(params)"

                        col_def.update(
                            {
                                "type": "rightAligned",
                                "tooltipField": f"{safe_col}_tooltip",
                                "valueFormatter": {"function": formatter_func},
                                "cellStyle": {"function": style_func},
                                "filter": "agNumberColumnFilter",
                            }
                        )

                    col_defs.append(col_def)

                if col_defs:
                    col_defs[0]["pinned"] = "left"
                    col_defs[0]["width"] = 200 if category_column == "variabel" else 125

                return col_defs

            column_defs = _create_column_defs(original_cols, safe_cols, category_column)

            return row_data, column_defs, [count_row]

        @callback(
            Output("macromodule-nopost-detail-grid", "rowData"),
            Output("macromodule-nopost-detail-grid", "columnDefs"),
            Output("macromodule-nopost-detail-grid-title", "children"),
            Output("macromodule-nopost-detail-grid", "columnState"),
            Output("macromodule-nopost-detail-grid", "resetColumnState"),
            Output("macromodule-nopost-detail-grid", "filterModel"),
            Output("macromodule-nopost-detail-grid", "paginationGoTo"),
            Input("macromodule-nopost-heatmap-grid", "cellClicked"),
            State("var-aar", "value"),
            State("macromodule-nopost-foretak-or-bedrift", "value"),
            State("macromodule-nopost-heatmap-grid", "rowData"),
            State("macromodule-nopost-filter-velger", "value"),
            State("macromodule-nopost-nace-siffer-velger", "value"),
            prevent_initial_call=True,
        )
        def update_detail_table(
            cell_data: dict[str, Any] | None,
            variabelvelger_aar: str,
            foretak_or_bedrift: str,
            heatmap_row_data: list[dict[str, Any]],
            macro_level: str | None,
            nace_siffer_level: int,
        ) -> tuple[
            list[dict[Hashable, Any]],
            list[dict[str, Any]],
            str,
            list[dict[str, Any]],
            bool,
            None,
            int,
        ]:
            """Table with foretak & bedrift-level details which updates when user selects a cell in heatmap-grid."""
            if not cell_data or not variabelvelger_aar:
                raise PreventUpdate

            row_id = cell_data.get("rowId", "")
            if row_id == "count_row":
                raise PreventUpdate

            col = cell_data.get("colId")
            if col in ["variabel", macro_level]:
                raise PreventUpdate

            assert isinstance(col, str)
            selected_nace = col.replace("_", ".")
            row_idx = int(row_id)

            if not selected_nace:
                raise PreventUpdate

            assert macro_level is not None
            var_dict = MACRO_FILTER_OPTIONS[macro_level]

            selected_filter_val = heatmap_row_data[row_idx].get("nopost")
            if selected_filter_val is None or pd.isna(selected_filter_val):
                raise PreventUpdate

            aar: int = int(variabelvelger_aar)

            # read in every unit in selected nace
            t_filtered: ibis.TableExpr = self.parquet_reader.load_year(
                aar,
                self.base_path,
                foretak_or_bedrift,
                [selected_nace],
                nace_siffer_level,
                detail_grid=True,
            )

            assert isinstance(macro_level, str)

            t_filtered = t_filtered.mutate(
                **{
                    macro_level: t_filtered.kommune.substr(0, length=4)
                    .fill_null("UKJENT")
                    .replace("", "UKJENT")
                }
            )

            select_cols = [
                "navn",
                "sfnr",
                "orgnr_foretak",
                "naring",
                "naring_f",
                "reg_type",
                "reg_type_f",
                "type",
                "kommune",
                *var_dict.keys(),
                "giver_fnr",
                "giver_bnr",
            ]
            if foretak_or_bedrift == "bedrifter":
                select_cols.append("orgnr_bedrift")
            t_filtered = t_filtered.select(
                [c for c in select_cols if c in t_filtered.columns]
            )

            if foretak_or_bedrift == "foretak":
                rename_mapping = {
                    "naring_f": "naring",
                    "reg_type_f": "reg_type",
                    "orgnr_f": "orgnr_foretak",
                    "kommune_f": "kommune",
                }
                kommune_col = "kommune_f"
                naring_col = "naring_f"
            elif foretak_or_bedrift == "bedrifter":
                rename_mapping = {
                    "naring_b": "naring",
                    "reg_type_b": "reg_type",
                    "orgnr_f": "orgnr_foretak",
                    "orgnr_b": "orgnr_bedrift",
                    "kommune_b": "kommune",
                }
                kommune_col = "kommune_b"
                naring_col = "naring_b"

            t = t_filtered.rename(**rename_mapping)

            for col in var_dict.keys():
                if col in t.columns:
                    t = t.mutate(**{col: t[col].cast("float64")})

            df = t.rename(
                {v: k for k, v in var_dict.items() if k in t.columns}
            ).execute()

            if (
                "giver_bnr" in df.columns and "giver_fnr" in df.columns
            ):  # unngå foretakstabellar som ikkje har giver
                df["giver_fnr_tooltip"] = "Giverforetak: " + df["giver_fnr"].astype(str)
                df["giver_bnr_tooltip"] = "Giverbedrifter: " + df["giver_bnr"].astype(
                    str
                )

            # order for columns
            if selected_filter_val in df.columns:
                metrics_order = [selected_filter_val]
            else:
                metrics_order = []
            metrics_order += [
                var_dict.get(v, v)
                for v in var_dict
                if var_dict.get(v, v) != selected_filter_val
            ]

            visible_cols = [
                c for c in DETAIL_GRID_ID_COLS + metrics_order if c in df.columns
            ]

            df = df.sort_values(selected_filter_val, ascending=True)
            row_data: list[dict[Hashable, Any]] | Any = df.to_dict("records")

            column_defs = []
            for col in visible_cols:
                col_def = {
                    "headerName": col,
                    "field": col,
                    "width": 140,
                    "filterParams": {"buttons": ["reset"]},
                }

                if col == "orgnr_f" and "giver_fnr_tooltip" in df.columns:
                    col_def["tooltipField"] = "giver_fnr_tooltip"
                elif col == "orgnr_b" and "giver_bnr_tooltip" in df.columns:
                    col_def["tooltipField"] = "giver_bnr_tooltip"
                elif f"{col}_tooltip" in df.columns:
                    col_def["tooltipField"] = f"{col}_tooltip"

                if col not in DETAIL_GRID_ID_COLS:
                    col_def["valueFormatter"] = {
                        "function": "MacroModule.formatDetailGridValue(params)"
                    }

                if df[col].dtypes == "float":
                    col_def["filter"] = "agNumberColumnFilter"

                column_defs.append(col_def)

            if column_defs:
                column_defs[0]["pinned"] = "left"
                column_defs[0]["width"] = 240

            title = f"{foretak_or_bedrift.capitalize()} i næring {selected_nace}"

            return row_data, column_defs, title, [], True, None, 0

        @callback(
            Output("macromodule-nopost-detail-grid", "rowData", allow_duplicate=True),
            Output(
                "macromodule-nopost-detail-grid", "columnDefs", allow_duplicate=True
            ),
            Output(
                "macromodule-nopost-detail-grid-title", "children", allow_duplicate=True
            ),
            Input("var-aar", "value"),
            Input("macromodule-nopost-foretak-or-bedrift", "value"),
            Input("macromodule-nopost-filter-velger", "value"),
            Input("macromodule-nopost-nace-siffer-velger", "value"),
            Input("macromodule-nopost-naring-velger", "value"),
            prevent_initial_call=True,
        )
        def reset_detail_grid_on_filter_change(*args: Any) -> tuple[list, list, str]:
            """Reset detail grid when any filter changes."""
            return [], [], ""

        @callback(  # type: ignore[misc]
            Output("var-ident", "value", allow_duplicate=True),
            Output("var-bedrift", "value", allow_duplicate=True),
            Output("altinnedit-option1", "value", allow_duplicate=True),
            Input("macromodule-nopost-detail-grid", "cellClicked"),
            State("macromodule-nopost-detail-grid", "rowData"),
            prevent_initial_call=True,
        )
        def output_to_variabelvelger(
            clickdata: dict | None, rowdata: list[dict[str, Any]]
        ) -> tuple[str, str, str]:
            """Handle cell clicks in detail grid and update variable selector in the Dash app."""
            if not clickdata:
                raise PreventUpdate

            row_id = clickdata.get("rowId")
            col_id = clickdata.get("colId")

            if row_id is None or col_id not in ("orgnr_f", "orgnr_b", "navn"):
                raise PreventUpdate

            row_idx = int(row_id)
            if row_idx >= len(rowdata):
                raise PreventUpdate

            clicked_row = rowdata[row_idx]
            bedrift = ""

            if col_id in ("orgnr_f", "navn"):
                tabell = "skjemadata_foretak"
            elif col_id == "orgnr_b":
                bedrift = clicked_row.get("orgnr_b", "")
                tabell = "skjemadata_bedriftstabell"
            else:
                raise PreventUpdate

            ident = clicked_row.get("orgnr_f", "")

            return (
                str(ident) if ident else "",
                str(bedrift) if bedrift else "",
                str(tabell) if tabell else "",
            )


class MacroNspekPostControlTab(TabImplementation, MacroNspekPostControl):
    """MacroNspekPostControlTab is an implementation of the MacroNspekPostControl module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroNspekPostControlTab class."""
        MacroNspekPostControl.__init__(
            self, time_units=time_units, conn=conn, base_path=base_path
        )
        TabImplementation.__init__(self)


class MacroNspekPostControlWindow(WindowImplementation, MacroNspekPostControl):
    """MacroNspekPostControlWindow is an implementation of the MacroNspekPostControl module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroNspekPostControlWindow class."""
        MacroNspekPostControl.__init__(
            self, time_units=time_units, conn=conn, base_path=base_path
        )
        WindowImplementation.__init__(self)
