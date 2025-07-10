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
                        self.skjemaversjonsmodal(),
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

    def kontaktcanvas(self) -> html.Div:
        """Retuns an offcanvas component containing a table with contact information."""
        return html.Div(
            [
                dbc.Offcanvas(
                    html.Div(
                        style={
                            "display": "grid",
                            "grid-template-rows": "10% 10% 10% 35% 35%",
                            "height": "100%",
                        },
                        children=[
                            html.Div(
                                [
                                    html.Label("Navn:"),
                                    dbc.Input(
                                        type="text",
                                        id="skjemadata-kontaktinfo-navn",
                                        placeholder="Navn Navnesen",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("E-post:"),
                                    dbc.Input(
                                        type="email",
                                        id="skjemadata-kontaktinfo-epost",
                                        placeholder="navn@mail.com",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("Telefonnummer:"),
                                    dbc.Input(
                                        type="text",
                                        id="skjemadata-kontaktinfo-telefon",
                                        placeholder="12345678",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("Kontaktinfokommentar:"),
                                    dbc.Textarea(
                                        placeholder="Ingen kommentar",
                                        id="skjemadata-kontaktinfo-kommentar1",
                                        style={"height": "80%"},
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("kommentar_krevende:"),
                                    dbc.Textarea(
                                        placeholder="Ingen kommentar",
                                        id="skjemadata-kontaktinfo-kommentar2",
                                        style={"height": "80%"},
                                        disabled=True,
                                    ),
                                ]
                            ),
                        ],
                    ),
                    id="skjemadata-kontaktinfocanvas",
                    title="Kontaktinfo og kommentarer",
                    is_open=False,
                    placement="end",
                    backdrop=False,
                    style={"width": "25%", "height": "100%"},
                ),
            ]
        )

    def enhetsinfomodal(self) -> dbc.Modal:
        """Returns a modal component containing a table with enhetsinfo."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Enhetsinfo")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={"editable": True},
                        id="skjemadata-enhetsinfomodal-table1",
                        className="ag-theme-alpine-dark header-style-on-filter",
                    ),
                    className="d-flex flex-column justify-content-center align-items-center",
                ),
            ],
            id="skjemadata-enhetsinfomodal",
            is_open=False,
            size="xl",
        )



    def skjemaversjonsmodal(self) -> dbc.Modal:
        """Returns a modal component with a table containing all the skjema versions."""
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Skjemaversjoner")),
                dbc.ModalBody(
                    dag.AgGrid(
                        defaultColDef={
                            "resizable": True,
                            "sortable": True,
                            "floatingFilter": True,
                            "filter": "agTextColumnFilter",
                        },
                        id="altinnedit-table-skjemaer",
                        dashGridOptions={"rowSelection": "single"},
                        columnSize="responsiveSizeToFit",
                        className="ag-theme-alpine-dark header-style-on-filter",
                    ),
                ),
            ],
            id="skjemadata-skjemaversjonsmodal",
            is_open=False,
            size="xl",
        )

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

    def hjelpetabellmodal(self) -> dbc.Modal:
        """Return a modal component containing tab content. Future versions may support adding new tabs."""
        hjelpetabellmodal = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Hjelpetabeller")),
                dbc.ModalBody(
                    html.Div(
                        [
                            html.P("Velg hvilken tidsenhet som skal rullere -1:"),
                            dcc.Dropdown(
                                id="skjemadata-hjelpetablellmodal-dd",
                                options=[
                                    {"label": unit, "value": unit}
                                    for unit in self.time_units
                                ],
                                value=self.time_units[0] if self.time_units else None,
                                clearable=False,
                                className="dbc",
                            ),
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        self.create_ag_grid(
                                            "skjemadata-hjelpetabellmodal-table1"
                                        ),
                                        tab_id="modal-hjelpetabeller-tab1",
                                        label="Endringer",
                                    ),
                                    dbc.Tab(
                                        self.create_ag_grid(
                                            "skjemadata-hjelpetabellmodal-table2"
                                        ),
                                        tab_id="modal-hjelpetabeller-tab2",
                                        label="Tabell2",
                                    ),
                                ],
                                id="skjemadata-hjelpetabellmodal-tabs",
                            ),
                        ],
                    ),
                ),
            ],
            id="skjemadata-hjelpetabellmodal",
            is_open=False,
            size="xl",
        )
        return hjelpetabellmodal

    def create_ag_grid(self, component_id: str) -> dag.AgGrid:
        """Returns a non-editable AgGrid component with a dark alpine theme."""
        return dag.AgGrid(
            defaultColDef={"editable": False},
            id=component_id,
            className="ag-theme-alpine-dark header-style-on-filter",
        )
