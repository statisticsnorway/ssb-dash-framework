from pandas.core.frame import DataFrame


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

TYPE_REGNSKAP_FILEPATH = { # type: file-path
    "balanseregnskap": "/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/balanseregnskap",
    "resultatregnskap": "/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/resultatregnskap",
    "virksomhet": "/buckets/shared/nspek/naeringsdata/flat_p2024_v1.parquet/virksomhet",
    }
virksomhetsinfo_variabler = ["virksomhetstype", "regeltypeForAarsregnskap", "regnskapspliktstype", "start", "slutt"]

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

def get_virksomhetsinfo(virksomhetsinfo_filepath: str, variables_to_fetch: list, ident: str, aar: str, conn):
    """
    Fetch and return virksomhetsinfo from nspek files for specified variables for a unit.
    Searches through a folder to find the file with the ident of interest.

    Example use: get_virksomhetsinfo(TYPE_REGNSKAP_FILEPATH["virksomhet"], virksomhetsinfo_variabler, "932598957", "2023", conn)
    """
    t = conn.read_parquet(f"{virksomhetsinfo_filepath}/*.parquet")
    t = t.filter((t.norskIdentifikator == ident) & (t.inntektsaar == aar))
    filtered = t.filter(t['felt'].isin(variables_to_fetch)).select(["felt", "char_verdi"])
    df = filtered.execute()
    
    return df


def post_description_data(regnskapstype: str) -> DataFrame:
    """
    Returns a pandas dataframe with the npspek posts and their names.

    Example use: post_description_data("balanseregnskap")
    """
    post_file_path = "/buckets/produkt/temp/nspek_editeringsrammeverk/nspek_utility/"
    if regnskapstype == "balanseregnskap":
        poster = "nspek_balanseposter"
    elif regnskapstype == "resultatregnskap":
        poster = "nspek_resultatposter"
    df = pd.read_csv(f"{post_file_path}{poster}.csv")
    return df[["tekst", "felt"]]

def fetch_data_by_orgnr(regnskapstype: str, ident: str, aar: str, conn) -> DataFrame:
    """
    Returns a pandas dataframe with all nspek values found in the specified regnskapstype for a unit/orgnr.

    Example use: fetch_data_by_orgnr("resultatregnskap", "932598957", aar, conn)
    """
    file_path = TYPE_REGNSKAP_FILEPATH[regnskapstype]

    t = conn.read_parquet(f"{file_path}/*.parquet")
    t = t.filter((t.norskIdentifikator == ident) & (t.inntektsaar == aar))
    filtered = t.select(["felt", "belop"])
    df = filtered.execute()
    return df


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
        Explanation of module.
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

    def create_info_card(self, title: str, component_id: str, var_type: str):
        card_info = dbc.Card(
                children=[
                    dbc.CardHeader(title),
                    dbc.CardBody(
                        children=[
                            dbc.Input(id=component_id, type=var_type),
                        ],
                        className="nspek-card-body",
                    ),
                ],
                className="nspek-card",
        )
        return card_info

    def _create_layout(self):
        """
        Generates the layout for the nspek module.
        """
        layout = html.Div([
            # info cards
            html.Div(
                dbc.Row(
                    children=[
                        dbc.Col(
                            children=self.create_info_card(
                                title="Virksomhetstype",
                                component_id="nspek-info-card-virksomhetstype",
                                var_type="text",
                            ),
                        ),
                        dbc.Col(
                            children=self.create_info_card(
                                title="Regeltype",
                                component_id="nspek-info-card-regeltypeforaarsregnskap",
                                var_type="text",
                            ),
                        ),
                        dbc.Col(
                            children=self.create_info_card(
                                title="Type regnskapsplikt",
                                component_id="nspek-info-card-regnskapspliktstype",
                                var_type="text",
                            ),
                        ),
                        dbc.Col(
                            children=self.create_info_card(
                                title="Startdato",
                                component_id="nspek-info-card-start",
                                var_type="text",
                            ),
                        ),
                        dbc.Col(
                            children=self.create_info_card(
                                title="Sluttdato",
                                component_id="nspek-info-card-slutt",
                                var_type="text",
                            ),
                        ),
                    ],
                    className="nspek-info-cards"
                ),
            ),
            
            # data grids
            html.Div(
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
        ])

        return layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Naeringsspesifikasjon module."""
        
        @callback(
            Output(component_id="nspek-info-card-virksomhetstype", component_property="value"),
            Output(component_id="nspek-info-card-regeltypeforaarsregnskap", component_property="value"),
            Output(component_id="nspek-info-card-regnskapspliktstype", component_property="value"),
            Output(component_id="nspek-info-card-start", component_property="value"),
            Output(component_id="nspek-info-card-slutt", component_property="value"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
        )
        def create_info_cards_virksomhet(aar: str, orgnr_foretak: str) -> tuple[str, str, str, str, str]:
            """
            Returns a tuple of strings with the values for info cards for the top of the nspek module.
            These cards will hold virksomhetsinfo for the foretak.
            """
            df = get_virksomhetsinfo(
                virksomhetsinfo_filepath=TYPE_REGNSKAP_FILEPATH["virksomhet"], 
                variables_to_fetch=virksomhetsinfo_variabler, 
                ident=orgnr_foretak, 
                aar=aar, 
                conn=self.conn)

            virksomhetstype = df[df["felt"]=="virksomhetstype"]["char_verdi"]
            regeltype = df[df["felt"]=="regeltypeForAarsregnskap"]["char_verdi"]
            regnskapspliktstype = df[df["felt"]=="regnskapspliktstype"]["char_verdi"]
            start = df[df["felt"]=="start"]["char_verdi"]
            slutt = df[df["felt"]=="slutt"]["char_verdi"]

            return (
                virksomhetstype,
                regeltype,
                regnskapspliktstype,
                start,
                slutt
            )

        @callback(
            Output("nspek-balansedata-grid", "rowData"),
            Output("nspek-balansedata-grid", "columnDefs"),
            # Output("nspek-data-grid", "pinnedTopRowData"),
            Input("var-aar", "value"),
            Input("var-foretak", "value"),
        )
        def show_balanseregnskap(
            aar: str, 
            orgnr_foretak: str
            ):

            post_descriptions = post_description_data("balanseregnskap")
            ident_data = fetch_data_by_orgnr("balanseregnskap", orgnr_foretak, aar, self.conn)

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df = post_descriptions.merge(ident_data, how= "outer", on="felt")
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
            orgnr_foretak: str
            ):

            post_descriptions = post_description_data("resultatregnskap")
            ident_data = fetch_data_by_orgnr("resultatregnskap", orgnr_foretak, aar, self.conn)

            post_descriptions["felt"] = post_descriptions["felt"].astype(str)
            ident_data["felt"] = ident_data["felt"].astype(str)

            df = post_descriptions.merge(ident_data, how= "outer", on="felt")
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