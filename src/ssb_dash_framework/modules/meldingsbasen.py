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

ibis.options.interactive = True
logger = logging.getLogger(__name__)

class Meldingsbasen:
    """
    
    """
    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the module_callbacks.
            "foretak",
        ]
    )

    def __init__(self, time_units: list[str]) -> None:
        """
        Explanation of module.
        """
        self.module_number = Meldingsbasen._id_number
        self.module_name = self.__class__.__name__
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

    def create_info_card(self, title: str, component_id: str, var_type: str):
        card_info = dbc.Card(
                children=[
                    dbc.CardHeader(title),
                    dbc.CardBody(
                        children=[
                            dbc.Input(id=component_id, type=var_type),
                        ],
                        className="meldingsbasen-card-body",
                    ),
                ],
                className="meldingsbasen-card",
        )
        return card_info

    def get_enhetsinfo(virksomhetsinfo_filepath: str, variables_to_fetch: list, ident: str, aar: str, conn):
        """
        """
        t = conn.read_parquet(f"{virksomhetsinfo_filepath}/*.parquet")
        t = t.filter((t.norskIdentifikator == ident) & (t.inntektsaar == aar))
        filtered = t.filter(t['felt'].isin(variables_to_fetch)).select(["felt", "char_verdi"])
        df = filtered.execute()
        
        return df

    def _create_layout(self):
        """
        Generates the layout for the meldingsbasen module.
        """
        layout = html.Div(
            children=[
                # buttons and options
                html.Div(
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
                ),
                # data grids
                html.Div(
                    # Dropdown with option as foretak, which if True shows a foretak AgGrid. Default True.
                ),

                html.Div(
                    # Dropdown with option as bedrift, which if True shows a foretak AgGrid. Default False
                ),
            ],
        )

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Meldingsbasen module."""

        @callback(

        )
        def show_foretak_data(
            aar: str, 
            orgnr_foretak: str
            ):

            with sqlite3.connect(SSB_FORETAK_PATH) as conn:
                df = pd.read_sql_query(
                    f"SELECT * FROM ssb_foretak WHERE orgnr = '{orgnr}'", conn
                )

            if skjema:
                s = self.conn.table("core_skjemadata_mapped")
                s = (
                    s.filter(_.aar == aar)
                    .filter(_.ident == orgnr_foretak)
                    .filter(_.refnr.isin(active_no_duplicates_refnr_list(conn)))
                    .filter(_.variabel == "naeringskode")
                    .select(["ident", "refnr", "verdi"]).to_pandas()
                s = s.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})
                print(s)

                df = df.merge(s, how="left", on="orgnr")
            
            if enhetsinfo:
                e = self.conn.table("enhetsinfo")
                e = (
                    s.filter(_.aar == aar)
                    .filter(_.ident == orgnr_foretak)
                    .filter(_.variabel == "nace_2007")
                    .select(["ident", "verdi"]).to_pandas()
                s = s.rename(columns={"ident": "orgnr", "verdi": "sn07_1"})
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

        )
        def show_bedrift_data(
            aar: str, 
            orgnr_foretak: str
            ):

            if orgnr_foretak is not None:
                with sqlite3.connect(SSB_BEDRIFT_PATH) as conn:
                    df = pd.read_sql_query(
                        f"""SELECT bedrifts_nr, orgnr, navn, sn07_1, sn2025_1, org_form,
                        FROM ssb_bedrift WHERE foretaks_nr = '{orgnr_foretak}';""",
                        conn,
                    )

            df["kilde"] = df["kilde"].astype(str)
            df["fritekst"] = df["fritekst"].astype(str)

            if skjema:
                s = self.conn.table("core_skjemadata_mapped")
                s = (
                    s.filter(_.aar == aar)
                    .filter(_.ident != orgnr_foretak)
                    .filter(_.refnr == refnr) # fetch from table above
                    .filter(_.variabel == "virkNaeringskode")
                    .select(["ident", "verdi"]).to_pandas()
                print(s)
            
            if enhetsinfo:
                e = self.conn.table("enhetsinfo")
                e = (
                    s.filter(_.aar == aar)
                    .filter(_.foretak == orgnr_foretak)
                    .filter(_.variabel == "nace_2007")
                    .select(["ident", "verdi"]).to_pandas()
                print(e)

            
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


class NaeringsspesifikasjonTab(TabImplementation, Meldingsbasen):
    """NaeringsspesifikasjonTab is an implementation of the Meldingsbasen module as a tab in a Dash application."""
    def __init__(self, time_units: list[str]) -> None:
        """Initializes the NaeringsspesifikasjonTab class."""
        Meldingsbasen.__init__(
            self, time_units=time_units
        )
        TabImplementation.__init__(self)


class NaeringsspesifikasjonWindow(WindowImplementation, Meldingsbasen):
    """NaeringsspesifikasjonWindow is an implementation of the Meldingsbasen module as a tab in a Dash application."""
    def __init__(self, time_units: list[str]) -> None:
        """Initializes the NaeringsspesifikasjonWindow class."""
        Meldingsbasen.__init__(
            self, time_units=time_units
        )
        WindowImplementation.__init__(self)