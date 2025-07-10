import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html


class AltinnComponents:
    """Components for the Altinn Skjemadata Editor.

    Includes:
    - layout (The main layout)
    - Offcanvas for kontaktinfo and controls
    - Modals
    - Function for creating ag grids
    """

    def __init__(self, time_units: int) -> None:
        """Altinn editing module layout and some other methods."""
        self.time_units = time_units

    def layout(self) -> html.Div:
        """Generate the layout for the Pi memorizer tab."""
        skjemadata_table_names = self.get_skjemadata_table_names()

        layout = html.Div(
            style={
                "display": "flex",
                "flexDirection": "row",
                "overflowY": "auto",
                "minHeight": "95vh",
                "maxHeight": "95vh",
            },
            children=[
                html.Div(
                    style={"width": "10%", "padding": "0.5rem"},
                    children=[
                        # self.offcanvas_kontrollutslag(),
                        self.kontaktcanvas(),
                        # self.historikkmodal(),
                        self.hjelpetabellmodal(),
                        # self.kommentarmodal(),
                        # self.skjemaversjonsmodal(),
                        self.enhetsinfomodal(),
                        *self.create_cards(),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("ident", className="card-title"),
                                    dbc.Input(id="altinnedit-ident", type="text"),
                                ]
                            ),
                            className="mb-2",
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("skjemaer", className="card-title"),
                                    dcc.Dropdown(id="altinnedit-skjemaer"),
                                ]
                            ),
                            className="mb-2",
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Skjemaversjon", className="card-title"),
                                    dbc.Input(
                                        id="altinnedit-skjemaversjon",
                                        type="text",
                                        className="mb-2",
                                    ),
                                    dbc.Button(
                                        "Se alle",
                                        id="altinnedit-skjemaversjon-button",
                                        type="text",
                                    ),
                                ]
                            ),
                            className="mb-2",
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Enhetsinfo", className="card-title"),
                                    dbc.Button(
                                        "Se all enhetsinfo",
                                        id="altinnedit-enhetsinfo-button",
                                        type="text",
                                    ),
                                ]
                            ),
                            className="mb-2",
                        ),
                        html.Div(id="skjemadata-sidebar-enhetsinfo"),
                    ],
                ),
                html.Div(
                    style={
                        "width": "90%",
                        "padding": "1rem",
                    },
                    children=[
                        dbc.Container(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label("Tabell", className="mb-1"),
                                                dcc.Dropdown(
                                                    id="altinnedit-option1",
                                                    options=skjemadata_table_names,
                                                    value=skjemadata_table_names[0][
                                                        "value"
                                                    ],
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label(
                                                    "Kontaktinfo", className="mb-1"
                                                ),
                                                dbc.Button(
                                                    "Se kontaktinfo",
                                                    id="altinnedit-option2",
                                                    className="w-100",
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label(
                                                    "Hjelpetabeller",
                                                    className="mb-1",
                                                ),
                                                dbc.Button(
                                                    "Åpn hjelpetabeller",
                                                    id="altinnedit-option3",
                                                    className="w-100",
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label(
                                                    "Historikk",
                                                    className="mb-1",
                                                ),
                                                dbc.Button(
                                                    "Se historikk",
                                                    id="altinnedit-option4",
                                                    className="w-100",
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label(
                                                    "Kontroller", className="mb-1"
                                                ),
                                                dbc.Button(
                                                    "Se kontrollutslag",
                                                    id="altinnedit-option5",
                                                    className="w-100",
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Form(
                                            [
                                                dbc.Label(
                                                    "Editeringskommentar",
                                                    className="mb-1",
                                                ),
                                                dbc.Button(
                                                    "Se kommentarer",
                                                    id="altinnedit-option6",
                                                    className="w-100",
                                                ),
                                            ]
                                        ),
                                        md=2,
                                    ),
                                ]
                            ),
                            fluid=True,
                            className="mb-3",
                        ),
                        dag.AgGrid(
                            id="altinnedit-table-skjemadata",
                            className="ag-theme-alpine-dark header-style-on-filter",
                            style={"width": "100%", "height": "90%"},
                            defaultColDef={
                                "resizable": True,
                                "sortable": True,
                                "floatingFilter": True,
                                "editable": True,
                                "filter": "agTextColumnFilter",
                                "flex": 1,
                            },
                            dashGridOptions={"rowHeight": 38},
                        ),
                        dbc.Row(
                            html.P(id="skjemadata-hovedtabell-updatestatus"),
                            className="mt-2",
                        ),
                    ],
                ),
            ],
        )
        return layout

    def create_cards(self) -> list[dbc.Card]:
        """Return a list of dbc.Card components dynamically generated for each time unit."""
        return [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(unit, className="card-title"),
                        html.Div(
                            style={
                                "display": "grid",
                                "grid-template-columns": "100%",
                            },
                            children=[
                                dbc.Input(id=f"altinnedit-{unit}", type="number"),
                            ],
                        ),
                    ],
                    style={"max-height": "100%"},
                ),
                style={"max-height": "100%"},
            )
            for unit in self.time_units
        ]
