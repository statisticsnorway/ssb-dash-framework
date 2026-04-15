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
from ibis import _
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
SELECT_COLUMNS_FORETAK = ["foretaks_nr", "orgnr", "org_form", "navn", "sn07_1", "sn2025_1", "kilde", "fritekst"]
SELECT_COLUMNS_BEDRIFT  = ["orgnr", "org_form", "navn", "sn07_1", "sn2025_1", "kilde", "fritekst"]

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
            className="meldingsbasen",
            children=[
                # Top bar with button
                html.Div(
                    children=[
                        dbc.Button(
                            "Send oppdateringer",
                            id="meldingsbasen-save-edits-button1",
                            className="meldingsbasen-button-update",
                            # outline=True,
                            # color="primary",
                        ),
                    ],
                    className="d-grid gap-2 justify-content-md-end",
                ),
                # sidebar
                html.Div(
                    className="meldingsbasen-sidebar",
                    children=[
                        dbc.Checklist(
                            className="meldingsbasen-checklist",
                            id="meldingsbasen-checklist",
                            options=[
                                {"label": "Vis skjemadata",   "value": "skjemadata"},
                                {"label": "Vis enhetsinfo",   "value": "enhetsinfo"},
                            ],
                            value=["skjemadata", "enhetsinfo"],
                            switch=True,
                        ),
                    ]
                ),
                # grids
                html.Div(
                    className="meldingsbasen-container",
                    children=[
                        # Right: grids stacked vertically
                        html.Div(
                            className="meldingsbasen-grid-container",
                            children=[
                                dcc.Store(id="meldingsbasen-foretak-store"),
                                html.Div(
                                    className="meldingsbasen-foretak-grid-container",
                                    children=[
                                        html.Label("Foretak", className="meldingsbasen-label"),
                                        AgGrid(
                                            id="meldingsbasen-foretak-grid",
                                            getRowId="params.data.id",
                                            defaultColDef={"sortable": True, "filter": True, "resizable": True},
                                            columnSize="responsiveSizeToFit",
                                            rowData=[],
                                            columnDefs=[],
                                            dashGridOptions={"rowSelection": "single", "enableCellTextSelection": True},
                                            style={"height": "100%", "width": "100%"},
                                        )
                                    ]
                                ),
                                dcc.Store(id="meldingsbasen-bedrift-store"),
                                html.Div(
                                    className="meldingsbasen-bedrift-grid-container",
                                    children=[
                                        html.Label("Bedrifter", className="meldingsbasen-label"),
                                        AgGrid(
                                            id="meldingsbasen-bedrift-grid",
                                            getRowId="params.data.id",
                                            defaultColDef={"sortable": True, "filter": True, "resizable": True},
                                            columnSize="responsiveSizeToFit",
                                            rowData=[],
                                            columnDefs=[],
                                            dashGridOptions={"rowSelection": "single", "enableCellTextSelection": True},
                                            style={"height": "100%", "width": "100%"},
                                        )
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        )

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Meldingsbasen module."""

        # 1. Fetch and store foretak data - only fires on aar/orgnr change
        @callback(
            Output("meldingsbasen-foretak-store", "data"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
        )
        def fetch_foretak_data(aar, orgnr_foretak):
            if not aar or not orgnr_foretak:
                raise PreventUpdate

            with sqlite3.connect(SSB_FORETAK_PATH) as conn:
                df = pd.read_sql_query(
                    f"SELECT foretaks_nr, orgnr, navn, sn07_1, sn2025_1, org_form FROM ssb_foretak WHERE orgnr = '{orgnr_foretak}'", conn
                )

            s = self.conn.table("core_skjemadata_mapped")
            s = (s
                .filter(_.aar == aar)
                .filter(_.ident == orgnr_foretak)
                .filter(_.refnr.isin(active_no_duplicates_refnr_list(self.conn)))
                .filter(_.variabel == "naeringskode")
                .select(["ident", "refnr", "verdi"]).to_pandas()
            )
            s = s.rename(columns={"ident": "orgnr", "verdi": "naeringskode"})
            df = df.merge(s, how="left", on="orgnr")

            e = self.conn.table("enhetsinfo")
            e = (e
                .filter(_.aar == aar)
                .filter(_.ident == orgnr_foretak)
                .filter(_.variabel == "nace_2007")
                .select(["ident", "verdi"]).to_pandas()
            )
            e = e.rename(columns={"ident": "orgnr", "verdi": "nace_2007"})
            df = df.merge(e, how="left", on="orgnr")

            df["kilde"] = ""
            df["fritekst"] = ""
            if "sn07_1" not in df.columns:   df["sn07_1"] = None
            if "sn2025_1" not in df.columns: df["sn2025_1"] = None
            if "naeringskode" not in df.columns: df["naeringskode"] = None
            if "nace_2007" not in df.columns:    df["nace_2007"] = None

            df = df.reset_index().rename(columns={"index": "id"})
            return df.to_dict("records")


        # 2. Display foretak grid - fires on store change OR checklist change (no data fetching)
        @callback(
            Output("meldingsbasen-foretak-grid", "rowData"),
            Output("meldingsbasen-foretak-grid", "columnDefs"),
            Input("meldingsbasen-foretak-store", "data"),
            Input("meldingsbasen-checklist", "value"),
        )
        def show_foretak_grid(store_data, vis_kolonner):
            if not store_data:
                raise PreventUpdate

            skjemadata = "skjemadata" in vis_kolonner
            enhetsinfo  = "enhetsinfo"  in vis_kolonner

            df = pd.DataFrame(store_data)

            cols = SELECT_COLUMNS_FORETAK.copy()
            if skjemadata: cols.append("naeringskode")
            if enhetsinfo: cols.append("nace_2007")
            cols = [c for c in cols if c in df.columns]
            df = df[cols]

            bof_children = [
                {"field": "orgnr",    "headerName": "orgnr"},
                {"field": "org_form", "headerName": "org_form"},
                {"field": "navn",     "headerName": "navn"},
                {"field": "sn07_1",   "headerName": "sn07_1"},
                {"field": "sn2025_1", "headerName": "sn2025_1"},
                {"field": "kilde",    "headerName": "kilde",    "editable": True},
                {"field": "fritekst", "headerName": "fritekst", "editable": True},
            ]
            column_defs = [{"headerName": "BoF", "children": bof_children}]
            if skjemadata:
                column_defs.append({"headerName": "Altinn3",    "children": [{"field": "naeringskode",     "headerName": "naeringskode"}]})
            if enhetsinfo:
                column_defs.append({"headerName": "Enhetsinfo", "children": [{"field": "nace_2007", "headerName": "nace_2007"}]})

            return df.to_dict("records"), column_defs


        # 3. Fetch and store bedrift data - only fires on aar/orgnr change
        @callback(
            Output("meldingsbasen-bedrift-store", "data"),
            Input("meldingsbasen-foretak-store", "data"),
            State("var-aar", "value"),
            State("var-foretak", "value"),
            State("var-bedrift", "value"),
        )
        def fetch_bedrift_data(foretak_store, aar, orgnr_foretak, orgnr_bedrift):
            if not aar or not foretak_store:
                raise PreventUpdate

            refnr      = foretak_store[0].get("refnr", "")
            foretaks_nr = foretak_store[0].get("foretaks_nr", "")

            with sqlite3.connect(SSB_BEDRIFT_PATH) as conn:
                df = pd.read_sql_query(
                    f"""SELECT orgnr, navn, sn07_1, sn2025_1, org_form FROM ssb_bedrift WHERE foretaks_nr = '{foretaks_nr}';""",
                    conn,
                )
            print(f"bedrift df: {df.head()}")
            if refnr:
                s = self.conn.table("core_skjemadata_mapped")
                s = (s
                    .filter(_.aar == aar)
                    .filter(_.refnr == refnr)
                    .filter(_.variabel == "virkNaeringskode")
                    .select(["ident", "verdi"]).to_pandas()
                )
                s = s.rename(columns={"ident": "orgnr", "verdi": "virkNaeringskode"})
                print(f"bedrift s: {s}")
                df = df.merge(s, how="left", on="orgnr")

            print(f"bedrift after merge with skjemadata df: {df.head()}")

            e = self.conn.table("enhetsinfo")
            e = (e
                .filter(_.aar == aar)
                .filter(_.foretak == orgnr_foretak)
                .filter(_.variabel == "nace_2007")
                .select(["ident", "verdi"]).to_pandas()
            )
            e = e.rename(columns={"ident": "orgnr", "verdi": "nace_2007"})
            print(f"bedrift e: {e}")
            df = df.merge(e, how="left", on="orgnr")

            df["kilde"] = ""
            df["fritekst"] = ""
            if "sn07_1" not in df.columns:          df["sn07_1"] = None
            if "sn2025_1" not in df.columns:        df["sn2025_1"] = None
            if "virkNaeringskode" not in df.columns: df["virkNaeringskode"] = None
            if "nace_2007" not in df.columns:        df["nace_2007"] = None

            if orgnr_bedrift:
                df = df.sort_values(
                    by="orgnr",
                    key=lambda x: x.map(lambda v: 0 if v == orgnr_bedrift else 1),
                )

            df = df.reset_index().rename(columns={"index": "id"})
            return df.to_dict("records")


        # 4. Display bedrift grid - fires on store change OR checklist change (no data fetching)
        @callback(
            Output("meldingsbasen-bedrift-grid", "rowData"),
            Output("meldingsbasen-bedrift-grid", "columnDefs"),
            Input("meldingsbasen-bedrift-store", "data"),
            Input("meldingsbasen-checklist", "value"),
        )
        def show_bedrift_grid(store_data, vis_kolonner):
            if not store_data:
                raise PreventUpdate

            skjemadata = "skjemadata" in vis_kolonner
            enhetsinfo  = "enhetsinfo"  in vis_kolonner

            df = pd.DataFrame(store_data)

            cols = SELECT_COLUMNS_BEDRIFT.copy()
            if skjemadata: cols.append("virkNaeringskode")
            if enhetsinfo: cols.append("nace_2007")
            cols = [c for c in cols if c in df.columns]
            df = df[cols]

            bof_children = [
                {"field": "orgnr",    "headerName": "orgnr"},
                {"field": "org_form", "headerName": "org_form"},
                {"field": "navn",     "headerName": "navn"},
                {"field": "sn07_1",   "headerName": "sn07_1"},
                {"field": "sn2025_1", "headerName": "sn2025_1"},
                {"field": "kilde",    "headerName": "kilde",    "editable": True},
                {"field": "fritekst", "headerName": "fritekst", "editable": True},
            ]
            column_defs = [{"headerName": "BoF", "children": bof_children}]
            if skjemadata:
                column_defs.append({"headerName": "Altinn3",    "children": [{"field": "virkNaeringskode", "headerName": "virkNaeringskode"}]})
            if enhetsinfo:
                column_defs.append({"headerName": "Enhetsinfo", "children": [{"field": "nace_2007",        "headerName": "nace_2007"}]})

            return df.to_dict("records"), column_defs


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