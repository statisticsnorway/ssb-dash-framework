from pandas.core.frame import DataFrame
import sqlite3
from dash_ag_grid import AgGrid
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime, date
import pandas as pd
import ibis
from ibis.backends import BaseBackend
import logging
from typing import Any
from typing import ClassVar
from typing import Literal
from ibis.expr.types.relations import Table
from pandas.core.frame import DataFrame
import os

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator
from ..modules.bofregistry import SSB_BEDRIFT_PATH, SSB_FORETAK_PATH
from ..utils import active_no_duplicates_refnr_list

ibis.options.interactive = True
logger = logging.getLogger(__name__)

SHOW_COLUMNS: dict[str, bool] = {"skjemadata": True, "skjemadata_fjor": True, "enhetsinfo": False, "enhetsinfo_fjor": False}

class Meldingsbasen:
    """
    
    """
    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the module_callbacks.
            "foretak",
        ]
    )

    def __init__(self, time_units: list[str], conn: object) -> None:
        """
        Explanation of module.
        """
        self.module_number = Meldingsbasen._id_number
        self.module_name = self.__class__.__name__
        Meldingsbasen._id_number += 1
        self.icon = "📒"
        self.label = "Meldingsbasen"

        self.conn = conn
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        logger.debug("TIME UNITS ", self.time_units)
        
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in Meldingsbasen._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"Meldingsbasen requires the variable selector option '{var}' to be set."
                ) from e


    def _create_layout(self):
        """
        Generates the layout for the meldingsbasen module.
        """
        layout = html.Div(
            children=[
                # buttons and options
                html.Div(
                    children=[
                        dcc.RadioItems(
                                    id="meldingsbasen-vis-kolonner",
                                    options=[
                                        {"label": "Skjemadata (i år)", "value": "skjemadata"},
                                        {"label": "Skjemadata (i fjor)", "value": "skjemadata_fjor"},
                                        {"label": "Enhetsinfo (i år)", "value": "enhetsinfo"},
                                        {"label": "Enhetsinfo (i fjor)", "value": "enhetsinfo_fjor"},
                                    ],
                                    value=["skjemadata", "skjemadata_fjor"],
                                ),
                    
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    dbc.Button(
                                        "Send oppdateringer",
                                        id="meldingsbasen-save-edits-button1",
                                    ),
                                    width="auto",
                                ),
                            ],
                        )
                    ]),
                # data grids
                html.Div(
                    # Dropdown with option as foretak, which if True shows a foretak AgGrid. Default True.
                    AgGrid(
                                    id="meldingsbasen-foretak-grid",
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
                ),

                html.Div(
                    # Dropdown with option as bedrift, which if True shows a foretak AgGrid. Default False
                    AgGrid(
                                    id="meldingsbasen-bedrift-grid",
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
                ),
            ],
        )

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Meldingsbasen module."""

        @callback(
            Output("meldingsbasen-foretak-grid", "rowData"),
            Output("meldingsbasen-foretak-grid", "columnDefs"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
            Input("meldingsbasen-vis-kolonner", "value")

        )
        def show_foretak_data(
            aar: str, 
            orgnr_foretak: str,
            vis_kolonner
            ):

            skjemadata      = "skjemadata"      in vis_kolonner
            skjemadata_fjor = "skjemadata_fjor" in vis_kolonner
            enhetsinfo      = "enhetsinfo"      in vis_kolonner
            enhetsinfo_fjor = "enhetsinfo_fjor" in vis_kolonner

            with sqlite3.connect(SSB_FORETAK_PATH) as conn:
                df = pd.read_sql_query(
                    f"SELECT * FROM ssb_foretak WHERE orgnr = '{orgnr_foretak}'", conn
                )

            if skjemadata:
                s = self.conn.table("core_skjemadata_mapped")
                s = (s
                    .filter(_.aar == aar)
                    .filter(_.ident == orgnr_foretak)
                    .filter(_.refnr.isin(active_no_duplicates_refnr_list(self.conn)))
                    .filter(_.variabel == "naeringskode")
                    .select(["ident", "refnr", "verdi"]).to_pandas()
                )
                s = s.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})
                print(s)

                df = df.merge(s, how="left", on="orgnr")
            
            if enhetsinfo:
                e = self.conn.table("enhetsinfo")
                e = (e
                    .filter(_.aar == aar)
                    .filter(_.ident == orgnr_foretak)
                    .filter(_.variabel == "nace_2007")
                    .select(["ident", "verdi"]).to_pandas()
                )
                e = e.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})
                print(e)

                df = df.merge(e, how="left", on="orgnr")

            orgnr = df["orgnr"][0]
            orgform = df["org_form"][0]
            navn = df["navn"][0]
            nace_07 = df["sn07_1"][0]
            nace_2025 = df["sn2025_1"][0]
            kilde = df["kilde"].astype(str)
            fritekst = df["fritekst"].astype(str)

            row_data = df.to_dict("records")
            column_defs = [
                {
                    "field": col, 
                    "headerName": col,
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    "editable": True,
                    
                }
                for col in df.columns
            ]

            return row_data, column_defs
        
        @callback(
            Output("meldingsbasen-bedrift-grid", "rowData"),
            Output("meldingsbasen-bedrift-grid", "columnDefs"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
            Input("var-bedrift", "value"),
            Input("meldingsbasen-vis-kolonner", "value")
        )
        def show_bedrift_data(
            aar: str, 
            orgnr_foretak: str,
            orgnr_bedrift: str,
            vis_kolonner,
            ):

            skjemadata      = "skjemadata"      in vis_kolonner
            skjemadata_fjor = "skjemadata_fjor" in vis_kolonner
            enhetsinfo      = "enhetsinfo"      in vis_kolonner
            enhetsinfo_fjor = "enhetsinfo_fjor" in vis_kolonner

            if orgnr_foretak is not None:
                with sqlite3.connect(SSB_BEDRIFT_PATH) as conn:
                    df = pd.read_sql_query(
                        f"""SELECT bedrifts_nr, orgnr, navn, sn07_1, sn2025_1, org_form
                        FROM ssb_bedrift WHERE foretaks_nr = '{orgnr_foretak}';""",
                        conn,
                    )

            if skjemadata:
                s = self.conn.table("core_skjemadata_mapped")
                s = (
                    s.filter(_.aar == aar)
                    .filter(_.ident != orgnr_foretak)
                    .filter(_.refnr == refnr) # fetch from table above
                    .filter(_.variabel == "virkNaeringskode")
                    .select(["ident", "verdi"]).to_pandas()
                )
                print(s)
                s = s.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})
                df = df.merge(s, how="left", on="orgnr")
                print(df)
            
            if enhetsinfo:
                e = self.conn.table("enhetsinfo")
                e = (e
                    .filter(_.aar == aar)
                    .filter(_.foretak == orgnr_foretak)
                    .filter(_.variabel == "nace_2007")
                    .select(["ident", "verdi"]).to_pandas()
                )
                print(e)
                e = e.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})

                df = df.merge(e, how="left", on="orgnr")
                print(df)

            df["kilde"] = df["kilde"].astype(str)
            df["fritekst"] = df["fritekst"].astype(str)

            if orgnr_bedrift != "":
                df = df.sort_values(
                        by="orgnr",
                        key=lambda x: x.map(lambda v: 0 if v == orgnr_bedrift else 1),
                    )
            
            row_data = df.to_dict("records")

            column_defs = [
                {
                    "field": col, 
                    "headerName": col,
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    "editable": True,
                    
                }
                for col in df.columns
            ]

            return row_data, column_defs


class MeldingsbasenTab(TabImplementation, Meldingsbasen):
    """MeldingsbasenTab is an implementation of the Meldingsbasen module as a tab in a Dash application."""
    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the MeldingsbasenTab class."""
        Meldingsbasen.__init__(
            self, time_units=time_units, conn=conn,
        )
        TabImplementation.__init__(self)


class MeldingsbasenWindow(WindowImplementation, Meldingsbasen):
    """MeldingsbasenWindow is an implementation of the Meldingsbasen module as a tab in a Dash application."""
    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the MeldingsbasenWindow class."""
        Meldingsbasen.__init__(
            self, time_units=time_units, conn=conn
        )
        WindowImplementation.__init__(self)