import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar
import os
# import sqlite3
import pandas as pd
import duckdb

from dash_ag_grid import AgGrid
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
from eimerdb import EimerDBInstance

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils import active_no_duplicates_refnr_list
from ..utils import conn_is_ibis
from ..utils.eimerdb_helpers import create_partition_select
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)

# Variables used in the heatmap-grid
HEATMAP_VARIABLES = {
    "omsetning": "omsetning",
    "ts_forbruk": "forbruk",
    "ts_salgsint": "salgsint",
    "sysselsetting_syss": "sysselsatte",
    "sysselsetting_ansatte": "lønnstakere",
    "sysselsetting_arsverk": "årsverk",
    "nopost_lonnskostnader": "lønnskost",
    "nopost_p5000": "lønn",
    "ts_vikarutgifter": "vikarutg",
    "produksjonsverdi": "prodv",
    "bearbeidingsverdi": "bearbv",
    "produktinnsats": "prodins",
    "nopost_driftskostnader": "driftskost",
    "nopost_driftsresultat": "driftsres",
    "brutto_driftsresultat": "brut_driftsres",
    "ts_varehan": "varehandel",
    "nopost_p4005": "p4005",
    "totkjop": "totalkjøp",
    "ts_anlegg": "anlegg",
    "bruttoinvestering_oslo": "brut_inv_oslo",
    "bruttoinvestering_kvgr": "brut_inv_kvgr",
}

FORETAK_OR_BEDRIFT = {"Foretak": "foretak", "Bedrifter": "bedrifter"}
MACRO_FILTER_OPTIONS = {"fylke": 2, "kommune": 4, "sammensatte variabler": HEATMAP_VARIABLES}
NACE_LEVEL_OPTIONS = {"2-siffer": 2, "3-siffer": 4, "4-siffer": 5, "5-siffer": 6}
HEATMAP_NUMBER_FORMAT = {"Prosentendring": True, "Totalsum": False}

class MacroModule_ParquetReader:
    """Helper class for reading and querying Parquet files with DuckDB."""
    
    def __init__(self):
        """Initialize a persistent DuckDB connection."""
        self.conn = duckdb.connect()
    
    def query_multi_year(
        self, 
        base_path: str, 
        foretak_or_bedrift: str,
        years: list[int],
        query_template: str
    ) -> pd.DataFrame:
        """
        Query multiple years of Parquet files and combine them.
        
        Args:
            base_path: Base path template
            foretak_or_bedrift: Either "foretak" or "bedrifter"
            years: List of years to query
            query_template: SQL query with 'data' as table name
            
        Returns:
            Combined DataFrame with aar column added
        """
        # # Build UNION ALL query for multiple years
        # union_parts = []
        # for year in years:
        #     file_path = f"{base_path}/aar={year}/statistikkfil_{foretak_or_bedrift}_nr.parquet"
        #     union_parts.append(f"""
        #         SELECT *, {year} as aar 
        #         FROM read_parquet('{file_path}', hive_partitioning = False)
        #     """)
        
        # union_query = " UNION ALL ".join(union_parts)
        
        # # Wrap the union in a CTE and apply the user's query
        # full_query = f"""
        # WITH data AS (
        #     {union_query}
        # )
        # {query_template}
        # """
        # logger.debug(full_query)
        # logger.debug(self.conn.execute(full_query).df().head(5))

        # return self.conn.execute(full_query).df()

        # 1. Determine all columns across years
        all_cols = set()
        for year in years:
            file_path = f"{base_path}/aar={year}/statistikkfil_{foretak_or_bedrift}_nr.parquet"
            cols = [row[0] for row in self.conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}', hive_partitioning=False)").fetchall()]
            all_cols.update(cols)
        
        # 2. Build per-year SELECTs with missing columns as NULL
        selects = []
        for year in years:
            file_path = f"{base_path}/aar={year}/statistikkfil_{foretak_or_bedrift}_nr.parquet"
            cols_in_file = [row[0] for row in self.conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}', hive_partitioning=False)").fetchall()]
            missing_cols = all_cols - set(cols_in_file)
            missing_expr = ", ".join(f"NULL AS {col}" for col in missing_cols)
            select_expr = f"SELECT *, {missing_expr}, {year} AS aar FROM read_parquet('{file_path}', hive_partitioning=False)"
            selects.append(f"({select_expr})")
        
        # 3. UNION ALL per-year
        union_query = " UNION ALL ".join(selects)
        full_query = query_template.replace("FROM data", f"FROM ({union_query}) AS data")
        
        # 4. Execute
        return self.conn.execute(full_query).df()
    
    def query_single_year(self, base_path: str, foretak_or_bedrift: str, 
                          year: int, query: str) -> pd.DataFrame:
        """Query a single year's Parquet file."""
        file_path = f"{base_path}/aar={year}/statistikkfil_{foretak_or_bedrift}_nr.parquet"
        
        full_query = f"""
        WITH data AS (
            SELECT * FROM read_parquet('{file_path}')
        )
        {query}
        """
        return self.conn.execute(full_query).df()
    
    def close(self):
        """Close the DuckDB connection."""
        self.conn.close()

class MacroModule(ABC):
    """The MacroModule module lets you view macro values for your variables and directly get a micro view for selected macro field.

    This module requires some adjustment to fit your data structure and requires specific variables defined in the variable selector.

    Note:
        Current implementation is locked into a specific data structure.
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

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroModule.

        Args:
            time_units (list[str]): Your time variables used in the variable selector. Example year, quarter, month, etc.
            conn (object): A connection object to a database (kept for compatibility, but DuckDB is used internally).
                Currently designed with parquet files in GC in mind.
            base_path (str): Base path to parquet files (e.g., "/buckets/produkt/naringer/klargjorte-data/statistikkfiler")
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        #        if not isinstance(conn, EimerDBInstance) and conn.__class__.__name__ != "Backend":
        #            raise TypeError("Argument 'conn' must be an 'EimerDBInstance' or Ibis backend. Received: {type(conn)}")
        self.module_number = MacroModule._id_number
        self.module_name = self.__class__.__name__
        MacroModule._id_number += 1

        self.icon = "🌍"
        self.label = "Macromodule"

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
        self.parquet_reader = MacroModule_ParquetReader()

        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in MacroModule._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"MacroModule requires the variable selector option '{var}' to be set."
                ) from e

    def get_nace_options(self, aar: int) -> list[str]:
        """Get distinct NACE codes for a given year."""
        query = """
        SELECT DISTINCT substr(naring, 1, 2) AS naring_kode
        FROM data
        WHERE naring IS NOT NULL
        ORDER BY naring_kode
        """
        
        df = self.parquet_reader.query_single_year(
            base_path=self.base_path,
            foretak_or_bedrift="bedrifter",
            year=aar,
            query=query
        )

        return sorted(df["naring_kode"].dropna().astype(str).unique())

    def _create_layout(self) -> html.Div:
        """Generates the layout for the MacroModule."""
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
                                "Aggregerte",
                                html.Br(),
                                "næringsendringer"
                            ], 
                            ),
                                html.Label(
                                    "Velg foretak eller bedrift",
                                    className="macromodule-label",
                                ),
                                # dcc.Dropdown(
                                #     className="macromodule-dropdown",
                                #     options=[
                                #         {"label": k, "value": k} for k in FORETAK_OR_BEDRIFT.keys()
                                #     ],
                                #     value="Bedrifter",
                                #     id="macromodule-foretak-or-bedrift",
                                # ),
                                dcc.RadioItems(
                                    id="macromodule-foretak-or-bedrift",
                                    className="macromodule-radio-buttons",
                                    options=[
                                        {"label": k, "value": v}
                                        for k, v in FORETAK_OR_BEDRIFT.items()
                                    ],
                                    value=FORETAK_OR_BEDRIFT["Bedrifter"],
                                ),

                                html.Label(
                                    "Velg kategori-inndeling",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    className="macromodule-dropdown",
                                    options=[
                                        {"label": k, "value": k} for k in MACRO_FILTER_OPTIONS.keys()
                                    ],
                                    value="fylke",
                                    id="macromodule-filter-velger",
                                ),

                                html.Label(
                                    "Velg variabel",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    className="macromodule-dropdown",
                                    options=[
                                        {"label": HEATMAP_VARIABLES.get(v, v), "value": v} for v in HEATMAP_VARIABLES
                                    ],
                                    value="produksjonsverdi",
                                    id="macromodule-macro-variable",
                                ),

                                html.Label(
                                    "Velg næring(er)",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    id="macromodule-naring-velger",
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
                                    id="macromodule-nace-siffer-velger",
                                    className="macromodule-radio-buttons",
                                    options=[
                                        {"label": k, "value": v}
                                        for k, v in NACE_LEVEL_OPTIONS.items()
                                    ],
                                    value=NACE_LEVEL_OPTIONS["3-siffer"],
                                ),

                                html.Label(
                                    "Velg tallvisning",
                                    className="macromodule-label",
                                ),
                                dcc.RadioItems(
                                    id="macromodule-tall-visning-velger",
                                    className="macromodule-radio-buttons",
                                    options=[
                                        {"label": k, "value": v}
                                        for k, v in HEATMAP_NUMBER_FORMAT.items()
                                    ],
                                    value=HEATMAP_NUMBER_FORMAT["Prosentendring"],
                                ),
                            ],
                        ),
                        # Right column: AG Grid table container
                        html.Div(
                            className="macromodule-heatmap-grid-container",
                            children=[
                                AgGrid(
                                    id="macromodule-heatmap-grid",
                                    className="macromodule-heatmap-grid",
                                    getRowId="params.data.id",  # Add id to each row
                                    defaultColDef={
                                        "sortable": True,
                                        "filter": True,
                                        "resizable": True,
                                        "width": 120,
                                    },
                                    columnSize=None,
                                    rowData=[],
                                    columnDefs=[],
                                    dashGridOptions={
                                        "rowSelection": "single", 
                                        "enableCellTextSelection": True, 
                                        'enableBrowserTooltips': True,
                                    },
                                    style={"height": "100%", "width": "100%"},
                                )
                            ],
                        ),
                    ],
                ),

                # Full-width detail grid
                html.Div(
                    className="macromodule-detail-grid-container",
                    children=[
                        html.H3(id="macromodule-detail-grid-title"),
                        dcc.Loading(
                            type="circle",
                            color="#454545",
                            children=[
                                AgGrid(
                                    id="macromodule-detail-grid",
                                    defaultColDef={
                                        "sortable": True,
                                        "filter": True,
                                        "resizable": True,
                                    },
                                    columnSize=None,
                                    rowData=[],
                                    columnDefs=[],
                                    dashGridOptions={
                                        "enableCellTextSelection": True, 
                                        "pagination": True, 
                                        "paginationPageSize": 15,
                                        'tooltipInteraction': True
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

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the MacroModule module.

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
        """Defines the callbacks for the MacroModule module."""
        # dynamic_states = self.variableselector.get_all_inputs()

        @callback(
            Output("macromodule-naring-velger", "options"),
            Input("var-aar", "value"),
        )
        def update_nace_options(aar):
            """Populate NACE dropdown with options from selected year."""
            if not aar:
                return []
            try:
                nace_options = self.get_nace_options(aar)
                return [{"label": n, "value": n} for n in nace_options]
            except Exception as e:
                logger.error(f"Error loading NACE options: {e}")
                return []

        @callback(
            Output("macromodule-heatmap-grid", "rowData"),
            Output("macromodule-heatmap-grid", "columnDefs"),
            Input("var-aar", "value"),
            Input("macromodule-foretak-or-bedrift", "value"),
            Input("macromodule-macro-variable", "value"),
            Input("macromodule-filter-velger", "value"),
            Input("macromodule-nace-siffer-velger", "value"),
            Input("macromodule-naring-velger", "value"),
            Input("macromodule-tall-visning-velger", "value"),
            allow_duplicate=True,
        )
        
        # TODO: Set up a way to get aar from variabelvelger. Can read variabelvelgeren.md or hurtigstart.md for instance.
        
        def update_graph(aar, foretak_or_bedrift, variabel, macro_level, nace_siffer_level, nace, tallvisning_valg):
            """
            Creates a colour-coordinated matrix heatmap of aggregated values 
            based on their %-change from the previous year
            """

            if not nace or not variabel or not macro_level or not aar:
                return [], []

            aar = int(aar)
            logger.debug(f"Datatype for aar: {type(aar)}, aar: {aar}")
            years = [aar, aar-1]
            
            naring_filter = ", ".join(f"'{n}'" for n in nace)

            if macro_level == "sammensatte variabler":
                var_selects = ",\n".join([f"SUM(CAST({db_col} AS DOUBLE)) AS {alias}" for db_col, alias in HEATMAP_VARIABLES.items()])
                group_by = "nace"
                select_extra = ""
            else:
                var_selects = f"SUM(CAST({variabel} AS DOUBLE)) AS sum_{variabel}"
                group_by = f"{macro_level}, nace"
                select_extra = f"substr(kommune, 1, {MACRO_FILTER_OPTIONS[macro_level]}) AS {macro_level},"

            # TODO: Add eimerdb as an option
            
            # Query has to read both years?
            query = f"""
                SELECT
                    substr(naring, 1, {nace_siffer_level}) AS nace,
                    {select_extra}
                    {var_selects},
                    aar
                FROM data
                WHERE
                    aar IN ({years[0]}, {years[1]}) AND
                    substr(naring, 1, 2) IN ({naring_filter})
                GROUP BY
                    aar,
                    {group_by};
                """
            df = self.parquet_reader.query_multi_year(
                    base_path=self.base_path,
                    foretak_or_bedrift=foretak_or_bedrift,
                    years=years,
                    query_template=query
                )
            
            logger.debug(df.head(2))
            
            if macro_level == "sammensatte variabler":
                df = df.pivot_table(
                    index=["nace", "aar"],
                    values=HEATMAP_VARIABLES.values(),
                    aggfunc="sum"
                ).reset_index()
                df = df.melt(id_vars=["nace", "aar"], var_name="variabel", value_name="value")
                df = df.pivot(index=["variabel", "nace"], columns="aar", values="value").reset_index()
                category_column = "variabel"

            else:
                df = df.pivot_table(
                    index=[f"{macro_level}", "nace"],
                    columns="aar",
                    values=f"sum_{variabel}"
                ).reset_index()
                category_column = macro_level

            df.columns = df.columns.map(str) # Set to str in case aar loaded as int

            # Percentage change from previous year
            df[[f"{aar}", f"{aar-1}"]] = df[[f"{aar}", f"{aar-1}"]]
            df["diff"] = df[f"{aar}"] - df[f"{aar-1}"]
            df["percent_diff"] = df["diff"] / df[f"{aar-1}"]

            if tallvisning_valg: # = True, showing %-diff
                tallvisning = "percent_diff"
            else: # = False, showing total value instead of %-diff
                tallvisning = f"{aar}"

            matrix = df.pivot(
                index=category_column, 
                columns="nace", 
                values=tallvisning
            ).reset_index().fillna(0)

            # Keep specified order instead of alphabetical ordering
            if category_column == "variabel":
                custom_order = list(HEATMAP_VARIABLES.values())
                matrix = matrix.set_index("variabel").loc[custom_order].reset_index()

            # For nice UI: safe column names for field keys by replacing '.' with '_'
            original_cols = matrix.columns.astype(str).tolist()
            safe_cols = [c.replace(".", "_") for c in original_cols]
            matrix.columns = safe_cols
            # ID column
            matrix["id"] = matrix.index.astype(str)
            row_data = matrix.to_dict("records")

            ############################################ Kan endre aar til years[0] osv.
            def generate_tooltips(row_data, df, category_column, safe_cols):
                """
                Create tooltips showing the raw data from each year and the diff,
                so the user can see both the %-diff in the cell and also the raw data when hovering.
                """
                for row in row_data:
                    for col in safe_cols:
                        if col not in ["id", category_column]:
                            prev_year = df.loc[
                                (df[category_column] == row[category_column]) & 
                                (df["nace"] == col.replace("_", ".")),
                                f"{aar-1}"
                            ]
                            current_year = df.loc[
                                (df[category_column] == row[category_column]) & 
                                (df["nace"] == col.replace("_", ".")),
                                f"{aar}"
                            ]
                            val1 = prev_year.values[0] if not prev_year.empty else 0
                            val2 = current_year.values[0] if not current_year.empty else 0
                            diff = val2 - val1
                            tooltip = f"{aar}: {val2:,.0f}\n{aar-1}: {val1:,.0f}\nDiff: {diff:+,.0f}"
                            row[f"{col}_tooltip"] = tooltip

            def create_column_defs(original_cols, safe_cols, category_column):
                """
                Create column definitions to include styling, tooltips and cell coloring
                to create the heatmap.
                """
                col_defs = []
                for orig_col, safe_col in zip(original_cols, safe_cols):
                    col_def = {
                        "headerName": orig_col,
                        "field": safe_col,
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                    }
                    if safe_col != category_column:
                        # Common properties for data columns
                        col_def.update({
                            "type": "rightAligned",
                            "tooltipField": f"{safe_col}_tooltip",
                        })

                        # Set default formatting (displayDiffHeatMap + %)
                        col_def["valueFormatter"] = {"function": "d3.format(',.1%')(params.value)"}
                        col_def["cellStyle"] = {"function": "MacroModule.displayDiffHeatMap(params)"}

                        # Override if tallvisning_valg is False
                        if tallvisning_valg == False:
                            col_def["valueFormatter"] = {"function": "d3.format(',')(params.value)"}
                            col_def["cellStyle"] = {"function": "MacroModule.displaySimpleHeatMap(params)"}

                    col_defs.append(col_def)

                if col_defs:
                    col_defs[0]["pinned"] = "left"
                    col_defs[0]["width"] = 200 if category_column == "variabel" else 115

                return col_defs

            generate_tooltips(row_data, df, category_column, safe_cols)
            column_defs = create_column_defs(original_cols, safe_cols, category_column)
            
            return row_data, column_defs

        @callback(
            Output("macromodule-detail-grid", "rowData"),
            Output("macromodule-detail-grid", "columnDefs"),
            Output("macromodule-detail-grid-title", "children"),
            Input("var-aar", "value"),
            Input("macromodule-foretak-or-bedrift", "value"),
            Input("macromodule-heatmap-grid", "cellClicked"),
            State("macromodule-heatmap-grid", "rowData"),
            State("macromodule-filter-velger", "value"),
            State("macromodule-nace-siffer-velger", "value"),
            State("macromodule-macro-variable", "value"),
            allow_duplicate=True,
        )

        def update_detail_table(aar, foretak_or_bedrift, cell_data, row_data, macro_level, nace_siffer_level, valgt_variabel):
            """
            Table with foretak & bedrift-level details which updates 
            when user selects a cell in heatmap-grid
            """
            if not cell_data or not aar:
                return [], [], ""

            aar = int(aar)
            years = [aar, aar - 1]
            valgt_variabel = HEATMAP_VARIABLES.get(valgt_variabel)

            col = cell_data.get("colId")
            if col in ["variabel", macro_level]:
                return [], [], ""

            selected_nace = col.replace("_", ".")
            row_idx = int(cell_data.get("rowId"))
            
            if macro_level == "sammensatte variabler":
                selected_filter_val = row_data[row_idx].get("variabel")
                valgt_variabel = selected_filter_val
            else:
                selected_filter_val = row_data[row_idx].get(macro_level)

            if not selected_filter_val or not selected_nace:
                return [], [], ""

            if macro_level not in ("sammensatte variabler"):
                where_filter = f"substr(kommune, 1, {MACRO_FILTER_OPTIONS[macro_level]}) = '{selected_filter_val}' AND"
            else:
                where_filter = ""

            variabel_selects = ",\n".join([
                f"{db_col} AS {alias}" 
                for db_col, alias in HEATMAP_VARIABLES.items()]
            )

            # TODO: Add eimerdb as an option
            
            # Change to duckdb and read for both years
            query = f"""
                SELECT 
                    navn,
                    orgnr_foretak as orgnr_f,
                    orgnr_bedrift as orgnr_b, 
                    naring_f as naring_f,
                    naring as naring_b,
                    reg_type as reg_type,
                    type as type,
                    {variabel_selects},
                    giver_fnr as giver_fnr,
                    giver_bnr as giver_bnr,
                    aar
                FROM data
                WHERE
                    {where_filter}
                    aar IN ({aar}, {aar-1}) AND
                    substr(naring, 1, {nace_siffer_level}) = '{selected_nace}'
                """

            df = self.parquet_reader.query_multi_year(
                    base_path=self.base_path,
                    foretak_or_bedrift=foretak_or_bedrift,
                    years=years,
                    query_template=query
                )

            logger.debug(df.head(2))

            df_current = df[df['aar'] == aar].copy()
            df_previous = df[df['aar'] == aar - 1].copy()

            df_previous.drop(columns='aar', inplace=True)
            df_current.drop(columns='aar', inplace=True)

            df_merged = df_current.merge(
                df_previous,
                on=['orgnr_f', 'orgnr_b'],
                how='left',
                suffixes=('', '_x'))

            df = df_merged.copy()

            df["giver_fnr_tooltip"] = "Giverforetak: " + df["giver_fnr"].astype(str)
            df["giver_bnr_tooltip"] = "Giverbedrift: " + df["giver_bnr"].astype(str)
            for col in ["naring_f", "naring_b", "type"]:
                if f"{col}_x" in df.columns:
                    df[f"{col}_tooltip"] = "Fjorårets verdi: " + df[f"{col}_x"].astype(str)

            id_cols = ['navn', 'orgnr_f', 'orgnr_b', 'naring_f', 'naring_b', "reg_type", "type"]

            # Desired order for columns in dash view
            if valgt_variabel in df.columns:
                metrics_order = [valgt_variabel]
            else:
                metrics_order = []
            metrics_order += [HEATMAP_VARIABLES.get(v, v) for v in HEATMAP_VARIABLES if HEATMAP_VARIABLES.get(v, v) != valgt_variabel]

            ordered_value_cols = []
            for metric in metrics_order:
                current_year_col = metric
                previous_year_col = f"{metric}_x"
                
                if current_year_col in df.columns:
                    ordered_value_cols.append(current_year_col)
                if previous_year_col in df.columns:
                    ordered_value_cols.append(previous_year_col)

            # Column order
            if valgt_variabel in df.columns and f"{valgt_variabel}_x" in df.columns:
                df["diff"] = (df[valgt_variabel] - df[f"{valgt_variabel}_x"]).abs() # Sort by absolute diff
                df = df.sort_values("diff", ascending=False)
                df = df.drop(columns=["diff"])

            row_data = df.to_dict("records")

            visible_cols = id_cols + ordered_value_cols

            column_defs = [] 
            for col in visible_cols:
                col_def = {
                    "headerName": col,
                    "field": col,
                    "width": 140
                    }

                if col == "orgnr_f" and "giver_fnr_tooltip" in df.columns:
                    col_def["tooltipField"] = "giver_fnr_tooltip"
                elif col == "orgnr_b" and "giver_bnr_tooltip" in df.columns:
                    col_def["tooltipField"] = "giver_bnr_tooltip"
                elif f"{col}_tooltip" in df.columns:
                    col_def["tooltipField"] = f"{col}_tooltip"

                if col not in id_cols:
                    col_def["valueFormatter"] = {"function": "params.value == null ? '' : d3.format(',')(params.value)"} # Thousand sep.
                    if col.endswith("_x"):
                        col_def["cellStyle"] = {
                            "backgroundColor": "#e8e9eb"  # light grey for previous year
                        }
                
                if col in ["orgnr_f", "naring_f", "naring_b", "type"]: # slik at orgnr_f vil vise farge i bedriftstabellen om ei bedrift har skifta foretak
                    col_def.update({
                        "cellStyle": {"function": "MacroModule.displayDiffHighlight(params)"}
                    })
                
                column_defs.append(col_def)

            if column_defs:
                column_defs[0]["pinned"] = "left" # pin first column when scrolling horizontally
                column_defs[0]["width"] = 240

            title = f"Bedrifter i næring {selected_nace} i {macro_level} {selected_filter_val}"
            if macro_level == "sammensatte variabler":
                title = f"Bedrifter i næring {selected_nace}"

            return row_data, column_defs, title

        @callback(
            Output("macromodule-macro-variable", "disabled"),
            Input("macromodule-filter-velger", "value"),
        )

        def toggle_variabel_dropdown(macro_level):
            """
            Disables macro-variable if sammensatte variabler is selected by user
            """
            return macro_level == "sammensatte variabler"

        # @callback(  # type: ignore[misc]
        #     Output("var-ident", "value", allow_duplicate=True),
        #     Output("var-foretak", "value"),
        #     Output("var-bedrift", "value"),
        #     Input("macromodule-detail-grid", "clickData"),
        #     prevent_initial_call=True,
        # )
        # def output_to_variabelvelger(clickdata: dict[str, list[dict[str, Any]]]) -> str:
        #     logger.debug(clickdata)
        #     if clickdata:
        #         logger.debug(clickdata)
        #         # do it so it returns the ident, of foretak as var-foretak and var-bedrift if bedrift is clicked. if foretak is clicked then set var-foretak == ident.
        #         ident = clickdata["points"][0]["customdata"][0]
        #         return str(ident)
        #         if col == "orgnr_f":
        #             return ident, foretak, ""
        #         elif col == "orgnr_b":
        #             return ident, orgnr_f["verdi"], bedrift
        #     else:
        #         raise PreventUpdate


class MacroModuleTab(TabImplementation, MacroModule):
    """MacroModuleTab is an implementation of the MacroModule module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroModuleTab class."""
        MacroModule.__init__(self, time_units=time_units, conn=conn, base_path=base_path)
        TabImplementation.__init__(self)


class MacroModuleWindow(WindowImplementation, MacroModule):
    """MacroModuleWindow is an implementation of the MacroModule module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object, base_path: str) -> None:
        """Initializes the MacroModuleWindow class."""
        MacroModule.__init__(self, time_units=time_units, conn=conn, base_path=base_path)
        WindowImplementation.__init__(self)