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

ibis.options.interactive = True
logger = logging.getLogger(__name__)

# alle filene ligg her
NSSPEK = '/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/'

noposter_resultatregnskap: DataFrame= pd.read_csv("/buckets/produkt/temp/nspek_editeringsrammeverk/nspek_utility/nspek_resultatposter.csv")
noposter_balanseregnskap: DataFrame= pd.read_csv("/buckets/produkt/temp/nspek_editeringsrammeverk/nspek_utility/nspek_balanseposter.csv")

TYPE_REGNSKAP = { # type: file-path
    "balanseregnskap": "/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/balanseregnskap",
    "resultatregnskap": "/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/resultatregnskap"
    }
# balanseposter (1000–2999)
BALANSEPOSTER = {
    "eiendeler": range(1000, 2000),              # 1000–1999
    "egenkapital og gjeld": range(2000, 3000),   # 2000–2999
}
# resultatposter (3000–8999)
RESULTATPOSTER = {
    "driftsinntekter": range(3000, 4000),                 # 3000–3999
    "varekostnader": range(4000, 5000),                   # 4000–4999
    "lønn- og personalkostnader": range(5000, 6000),      # 5000–5999
    "avskrivninger": range(6000, 7000),                   # 6000–6999
    "andre driftskostnader": range(7000, 8000),           # 7000–7999
    "finansinntekter og finanskostnader": range(8000, 9000), # 8000–8999
}


def post_description_data(regnskapstype):
    """
    Returns a pandas dataframe with the npspek posts and their names.

    Example use: post_description_data("balanseregnskap")
    """
    post_file_path = "/home/onyxia/work/stat-naringer-dash/ssb-dash-framework/src/ssb_dash_framework/modules//nspek_utility/"
    if regnskapstype == "balanseregnskap":
        poster = "nspek_balanseposter"
    elif regnskapstype == "resultatregnskap":
        poster = "nspek_resultatposter"
    df = pd.read_csv(f"{post_file_path}{poster}.csv")
    return df[["tekst", "felt"]]

# df = post_description_data("balanseregnskap")
# print(df)

def fetch_data_by_orgnr(regnskapstype, ident, conn):
    """
    Returns a pandas dataframe with all nspek values found in the specified regnskapstype for a unit/orgnr.

    Example use: fetch_data_by_orgnr("resultatregnskap", "932598957")
    """
    file_path = TYPE_REGNSKAP[regnskapstype]

    t = conn.read_parquet(f"{file_path}/*.parquet")
    filtered = t.filter(t.norskIdentifikator == ident)

    df = filtered.execute()
    return df[["felt", "belop"]]

# print(fetch_data_by_orgnr("resultatregnskap", "932598957"))

class Naeringsspesifikasjon:
    """
    The Naeringsspesifikasjon module lets you view the nspek/naeringsspesifikasjon for a specified foretak (var-foretak).
    """
    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the module_callbacks.
            "foretak",
        ]
    )

    def __init__(self, time_units: list[str]) -> None:
        """
        Explanation of module
        """
        self.module_number = Naeringsspesifikasjon._id_number
        self.module_name = self.__class__.__name__
        self.icon = "📒"
        self.label = "NSPEK"

        self.conn: BaseBackend = ibis.connect("duckdb://")
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
        for var in Naeringsspesifikasjon._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"Naeringsspesifikasjon requires the variable selector option '{var}' to be set."
                ) from e

    def _create_layout(self):
        """
        Generates the layout for the nspek module.
        """
        layout = html.Div(
            className="nspek-container",
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "100vh",
                "width": "100%",
                "padding": "20px",
                "gap": "20px"
            },
            children=[
                html.Div(
                    className="nspek-balansegrid-container",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "45vh",
                        "width": "100%"
                    },
                    children=[
                        html.H4("Balanseregnskap"),
                        AgGrid(
                            id="nspek-balansedata-grid",
                            getRowId="params.data.id",
                            defaultColDef={
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                            },
                            columnSize="responsiveSizeToFit",
                            rowData=[],
                            columnDefs=[],
                            dashGridOptions={
                                "rowSelection": "single",
                                "enableCellTextSelection": True,
                                "enableBrowserTooltips": True,
                            },
                            style={"height": "100%", "width": "100%"},
                        ),
                    ],
                ),
                html.Div(
                    className="nspek-resultatdata-container",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "45vh",
                        "width": "100%"
                    },
                    children=[
                        html.H4("Resultatregnskap"),
                        AgGrid(
                            id="nspek-resultatdata-grid",
                            getRowId="params.data.id",
                            defaultColDef={
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                            },
                            columnSize="responsiveSizeToFit",
                            rowData=[],
                            columnDefs=[],
                            dashGridOptions={
                                "rowSelection": "single",
                                "enableCellTextSelection": True,
                                "enableBrowserTooltips": True,
                            },
                            style={"height": "100%", "width": "100%"},
                        ),
                    ],
                ),
            ],
        )

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Naeringsspesifikasjon module."""
        
        @callback(
            Output("nspek-balansedata-grid", "rowData"),
            Output("nspek-balansedata-grid", "columnDefs"),
            # Output("nspek-data-grid", "pinnedTopRowData"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
        )
        def show_balanseregnskap(
            aar: str, 
            foretak_orgnr: str
            ):

            post_descriptions = post_description_data("balanseregnskap")
            ident_data = fetch_data_by_orgnr("balanseregnskap", foretak_orgnr, self.conn)

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df = post_descriptions.merge(ident_data, how= "left", on="felt")
            df = df.rename(columns={"tekst": "beskrivelse", "felt": "post", "belop": "verdi"})

            row_data = df.to_dict("records")
            column_defs = [
                {
                    "field": col, 
                    "headerName": col,
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    
                }
                for col in df.columns
            ]

            return row_data, column_defs
        
        @callback(
            Output("nspek-resultatdata-grid", "rowData"),
            Output("nspek-resultatdata-grid", "columnDefs"),
            # Output("nspek-data-grid", "pinnedTopRowData"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
        )
        def show_resultatregnskap(
            aar: str, 
            foretak_orgnr: str
            ):

            post_descriptions = post_description_data("resultatregnskap")
            ident_data = fetch_data_by_orgnr("resultatregnskap", foretak_orgnr, self.conn)

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df = post_descriptions.merge(ident_data, how= "left", on="felt")
            df = df.rename(columns={"tekst": "beskrivelse", "felt": "post", "belop": "verdi"})
            row_data = df.to_dict("records")

            column_defs = [
                {
                    "field": col, 
                    "headerName": col,
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    
                }
                for col in df.columns
            ]

            return row_data, column_defs


class NaeringsspesifikasjonTab(TabImplementation, Naeringsspesifikasjon):
    """NaeringsspesifikasjonTab is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""
    def __init__(self, time_units: list[str]) -> None:
        """Initializes the NaeringsspesifikasjonTab class."""
        Naeringsspesifikasjon.__init__(
            self, time_units=time_units
        )
        TabImplementation.__init__(self)


class NaeringsspesifikasjonWindow(WindowImplementation, Naeringsspesifikasjon):
    """NaeringsspesifikasjonWindow is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""
    def __init__(self, time_units: list[str]) -> None:
        """Initializes the NaeringsspesifikasjonWindow class."""
        Naeringsspesifikasjon.__init__(
            self, time_units=time_units
        )
        WindowImplementation.__init__(self)