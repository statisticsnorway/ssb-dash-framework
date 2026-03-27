from pandas.core.frame import DataFrame


import logging
from collections.abc import Hashable
from typing import Any
from typing import ClassVar
from typing import Literal
from typing import Callable

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
from klass import KlassClassification
from datetime import date

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

ibis.options.interactive = True
logger = logging.getLogger(__name__)


def get_nace_values_from_group(aar: int, klass_gruppekode: str, sn2007: bool = False) -> dict[str, str]:
    """
    Uses Klass to get the current letter codes and NACE values in said group.
    Setting sn2007 to True forces the code to pick up the SN2007-Klass version instead. This param can be used when comparing SN2007 to SN2025.

    Example usage: 
        get_nace_values_from_group(2024, "G")
    Output: 
        {'G': ['45', '46', '47']}
    """
    if sn2007:
        aar = 2023
    standard_for_naeringsgruppering = KlassClassification(6)
    df = standard_for_naeringsgruppering.get_codes(
        f"{aar}-12-31"
    ).data

    # Get group and naringskoder for specified group
    df = df[df["level"].isin(["2"])][["code", "parentCode"]]
    df = df[df["parentCode"]==klass_gruppekode]

    # Create a dictionary with "group": ["codes"]
    strukt_naering_gruppekoder = {}
    for row in range(len(df)):
        gruppe, naring = df.parentCode.iloc[row], df.code.iloc[row]
        if gruppe not in strukt_naering_gruppekoder:
            strukt_naering_gruppekoder[gruppe] = [naring]
        else:
            strukt_naering_gruppekoder[gruppe].append(naring)
    return strukt_naering_gruppekoder


def get_nace_groups(aar: int) -> list[str]:
    """
    Uses Klass to get the existing letter codes in 'Standard for næringsgruppering' for specified year.
    """
    standard_for_naeringsgruppering = KlassClassification(6)
    df: DataFrame = standard_for_naeringsgruppering.get_codes(
        f"{aar}-12-31"
    ).data

    # Get group and naringskoder
    df = df[df["level"].isin(["2"])][["code", "parentCode"]]
    return df["parentCode"].unique().tolist()


DETAIL_GRID_ID_COLS = {
    "navn": "navn",
    "orgnr_foretak": "orgnr_f",
    "orgnr_bedrift": "orgnr_b",
    "naring": "naring",
    "naring_f": "naring_f",
    "reg_type": "reg_type",
    "reg_type_f": "reg_type_f",
    "type": "type",
}

FORETAK_OR_BEDRIFT: dict[str, str] = {"Foretak": "foretak", "Bedrifter": "bedrifter"}

NACE_LEVEL_OPTIONS: dict[str, int] = {
    "2-siffer": 2,
    "3-siffer": 4,
    "4-siffer": 5,
    "5-siffer": 6,
}
HEATMAP_NUMBER_FORMAT: dict[str, int] = {
    "Prosentendring": 1,
    "Årets totalsum": 2,
    "Differanse": 3,
}


class MacroModule_ParquetReader:
    """Helper class for reading and querying Parquet files with ibis."""

    def __init__(self) -> None:
        """Initialize a persistent DuckDB connection."""
        self.conn: BaseBackend = ibis.connect("duckdb://")

    def _load_year(
        self,
        aar: int,
        file_path_resolver: Callable[[int, str], str],
        foretak_or_bedrift: str,
        nace_list: list[str],
        nace_siffer_level: int,
        detail_grid: bool = False,
    ) -> Table:
        """Used to read parquet files, picking between foretak or bedrift level. Then filtering on chosen naring, and setting "aar" to a str column.

        Can be used for both the heatmap-grid and the detail-grid. If used for the prior, only filters on the first 2 naring digits (like "45", "88"), whereas for the latter it selects at specified nace_siffer_level.
        """
        file_path = file_path_resolver(aar, foretak_or_bedrift)

        letter_groups: set[str] = {n for n in nace_list if not n[0].isdigit()}
        print(letter_groups)
        only_nace_codes: set[str] = {n.split(".")[0][:2] for n in nace_list if n[0].isdigit()}
        print(only_nace_codes)

        # plan
        # if letter_groups, use the function get_nace_values_from_group for each letter to fetch a list of nace values
        # then make a dict of that like "G": ["45", "46", "47"]
        # and add the letter codes to only_nace_codes if it doesn't already have them (a set?)
        # then read in data for those nærings

        # check the data output for this
        # make a loop for each letter:
        # use the dict to copy rows from the specified nærings, and rename the copied rows' naring value to the letter name
        # the result should be all the necessary data, with the naring column containing both G, and 45, 46 etc

        # [x] in the heatmap and detail grid: letter shouldn't be affected by nace_level
        # [x] if someone clicks a letter code, we could just set the nace_siffer_level to 5?

        # [x] for the detail grid, when it's a letter, if nace_list = a letter, use get_nace_values_from_group to update nace_list

        try:
            t: ibis.TableExpr = self.conn.read_parquet(file_path)
        except Exception as e:
            print(
                f"Failed to read parquet file at {file_path}: {e}. "
                "Did you put in a valid year into the variabelvelger?"
            )
            raise PreventUpdate from None

        if detail_grid:
            if nace_list:
                if letter_groups:
                    klass_group: str = nace_list[0]
                    group_and_nace_values = get_nace_values_from_group(aar, klass_group)
                    t = t.filter(
                        t.naring.substr(0, length=2).isin(group_and_nace_values.get(klass_group))
                    )
                else:
                    t = t.filter(
                        t.naring.substr(0, length=nace_siffer_level).isin(nace_list)
                    )

        else:
            if letter_groups:
                # regular nace values
                t_only_nace = t.filter(t.naring.substr(0, length=2).isin(only_nace_codes))

                klass_dataframes = []
                group_nace_values = set()
                for letter in letter_groups:
                    nace_group = get_nace_values_from_group(aar, letter)
                    nace_values: list[str] | None = nace_group.get(letter)
                    assert nace_values is not None
                    group_nace_values.update(nace_values)

                    # rename these per letter to the letter name
                    t_klass = t.filter(t.naring.substr(0, length=2).isin(group_nace_values))
                    # set naring = letter
                    t_klass = t_klass.mutate(naring=ibis.literal(letter).cast("string"))

                    # add df to klass_dataframes
                    klass_dataframes.append(t_klass)

                # merge/join klass_dataframes with t_only_nace
                t_unioned = ibis.union(t_only_nace, *klass_dataframes)
                t_unioned = t_unioned.mutate(selected_nace=t_unioned.naring.substr(0, length=nace_siffer_level))
                return t_unioned.mutate(aar=ibis.literal(aar).cast("string"))

            else:
                t = t.filter(t.naring.substr(0, length=2).isin(only_nace_codes))
                t = t.mutate(selected_nace=t.naring.substr(0, length=nace_siffer_level))

        return t.mutate(aar=ibis.literal(aar).cast("string"))


class MacroModule:
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
            "foretak",
            "bedrift",
            "valgt_tabell",
            "altinnskjema",
        ]
    )

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        heatmap_variables: dict[str, str],
        file_path_resolver: Callable[[int, str], str],
        consolidated: bool = False,
    ) -> None:
        """Initializes the MacroModule.

        The MacroModule allows viewing macro values and getting micro-level views for selected fields.
        The base_path is used by load_year to locate parquet files.

        Args:
            time_units: Your time variables used in the variable selector. Example year, quarter, month, etc.
            conn: A connection object to a database (kept for compatibility, but DuckDB is used internally).
                Currently designed with parquet files in GC in mind.
            base_path: Base path to parquet files
                (e.g., "/buckets/produkt/naringer/klargjorte-data/statistikkfiler").
        """

        if time_units != ["aar"]:
            raise ValueError(
                f"The macro module currently only accepts time-units as aar! 'time-units' must be ['aar'], got: {time_units}"
            )

        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        # TODO: Add functionality for EimerDB
        # if not isinstance(conn, EimerDBInstance) and conn.__class__.__name__ != "Backend":
        #     raise TypeError("Argument 'conn' must be an 'EimerDBInstance' or Ibis backend. Received: {type(conn)}")

        self.module_number = MacroModule._id_number
        self.module_name = self.__class__.__name__
        MacroModule._id_number += 1

        self.icon = "🌍"
        self.consolidated = consolidated
        self.label = "Makromodul konsolidert" if consolidated else "Makromodul"
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        logger.debug("TIME UNITS ", self.time_units)

        self.conn = conn
        self.file_path_resolver = file_path_resolver
        self.parquet_reader = MacroModule_ParquetReader()
        self.heatmap_variables = heatmap_variables

        self.macro_filter_options: dict[str, Any] = {
            "fylke": 2,
            "kommune": 4,
            "sammensatte variabler": heatmap_variables,
        }
        self.detail_grid_id_cols_ordered = [
            "navn",
            *(["sfnr"] if consolidated else []),
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

        self.status_change_detail_grid: list[str] = [
            *(["sfnr"] if consolidated else []),
            "orgnr_f",
            "navn",
            "naring_f",
            "naring_b",
            "type",
            "reg_type_f",
            "reg_type_b",
            "kommune_f",
            "kommune_b",
        ]  # gets tooltip + colour change per year if changed (should be categorical col)

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
                                        *(
                                            [html.Br(), "konsoliderte,"]
                                            if self.consolidated
                                            else []
                                        ),
                                        html.Br(),
                                        "næringsendringer",
                                    ],
                                ),
                                html.Label(
                                    "Velg foretak eller bedrift",
                                    className="macromodule-label",
                                ),
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
                                        {"label": k, "value": k}
                                        for k in self.macro_filter_options.keys()
                                    ],
                                    value="sammensatte variabler",
                                    id="macromodule-filter-velger",
                                ),
                                html.Label(
                                    "Velg variabel",
                                    className="macromodule-label",
                                ),
                                dcc.Dropdown(
                                    className="macromodule-dropdown",
                                    options=[
                                        {
                                            "label": self.heatmap_variables.get(v, v),
                                            "value": v,
                                        }
                                        for v in self.heatmap_variables
                                    ],
                                    value=list(self.heatmap_variables.keys())[0],
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
                                    value=NACE_LEVEL_OPTIONS["2-siffer"],
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
                        html.H5(id="macromodule-detail-grid-title"),
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

    def _get_nace_options(
        self, file_path_resolver: Callable[[int, str], str], aar: str
    ) -> list[str]:
        """Get distinct NACE codes for a given year."""
        file_path = file_path_resolver(int(aar), "bedrifter")
        t: ibis.TableExpr = self.parquet_reader.conn.read_parquet(file_path).select(
            "naring"
        )
        naring_filter = t.naring.substr(0, length=2).name("nace2")
        t = t.select(naring_filter).distinct()
        df: DataFrame = t.to_pandas()
        nace_numbers: list[str] = sorted(df["nace2"].astype(str))
        nace_groups: list[str] = list(get_nace_groups(int(aar)))
        return [*nace_numbers, *nace_groups]

    def module_callbacks(self) -> None:
        """Defines the callbacks for the MacroModule module."""
        # dynamic_states = self.variableselector.get_all_inputs()

        @callback(
            Output("macromodule-naring-velger", "options"),
            Input("var-aar", "value"),
        )
        def update_nace_options(aar: str) -> list[str] | list[dict[str, str]]:
            """Populate NACE dropdown with options from selected year."""
            if not aar:
                return []
            try:
                nace_options = self._get_nace_options(self.file_path_resolver, aar)
                return [{"label": n, "value": n} for n in nace_options]
            except Exception as e:
                logger.error(f"Error loading NACE options: {e}")
                return []

        @callback(
            Output("macromodule-heatmap-grid", "rowData"),
            Output("macromodule-heatmap-grid", "columnDefs"),
            Output("macromodule-heatmap-grid", "pinnedTopRowData"),
            Input("var-aar", "value"),
            Input("macromodule-foretak-or-bedrift", "value"),
            Input("macromodule-macro-variable", "value"),
            Input("macromodule-filter-velger", "value"),
            Input("macromodule-nace-siffer-velger", "value"),
            Input("macromodule-naring-velger", "value"),
            Input("macromodule-tall-visning-velger", "value"),
            allow_duplicate=True,
        )
        def update_graph(
            variabelvelger_aar: str,
            foretak_or_bedrift: str,
            variabel: str,
            macro_level: str | None,
            nace_siffer_level: int,
            nace_list: list[str],
            tallvisning_valg: int,
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
            """Creates a colour-coordinated matrix heatmap of aggregated values based on their %-change from the previous year."""
            if (
                not nace_list
                or not variabel
                or not macro_level
                or not variabelvelger_aar
            ):
                return [], [], []

            if not isinstance(variabelvelger_aar, str):
                raise TypeError(
                    f"'var-aar' must be str, got: {type(variabelvelger_aar)}"
                )

            aar: int = int(variabelvelger_aar)

            t: ibis.TableExpr = self.parquet_reader._load_year(
                aar,
                self.file_path_resolver,
                foretak_or_bedrift,
                nace_list,
                nace_siffer_level,
                detail_grid=False,
            )  # t, current aar
            t_1: ibis.TableExpr = self.parquet_reader._load_year(
                aar - 1,
                self.file_path_resolver,
                foretak_or_bedrift,
                nace_list,
                nace_siffer_level,
                detail_grid=False,
            )  # t-1, previous aar

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

            if macro_level == "sammensatte variabler":
                cols = [*list(self.heatmap_variables.keys()), "naring", "aar"]
                group_by_filter = ["selected_nace"]

            else:
                cols = [variabel, macro_level, "naring", "aar"]
                group_by_filter = [
                    "selected_nace",
                    macro_level,
                ]  # kommune, fylke eller sammensatte_variabler
                col_length: int = self.macro_filter_options[macro_level]

                t = t.mutate(
                    **{
                        macro_level: t.kommune.substr(0, length=col_length)
                        .fill_null("UKJENT")
                        .replace("", "UKJENT")
                    }
                )
                t_1 = t_1.mutate(
                    **{
                        macro_level: t_1.kommune.substr(0, length=col_length)
                        .fill_null("UKJENT")
                        .replace("", "UKJENT")
                    }
                )

            t = t.select([*cols, "selected_nace"])
            t_1 = t_1.select([*cols, "selected_nace"])

            # cast numerics to float in case of yearly type mismatches
            for col in self.heatmap_variables.keys():
                if col in t.columns:
                    t = t.mutate(**{col: t[col].cast("float64")})
                if col in t_1.columns:
                    t_1 = t_1.mutate(**{col: t_1[col].cast("float64")})

            combined = t.union(t_1)

            if macro_level == "sammensatte variabler":
                agg_dict = {
                    alias: combined[db_col].sum()
                    for db_col, alias in self.heatmap_variables.items()
                }
                df = combined.group_by(["aar", *group_by_filter]).aggregate(**agg_dict)
                df = df.pivot_longer(
                    self.heatmap_variables.values(),
                    names_to="variabel",
                    values_to="value",
                )
                values_col = "value"
                category_column = "variabel"
            else:
                df = combined.group_by(["aar", *group_by_filter]).aggregate(
                    variabel=combined[variabel].sum()
                )
                values_col = "variabel"
                category_column = macro_level

            df = df.pivot_wider(names_from="aar", values_from=values_col)

            df = df.rename(nace="selected_nace").execute()
            df.columns = df.columns.astype(str)  # set to str in case aar loaded as int

            df["diff"] = df[f"{aar}"] - df[f"{aar-1}"]
            df["differanse"] = df[f"{aar}"].fillna(0) - df[f"{aar-1}"].fillna(0)
            df["percent_diff"] = df["diff"] / abs(df[f"{aar-1}"])
            if tallvisning_valg == 1:
                tallvisning = "percent_diff"
            elif tallvisning_valg == 2:
                tallvisning = f"{aar}"
            else:
                tallvisning = "differanse"

            matrix = df.pivot(
                index=category_column, columns="nace", values=tallvisning
            ).reset_index()
            matrix[category_column] = matrix[category_column].fillna("UKJENT")
            matrix.iloc[:, 1:] = matrix.iloc[:, 1:].fillna(0)

            # decide order of variables
            if category_column == "variabel":
                custom_order = list(self.heatmap_variables.values())
                matrix = matrix.set_index("variabel").loc[custom_order].reset_index()

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

            def _generate_tooltips(
                row_data: list[dict[str, Any]],
                df: pd.DataFrame,
                category_column: str,
                safe_cols: list[str],
                aar: int,
            ) -> None:
                """Create tooltips showing the raw data from each year and the diff, so the user can see both the %-diff in the cell and also the raw data when hovering."""
                for row in row_data:
                    if row.get("id") == "count_row":
                        continue

                    for col in safe_cols:
                        if col not in ["id", category_column]:
                            prev_year: pd.Series | Any = df.loc[
                                (df[category_column] == row[category_column])
                                & (df["nace"] == col.replace("_", ".")),
                                f"{aar-1}",
                            ]
                            current_year: pd.Series | Any = df.loc[
                                (df[category_column] == row[category_column])
                                & (df["nace"] == col.replace("_", ".")),
                                f"{aar}",
                            ]
                            val1: float = (
                                prev_year.values[0] if not prev_year.empty else 0
                            )
                            val2: float = (
                                current_year.values[0] if not current_year.empty else 0
                            )
                            diff: float | int = val2 - val1
                            tooltip: str = (
                                f"{aar}: {val2:,.0f}\n{aar-1}: {val1:,.0f}\nDiff: {diff:+,.0f}"
                            )
                            row[f"{col}_tooltip"] = tooltip

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

                        formatter_func = f"MacroModule.formatHeatmapValue(params, {tallvisning_valg})"

                        style_func = (
                            "MacroModule.displayDiffHeatMap(params)"
                            if tallvisning_valg == 1
                            else "MacroModule.displaySimpleHeatMap(params)"
                        )

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
                    col_defs[0]["width"] = 180 if category_column == "variabel" else 130

                return col_defs

            _generate_tooltips(row_data, df, category_column, safe_cols, aar)
            column_defs = _create_column_defs(original_cols, safe_cols, category_column)

            return row_data, column_defs, [count_row]

        @callback(
            Output("macromodule-detail-grid", "rowData"),
            Output("macromodule-detail-grid", "columnDefs"),
            Output("macromodule-detail-grid-title", "children"),
            Output("macromodule-detail-grid", "columnState"),
            Output("macromodule-detail-grid", "resetColumnState"),
            Output("macromodule-detail-grid", "filterModel"),
            Output("macromodule-detail-grid", "paginationGoTo"),
            Input("macromodule-heatmap-grid", "cellClicked"),
            State("var-aar", "value"),
            State("macromodule-foretak-or-bedrift", "value"),
            State("macromodule-heatmap-grid", "rowData"),
            State("macromodule-filter-velger", "value"),
            State("macromodule-nace-siffer-velger", "value"),
            State("macromodule-macro-variable", "value"),
            prevent_initial_call=True,
        )
        def update_detail_table(
            cell_data: dict[str, Any] | None,
            variabelvelger_aar: str,
            foretak_or_bedrift: str,
            heatmap_row_data: list[dict[str, Any]],
            macro_level: str | None,
            nace_siffer_level: int,
            heatmap_valgt_variabel: str,
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

            aar: int = int(variabelvelger_aar)
            valgt_variabel = self.heatmap_variables.get(heatmap_valgt_variabel, "")

            col = cell_data.get("colId")
            if col in ["variabel", macro_level]:
                raise PreventUpdate

            assert isinstance(col, str)
            if col[0].isdigit():
                nace_letter_code = False
                selected_nace = col.replace("_", ".")
            else:
                nace_letter_code = True
                selected_nace = col
                nace_siffer_level = 2
            row_idx = int(row_id)

            if not selected_nace:
                raise PreventUpdate

            if macro_level == "sammensatte variabler":
                selected_filter_val: Any | None = heatmap_row_data[row_idx].get(
                    "variabel"
                )
                valgt_variabel: str | None = selected_filter_val
            else:
                assert macro_level is not None
                selected_filter_val = heatmap_row_data[row_idx].get(macro_level)

            if selected_filter_val is None or pd.isna(selected_filter_val):
                raise PreventUpdate

            # read in every unit in selected nace
            t_curr_filtered: ibis.TableExpr = self.parquet_reader._load_year(
                aar,
                self.file_path_resolver,
                foretak_or_bedrift,
                [selected_nace],
                nace_siffer_level,
                detail_grid=True,
            )
            t_prev_filtered: ibis.TableExpr = self.parquet_reader._load_year(
                aar - 1,
                self.file_path_resolver,
                foretak_or_bedrift,
                [selected_nace],
                nace_siffer_level,
                detail_grid=True,
            )

            # handle kommune/fylke filters
            if macro_level != "sammensatte variabler":

                assert isinstance(macro_level, str)

                col_length: int = self.macro_filter_options[macro_level]
                t_curr_filtered = t_curr_filtered.mutate(
                    **{
                        macro_level: t_curr_filtered.kommune.substr(
                            0, length=col_length
                        )
                        .fill_null("UKJENT")
                        .replace("", "UKJENT")
                    }
                )
                t_prev_filtered = t_prev_filtered.mutate(
                    **{
                        macro_level: t_prev_filtered.kommune.substr(
                            0, length=col_length
                        )
                        .fill_null("UKJENT")
                        .replace("", "UKJENT")
                    }
                )

                t_curr_filtered = t_curr_filtered.filter(
                    t_curr_filtered[macro_level] == selected_filter_val
                )
                t_prev_filtered = t_prev_filtered.filter(
                    t_prev_filtered[macro_level] == selected_filter_val
                )

            # collect all unique units (orgnr_foretak) from both years
            units_curr = t_curr_filtered.select("orgnr_foretak").distinct()
            units_prev = t_prev_filtered.select("orgnr_foretak").distinct()
            units_all = units_curr.union(units_prev).distinct()

            # reload ALL data (no nace/macro filters) for those units
            t: ibis.TableExpr = self.parquet_reader._load_year(
                aar,
                self.file_path_resolver,
                foretak_or_bedrift,
                [],  # no nace filter
                nace_siffer_level,
                detail_grid=True,
            )
            t_1: ibis.TableExpr = self.parquet_reader._load_year(
                aar - 1,
                self.file_path_resolver,
                foretak_or_bedrift,
                [],  # no nace filter
                nace_siffer_level,
                detail_grid=True,
            )

            # filter to only the units we identified
            t = t.semi_join(units_all, ["orgnr_foretak"])
            t_1 = t_1.semi_join(units_all, ["orgnr_foretak"])

            select_cols = [
                "navn",
                *(["sfnr"] if self.consolidated else []),
                "orgnr_foretak",
                *(["orgnr_bedrift"] if foretak_or_bedrift == "bedrifter" else []),
                "naring",
                "naring_f",
                "reg_type",
                "reg_type_f",
                "type",
                "kommune",
                *self.heatmap_variables.keys(),
                "giver_fnr",
                "giver_bnr",
                "aar",
            ]

            t = t.select([c for c in select_cols if c in t.columns])
            t_1 = t_1.select([c for c in select_cols if c in t_1.columns])

            if foretak_or_bedrift == "foretak":
                rename_mapping = {
                    "naring_f": "naring",
                    "reg_type_f": "reg_type",
                    "orgnr_f": "orgnr_foretak",
                    "kommune_f": "kommune",
                }
                kommune_col = "kommune_f"
                naring_col = "naring_f"
                merge_keys = "orgnr_f"
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
                merge_keys = ["orgnr_f", "orgnr_b"]

            t = t.rename(**rename_mapping)
            t_1 = t_1.rename(**rename_mapping)

            for col in self.heatmap_variables.keys():
                if col in t.columns:
                    t = t.mutate(**{col: t[col].cast("float64")})
                if col in t_1.columns:
                    t_1 = t_1.mutate(**{col: t_1[col].cast("float64")})

            t_curr = t.filter(t.aar == str(aar))
            t_prev = t_1.filter(t_1.aar == str(aar - 1))

            t_curr = t_curr.rename(
                {v: k for k, v in self.heatmap_variables.items() if k in t_curr.columns}
            ).execute()
            t_prev = t_prev.rename(
                {v: k for k, v in self.heatmap_variables.items() if k in t_prev.columns}
            ).execute()

            # use outer to catch units that may only exist in one year due to orgnr_bedrift changes
            merged_df = t_curr.merge(
                t_prev,
                how="outer",
                on=merge_keys,
                suffixes=("", "_x"),
                indicator=True,
            )

            merged_df[kommune_col] = (
                merged_df[kommune_col].fillna("UKJENT").replace("", "UKJENT")
            )
            merged_df[f"{kommune_col}_x"] = (
                merged_df[f"{kommune_col}_x"].fillna("UKJENT").replace("", "UKJENT")
            )

            merged_df["is_new"] = merged_df["_merge"] == "left_only"
            merged_df["is_exiter"] = merged_df["_merge"] == "right_only"

            # for exiters, fill in key identifying columns from previous year
            if "navn" in merged_df.columns and "navn_x" in merged_df.columns:
                merged_df["navn"] = merged_df["navn"].fillna(merged_df["navn_x"])
            if (
                self.consolidated
                and "sfnr" in merged_df.columns
                and "sfnr_x" in merged_df.columns
            ):
                merged_df["sfnr"] = merged_df["sfnr"].fillna(merged_df["sfnr_x"])
            merged_df = merged_df.drop(columns=["_merge"])

            # 2-siffer nace changes?
            if (
                naring_col in merged_df.columns
                and f"{naring_col}_x" in merged_df.columns
            ):
                merged_df["nace_prefix_curr"] = (
                    merged_df[naring_col].astype(str).str[:nace_siffer_level]
                )
                merged_df["nace_prefix_prev"] = (
                    merged_df[f"{naring_col}_x"].astype(str).str[:nace_siffer_level]
                )

                merged_df["is_nace_entrant"] = (  # different nace LAST year
                    ~merged_df["is_new"]
                    & (merged_df["nace_prefix_curr"] == selected_nace)
                    & (merged_df["nace_prefix_prev"] != selected_nace)
                )

                merged_df["is_nace_exiter"] = (  # different nace THIS year
                    ~merged_df["is_exiter"]
                    & (merged_df["nace_prefix_prev"] == selected_nace)
                    & (merged_df["nace_prefix_curr"] != selected_nace)
                )

                merged_df["nace_same"] = (
                    merged_df["nace_prefix_curr"] == merged_df["nace_prefix_prev"]
                ).fillna(False)

                # drop rows/units if it wasn't in bucket this or last year, necessary because of merging on orgnr_foretak
                mask = (merged_df["nace_prefix_curr"] == selected_nace) | (
                    merged_df["nace_prefix_prev"] == selected_nace
                )
                merged_df = merged_df[mask]

            # kommune/fylke change flags
            if macro_level in ("fylke", "kommune"):

                if (
                    kommune_col in merged_df.columns
                    and f"{kommune_col}_x" in merged_df.columns
                ):
                    merged_df["macro_prefix_curr"] = merged_df[kommune_col].where(
                        merged_df[kommune_col] == "UKJENT",
                        merged_df[kommune_col].astype(str).str[:col_length],
                    )
                    merged_df["macro_prefix_prev"] = merged_df[
                        f"{kommune_col}_x"
                    ].where(
                        merged_df[f"{kommune_col}_x"] == "UKJENT",
                        merged_df[f"{kommune_col}_x"].astype(str).str[:col_length],
                    )

                    merged_df["in_bucket_curr"] = (
                        merged_df["macro_prefix_curr"] == selected_filter_val
                    ).fillna(False)
                    merged_df["in_bucket_prev"] = (
                        merged_df["macro_prefix_prev"] == selected_filter_val
                    ).fillna(False)

                    # drop rows/units if it wasn't in bucket this or last year, necessary because of excess bedrifter when merging on orgnr_foretak
                    mask = merged_df["in_bucket_curr"] | merged_df["in_bucket_prev"]
                    merged_df = merged_df[mask]

                    merged_df["is_macro_entrant"] = (
                        ~merged_df["is_new"]
                        & merged_df["in_bucket_curr"]
                        & ~merged_df["in_bucket_prev"]
                    )
                    merged_df["is_macro_exiter"] = (
                        ~merged_df["is_exiter"]
                        & merged_df["in_bucket_prev"]
                        & ~merged_df["in_bucket_curr"]
                    )
            else:
                merged_df["in_bucket_curr"] = True
                merged_df["in_bucket_prev"] = True
                merged_df["is_macro_entrant"] = False
                merged_df["is_macro_exiter"] = False

            df = merged_df.copy()

            if (
                "giver_bnr" in df.columns and "giver_fnr" in df.columns
            ):  # unngå foretakstabellar som ikkje har giver
                df["giver_fnr_tooltip"] = "Giverforetak: " + df["giver_fnr"].astype(str)
                df["giver_bnr_tooltip"] = "Giverbedrifter: " + df["giver_bnr"].astype(
                    str
                )
            for col in self.status_change_detail_grid:
                if f"{col}_x" in df.columns:
                    df[f"{col}_tooltip"] = "Fjorårets verdi: " + df[f"{col}_x"].astype(
                        str
                    )

            # adjust values for current and previous contributors and then calculate diff accordingly
            if valgt_variabel in df.columns and f"{valgt_variabel}_x" in df.columns:

                current_contributes = (
                    ~df["is_exiter"]
                    & df["in_bucket_curr"]
                    & (df["nace_prefix_curr"] == selected_nace)
                )

                prev_contributes = (
                    ~df["is_new"]
                    & df["in_bucket_prev"]
                    & (df["nace_prefix_prev"] == selected_nace)
                )

                current_value_adjusted = (
                    df[valgt_variabel].where(current_contributes, other=0).fillna(0)
                )
                prev_value_adjusted = (
                    df[f"{valgt_variabel}_x"].where(prev_contributes, other=0).fillna(0)
                )

                df[f"{valgt_variabel}_diff"] = (
                    current_value_adjusted - prev_value_adjusted
                )

                df["is_tilgang"] = current_contributes & ~prev_contributes
                df["is_avgang"] = ~current_contributes & prev_contributes

                heatmap_value_change = cell_data.get("value", 0)
                heatmap_value_change = (
                    float(heatmap_value_change)
                    if heatmap_value_change is not None
                    else 0
                )
                ascending_sorting_param: bool = heatmap_value_change < 0
                df = df.sort_values(
                    f"{valgt_variabel}_diff", ascending=ascending_sorting_param
                )

            # order for columns
            if valgt_variabel in df.columns:
                metrics_order = [valgt_variabel]
            else:
                metrics_order = []
            metrics_order += [
                self.heatmap_variables.get(v, v)
                for v in self.heatmap_variables
                if self.heatmap_variables.get(v, v) != valgt_variabel
            ]

            ordered_value_cols = []
            diff_col = f"{valgt_variabel}_diff"
            for metric in metrics_order:
                current_year_col = metric
                previous_year_col = f"{metric}_x"

                if current_year_col in df.columns:
                    ordered_value_cols.append(current_year_col)
                if previous_year_col in df.columns:
                    ordered_value_cols.append(previous_year_col)

                if metric == valgt_variabel and diff_col in df.columns:
                    ordered_value_cols.append(diff_col)

            visible_cols = [
                c
                for c in [*self.detail_grid_id_cols_ordered, *ordered_value_cols]
                if c in df.columns
            ]

            if self.consolidated:
                df = df.astype(object)
                df = df.map(
                    lambda x: x.decode("latin-1") if isinstance(x, bytes) else x
                )

            row_data: list[dict[Hashable, Any]] | Any = df.to_dict("records")
            if macro_level in ("fylke", "kommune"):
                for row in row_data:
                    row["macro_len"] = self.macro_filter_options[
                        macro_level
                    ]  # for frontend JavaScript

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

                if col not in self.detail_grid_id_cols_ordered:
                    col_def["valueFormatter"] = {
                        "function": "MacroModule.formatDetailGridValue(params)"
                    }
                    if col.endswith("_x"):
                        col_def["cellStyle"] = {
                            "backgroundColor": "#e8e9eb"  # light grey for previous year
                        }

                if col in self.status_change_detail_grid:
                    col_def.update(
                        {
                            "cellStyle": {
                                "function": "MacroModule.displayDiffHighlight(params)"
                            }
                        }
                    )

                if col.endswith("_diff") or col in ("orgnr_b", "navn"):
                    col_def["cellStyle"] = {
                        "function": "MacroModule.displayDiffColumnHighlight(params)"
                    }

                if df[col].dtypes == "float":
                    col_def["filter"] = "agNumberColumnFilter"

                column_defs.append(col_def)

            if column_defs:
                column_defs[0]["pinned"] = "left"
                column_defs[0]["width"] = 240
            
            if nace_letter_code:
                nace_definition = "næringsgruppe"
            else:
                nace_definition = "næring"
            title = f"{foretak_or_bedrift.capitalize()} i {nace_definition} {selected_nace} i {macro_level} {selected_filter_val}"
            if macro_level == "sammensatte variabler":
                title = f"{foretak_or_bedrift.capitalize()} i {nace_definition} {selected_nace}"

            return row_data, column_defs, title, [], True, None, 0

        @callback(
            Output("macromodule-detail-grid", "rowData", allow_duplicate=True),
            Output("macromodule-detail-grid", "columnDefs", allow_duplicate=True),
            Output("macromodule-detail-grid-title", "children", allow_duplicate=True),
            Input("var-aar", "value"),
            Input("macromodule-foretak-or-bedrift", "value"),
            Input("macromodule-filter-velger", "value"),
            Input("macromodule-nace-siffer-velger", "value"),
            Input("macromodule-naring-velger", "value"),
            Input("macromodule-macro-variable", "value"),
            prevent_initial_call=True,
        )
        def reset_detail_grid_on_filter_change(*args: Any) -> tuple[list, list, str]:
            """Reset detail grid when any filter changes."""
            return [], [], ""

        @callback(
            Output("macromodule-macro-variable", "disabled"),
            Input("macromodule-filter-velger", "value"),
        )
        def toggle_variabel_dropdown(macro_level: str) -> bool:
            """Disables macro-variable if sammensatte variabler is selected by user."""
            return macro_level == "sammensatte variabler"

        @callback(  # type: ignore[misc]
            Output("var-ident", "value", allow_duplicate=True),
            Output("var-bedrift", "value", allow_duplicate=True),
            Output("altinnedit-option1", "value", allow_duplicate=True),
            Input("macromodule-detail-grid", "cellClicked"),
            State("macromodule-detail-grid", "rowData"),
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


class MacroModuleTab(TabImplementation, MacroModule):
    """MacroModuleTab is an implementation of the MacroModule module as a tab in a Dash application."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        heatmap_variables: dict[str, str],
        file_path_resolver: Callable[[int, str], str],
        consolidated: bool,
    ) -> None:
        """Initializes the MacroModuleTab class."""
        MacroModule.__init__(
            self,
            time_units=time_units,
            conn=conn,
            heatmap_variables=heatmap_variables,
            file_path_resolver=file_path_resolver,
            consolidated=consolidated,
        )
        TabImplementation.__init__(self)


class MacroModuleWindow(WindowImplementation, MacroModule):
    """MacroModuleWindow is an implementation of the MacroModule module as a tab in a Dash application."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        heatmap_variables: dict[str, str],
        file_path_resolver: Callable[[int, str], str],
        consolidated: bool,
    ) -> None:
        """Initializes the MacroModuleWindow class."""
        MacroModule.__init__(
            self,
            time_units=time_units,
            conn=conn,
            heatmap_variables=heatmap_variables,
            file_path_resolver=file_path_resolver,
            consolidated=consolidated,
        )
        WindowImplementation.__init__(self)
