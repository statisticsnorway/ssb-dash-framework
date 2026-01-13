import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from google.cloud import bigquery
from dapla import AuthClient
from datetime import datetime, date
import pandas as pd
import ibis
import logging
from typing import Any
from typing import ClassVar
from typing import Literal
import os

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

ibis.options.interactive = True
logger = logging.getLogger(__name__)

token = AuthClient.fetch_google_credentials()
project_id="skatt-naering-p-ph"
NSSPEK = bigquery.Client(credentials=token, project=project_id)


# input_options = {
#     "foretak": Input("var-foretak", "value"),
# }

# states_options = [
#     {
#         "aar": ("var-aar", "value"),
#         "nace": ("var-nace", "value"),
#     }
# ]

locale_NO = """d3.formatLocale({
  "decimal": ",",
  "thousands": "\u00a0",
  "grouping": [3],
  "currency": ["", " kr"],
  "percent": "\u202f%",
  "nan": ""
})"""

columnDefs = [
    {
        "field": "registrering_id",
        "headerName": "registrering_id",
        "hide": True,
        "editable": False,
        "flex": 0
    },
    {
        "field": "felt",
        "headerName": "felt",
        "hide": False,
        "editable": False,
        "flex": 3,
    },
    {
        "field": "tekst",
        "headerName": "tekst",
        "hide": False,
        "editable": False,
        "tooltipField": "tekst",
        "flex": 1,
    },
    {
        "field": "belop",
        "headerName": "belop",
        "hide": False,
        "editable": True,
        "type": "rightAligned",
        "valueFormatter": {"function": f"{locale_NO}.format('$,.0f')(params.value)"},
        "flex": 3
    },
    {
        "field": "endret_dato",
        "headerName": "endret dato",
        "hide": False,
        "editable": False,
        "flex": 2
    },
    {
        "field": "endret_av",
        "headerName": "endret av",
        "hide": False,
        "editable": False,
        "flex": 2
    }
]

columns = ["registrering_id", "felt", "tekst", "belop", "endret_dato", "endret_av"]
df = pd.DataFrame(columns=columns)
rowData = df.to_dict("records")

#midlertidig
import dapla as dp
df_felttekster = dp.read_pandas("gs://ssb-skatt-naering-data-produkt-prod/temp/temp_felttekster_p2022.parquet")

USERNAME = (os.getenv("DAPLA_USER") or "")[:3]
RESULTATTABELL = "skatt-naering-p-ph.skatt_naering.skatt_naering_beloep"

modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("TimeTravel")),
        dbc.ModalBody(
            [
                dbc.Row(
                    [
                        dbc.RadioItems(
                            options=[
                                {"label": "nyeste", "value": "nyeste"},
                                {"label": "timetravel", "value": "timetravel"},
                            ],
                            value="nyeste",
                            id="tab-nsspek-modal1-ritems1",
                            className="btn-group",
                            inputClassName="btn-check",
                            labelClassName="btn btn-outline-primary",
                            labelCheckedClassName="active",
                        ),
                    ],
                    className="justify-content-center"
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Legg inn dato:"),
                                dcc.DatePickerSingle(
                                    id="tab-nspek-modal1-datepicker1",
                                    min_date_allowed=date(2024, 1, 1),
                                    max_date_allowed=date(2034, 1, 1),
                                    initial_visible_month=date(2024, 1, 1),
                                    date=date(2024, 1, 1)
                                ),
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Legg inn tidspunkt:"),
                                dbc.Input(placeholder="00:00:00", id="tab-nspek-modal1-input1")
                            ]
                        )
                    ],
                    className="justify-content-center"
                ),
            ],
            className="d-flex flex-column justify-content-center align-items-center"
        )
    ],
    id="tab-nspek-modal1",
    is_open=False,
)

historikkmodal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Historikk")),
        dbc.ModalBody(
            [
                dag.AgGrid(
                    id="tab-nspek-modal2-table1",
                    className="ag-theme-alpine-dark header-style-on-filter",
                    columnSize="responsiveSizeToFit",
                ),
            ],
            className="d-flex flex-column justify-content-center align-items-center"
        )
    ],
    id="tab-nspek-modal2",
    size="xl",
    is_open=False,
)


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
        self.label = "Næringsspesifikasjon"

        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
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
        layout = html.Div(
            style={"height": "100vh", "display": "flex", "flexDirection": "column"},
            children=[
                modal,
                historikkmodal,
                dbc.Container(
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                        dbc.Label("År"),
                                        dbc.Input("tab-nspek-input1", type="number"),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                        dbc.Label("Orgnr"),
                                        dbc.Input("tab-nspek-input2"),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                        dbc.Label("Versjon"),
                                        dcc.Dropdown(id="tab-nspek-dd1"),
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                        dbc.Label("TimeTravel"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.P("Nyeste", id="tab-nspek-datetime"),
                                                        ]
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button("Velg dato", id="tab-nspek-button1"),
                                                        ]
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                        dbc.Label("Historikk"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.P(id="tab-nspek-felthist"),
                                                        ]
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button("Se historikk", id="tab-nspek-button2"),
                                                        ]
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ),
                            ]
                        ),
                    ],
                    fluid=True,
                ),
                html.Div(
                    style={
                        "height": "100%",
                        "overflow": "hidden",
                        "display": "grid",
                        "grid-template-columns": "5% 55% 5% 20% 5%",
                    },
                    children=[
                        html.Div(),
                        dag.AgGrid(
                            id="tab-ns-table1",
                            className="ag-theme-alpine-dark header-style-on-filter",
                            columnDefs=columnDefs,
                            rowData=rowData,
                            style={"height": "80%", "width": "100%"},
                        ),
                        html.Div(),
                        html.Div(
                            style={
                                "height": "100%",
                                "overflow": "hidden",
                                "display": "grid",
                                "grid-template-rows": "10% 70%",
                            },
                            children=[
                                html.Div(
                                    [
                                        dbc.Label("Tema"),
                                        dcc.Dropdown(
                                            id="tab-nspek-dd2",
                                            options=[
                                                {"label": "resultat", "value": "resultat"},
                                                {"label": "balanse", "value": "balanse"},
                                            ],
                                            value="resultat",
                                        ),
                                    ]
                                ),
                                dcc.Textarea(id="tab-nspek-textarea1", placeholder="Tomt kommentarfelt"),                             
                            ]
                        ),
                        html.Div(),
                    ]
                ),
                html.P(id="tab-ns-status")
            ]
        )
        return layout

    def module_callbacks(self):
        @callback(
            Output("tab-nspek-input1", "value"),
            Input("var-aar", "value"),
        )
        def update_aar(aar):
            return aar

        @callback(
            Output("tab-nspek-input2", "value"),
            Input("var-foretak", "value"),
        )
        def update_aar(foretak):
            return foretak

        @callback(
            Output("tab-nspek-dd1", "options"),
            Input("tab-nspek-input1", "value"),
            Input("tab-nspek-input2", "value"),
        )
        def update_dd1(aar, orgnr):
            df = NSSPEK.query(
                f"""SELECT id, sekvensnummer
                FROM skatt_naering.skatt_naering_registrering
                WHERE aar = {aar} AND orgnr = '{orgnr}'
                """).to_dataframe()
            df["order"] = df["sekvensnummer"].rank(method="first").astype(int)
            df["order"] = df["order"].apply(lambda x: f"{x:03}")
            df = df.sort_values(by="sekvensnummer").reset_index(drop=True)
            df.rename(columns={"id": "value"}, inplace=True)
            df["label"] = df["order"].astype(str) + ": " + df["sekvensnummer"].astype(str)
            df.drop(columns=["sekvensnummer", "order"], inplace=True)
            df = df.sort_values(by="label", ascending=False).reset_index(drop=True)
            options = [{"label": row["label"], "value": row["value"]} for index, row in df.iterrows()]
            return options

        @callback(
            Output("tab-nspek-dd1", "value"),
            Input("tab-nspek-dd1", "options"),
        )
        def update_value_dd1(options):
            value = options[0]["value"]
            return value

        @callback(
            Output("tab-nspek-modal1", "is_open"),
            Input("tab-nspek-button1", "n_clicks"),
            State("tab-nspek-modal1", "is_open"),
        )
        def toggle_timetravel_modal(n, is_open):
            if n:
                return not is_open
            return is_open

        @callback(
            Output("tab-nspek-modal2", "is_open"),
            Input("tab-nspek-button2", "n_clicks"),
            State("tab-nspek-modal2", "is_open"),
        )
        def toggle_historikkmodal(n, is_open):
            if n:
                return not is_open
            return is_open

        @callback(
            Output("tab-ns-table1", "selectedRows", allow_duplicate=True),
            Input("tab-ns-table1", "rowData"),
            prevent_initial_call=True,
        )
        def hovedside_update_valgt_skjema(rows):
            selected_row = rows[0]
            return [selected_row]

        @callback(
            Output("tab-nspek-datetime", "children"),
            Input("tab-nsspek-modal1-ritems1", "value"),
            Input("tab-nspek-modal1-datepicker1", "date"),
            Input("tab-nspek-modal1-input1", "value"),
        )
        def test(option, date, time):
            if option == "nyeste":
                return "nyeste"
            elif option == "timetravel":
                date_object = datetime.strptime(date, "%Y-%m-%d").date()
                datetime_combined = datetime.combine(date_object, datetime.strptime(time, "%H:%M:%S").time())
                datetime_string = datetime_combined.strftime("%Y-%m-%d %H:%M:%S")
                return datetime_string

        @callback(
            Output("tab-ns-table1", "rowData"),
            Input("tab-nspek-dd1", "value"),
            Input("tab-nspek-dd2", "value"),
            Input("tab-ns-status", "children"),
            Input("tab-nspek-datetime", "children"),
        )
        def hovedside_table_prefill_forbruk(reg_id, tabtype, status, timetravel):
            if reg_id:
                if timetravel == "nyeste":
                    timetravel_sql = ""
                else:
                    timetravel_sql = f"AND (endret_dato <= TIMESTAMP('{timetravel}') OR endret_dato IS NULL)"
                if tabtype == "resultat":
                    df = NSSPEK.query(
                        f"""SELECT registrering_id, felt, belop, endret_dato, endret_bruker
                        FROM skatt_naering.skatt_naering_beloep
                        WHERE registrering_id = '{reg_id}'
                        {timetravel_sql}
                        QUALIFY
                            ROW_NUMBER() OVER (PARTITION BY felt ORDER BY endret_dato DESC) = 1
                        ORDER BY felt
                        """).to_dataframe()
                    df = df.merge(df_felttekster, on="felt", how="left")
                    df = df[["registrering_id", "felt", "tekst", "belop", "endret_dato", "endret_bruker"]]
                return df.to_dict("records")
            else:
                raise PreventUpdate

        @callback(
            Output("tab-nspek-modal2-table1", "rowData"),
            Output("tab-nspek-modal2-table1", "columnDefs"),
            Input("tab-nspek-button2", "n_clicks"),
            State("tab-nspek-dd1", "value"),
            State("tab-nspek-dd2", "value"),
            State("tab-nspek-felthist", "children"),
            
        )
        def update_historikktabell(n_clicks, reg_id, tabtype, felt):
            if n_clicks > 0:
                if tabtype == "resultat":
                    df = NSSPEK.query(
                        f"""SELECT registrering_id, felt, belop, endret_dato, endret_bruker
                        FROM skatt_naering.skatt_naering_beloep
                        WHERE registrering_id = '{reg_id}'
                            AND felt = '{felt}'
                        ORDER BY endret_dato
                        """).to_dataframe()
                    df = df[["registrering_id", "felt", "belop", "endret_dato", "endret_bruker"]]
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": True if col == "registrering_id" else False,
                    }
                    for col in df.columns
                ]
                return df.to_dict("records"), columns
            else:
                raise PreventUpdate

        @callback(
            Output("tab-ns-status", "children"),
            Input("tab-ns-table1", "cellValueChanged"),
            prevent_initial_call=True,
        )
        def update_bigquery(edited):
            if edited is None:
                raise PreventUpdate
            if edited is not None:
                registrering_id = edited[0]["data"]["registrering_id"]
                felt = edited[0]["data"]["felt"]
                variabel = edited[0]["colId"]
                new_value = edited[0]["value"]
                if variabel == "belop":
                    now = datetime.now()
                    new_row = [
                        {
                            "registrering_id": registrering_id,
                            "felt": felt,
                            "belop": new_value,
                            "endret_bruker": USERNAME,
                            "endret_dato": now.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ]
                    errors = NSSPEK.insert_rows_json(RESULTATTABELL, new_row)

                    if errors == []:
                        return f"Felt {felt} oppdatert til {new_value}"
                    else:
                        return(f"Feil under oppdatering: {errors}")
                else:
                    return(f"Kolonna {variabel} kan ikke editeres!")

        @callback(
            Output("tab-nspek-felthist", "children"),
            Input("tab-ns-table1", "cellClicked"),
            State("tab-ns-table1", "rowData"),
        )
        def select_felt(click, row_data):
            return row_data[click["rowIndex"]]["felt"]

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