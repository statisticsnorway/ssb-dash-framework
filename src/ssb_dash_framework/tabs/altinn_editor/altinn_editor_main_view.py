import logging

import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from ...setup.variableselector import VariableSelector
from ...utils import create_alert
from .altinn_editor_contact import AltinnEditorContact
from .altinn_editor_history import AltinnEditorHistory
from .altinn_editor_primary_table import AltinnEditorPrimaryTable
from .altinn_editor_submitted_forms import AltinnEditorSubmittedForms
from .altinn_editor_unit_details import AltinnEditorUnitDetails

logger = logging.getLogger(__name__)


class AltinnSkjemadataEditor:

    def __init__(
        self, time_units, conn, variable_connection, sidepanels=None, top_panels=None
    ) -> None:
        self.icon = "🗊"
        self.label = "Data editor"

        self.time_units = time_units
        self.conn = conn
        self.variable_connection = variable_connection

        self.variableselector = VariableSelector(
            selected_inputs=[], selected_states=self.time_units
        )

        self.primary_table = AltinnEditorPrimaryTable(
            time_units=self.time_units,
            conn=self.conn,
            variable_selector_instance=self.variableselector,
        )
        # Below is futureproofing in case of increasing modularity
        if sidepanels is None:
            self.sidepanels = [
                AltinnEditorSubmittedForms(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorUnitDetails(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_connection=self.variable_connection,
                    variable_selector_instance=self.variableselector,
                ),
            ]
        else:
            self.sidepanels = sidepanels
        if top_panels is None:
            self.top_panels = [
                AltinnEditorContact(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
                AltinnEditorHistory(
                    time_units=self.time_units,
                    conn=self.conn,
                    variable_selector_instance=self.variableselector,
                ),
            ]
        else:
            self.top_panels = top_panels

        self.module_callbacks()

    def get_skjemadata_table_names(self):
        """Retrieves the names of all the skjemadata-tables in the eimerdb."""
        all_tables = list(self.conn.tables.keys())
        skjemadata_tables = [
            element for element in all_tables if element.startswith("skjemadata")
        ]
        return [{"label": item, "value": item} for item in skjemadata_tables]

    def skjemadata_table_selector(self):
        skjemadata_table_names = self.get_skjemadata_table_names()
        return dbc.Col(
            dbc.Form(
                [
                    dbc.Label("Tabell", className="mb-1"),
                    dcc.Dropdown(
                        id="altinnedit-option1",
                        options=skjemadata_table_names,
                        value=skjemadata_table_names[0]["value"],
                    ),
                ]
            ),
            md=2,
        )

    def _create_layout(self):
        return html.Div(
            id="altinn-editor-main-view",
            style={
                "height": "100vh",
                "width": "100%",
            },
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                id="altinn-editor-sidepanels",
                                style={
                                    "height": "100%",
                                    "width": "100%",
                                },
                                children=[
                                    *[
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        unit, className="card-title"
                                                    ),
                                                    html.Div(
                                                        style={
                                                            "display": "grid",
                                                            "grid-template-columns": "100%",
                                                        },
                                                        children=[
                                                            dbc.Input(
                                                                id=f"altinnedit-{unit}",
                                                                type="number",
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                style={"max-height": "100%"},
                                            ),
                                            style={"max-height": "100%"},
                                        )
                                        for unit in self.time_units
                                    ],
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "ident", className="card-title"
                                                ),
                                                dbc.Input(
                                                    id="altinnedit-ident", type="text"
                                                ),
                                            ]
                                        ),
                                        className="mb-2",
                                    ),
                                    *[
                                        sidepanel_module.layout()
                                        for sidepanel_module in self.sidepanels
                                    ],
                                ],
                            ),
                            width=1,
                        ),
                        dbc.Col(
                            [
                                dbc.Row(
                                    id="altinn-editor-top-panels",
                                    children=[
                                        self.skjemadata_table_selector(),
                                        *[
                                            dbc.Col(top_panel.layout(), md=2)
                                            for top_panel in self.top_panels
                                        ],
                                    ],
                                ),
                                dbc.Row(
                                    html.Div(
                                        children=[self.primary_table.layout()],
                                    )
                                ),
                            ]
                        ),
                    ]
                )
            ],
        )

    def layout(self):
        """Generates the layout for the Altinn Skjemadata Editor tab."""
        return self._create_layout()

    def module_callbacks(self):
        def generate_callback(unit):
            @callback(  # type: ignore[misc]
                Output(f"altinnedit-{unit}", "value"),
                Input(f"var-{unit}", "value"),
            )
            def callback_function(value):
                return value

            return callback_function

        for unit in self.time_units:
            generate_callback(unit)

        @callback(  # type: ignore[misc]
            Output("altinnedit-ident", "value"),
            Input("var-ident", "value"),
        )
        def aar_to_tab(ident):
            return ident

        return None


class AltinnSkjemadataEditor2:
    """A tab for editing skjemadata.

    This module provides:
    - A sidebar what contains information about the enhet
    - How many forms the enhet has sent to SSB, with a unique version ID and a datetime.
    - An editable table that contains the skjemadata.
    - Kontrollutslag, kontaktinformasjon etc-

    Attributes:
        label (str): The label for the tab, set to "🗊 skjemadata_viewer".
        conn (eimerdb): EimerDB

    Methods:
        layout(): Generates the layout for the skjemadataViewer tab.
        callbacks(): Registers the Dash callbacks for handling user interactions.
    """

    def __init__(self, time_units, conn, variable_connection: dict | None = None):
        self.icon = "🗊"
        self.label = "Data editor"
        self.time_units = time_units
        self.conn = conn
        self.variable_connection = variable_connection

    def _is_valid(self):
        pass

    def create_callback_components(self, input_type="Input"):
        """Generates a list of dynamic Dash Input or State components."""
        component = Input if input_type == "Input" else State
        return [component(f"altinnedit-{unit}", "value") for unit in self.time_units]

    def update_partition_select(self, partition_dict, key_to_update):
        """Updates the dictionary by adding the previous value (N-1)
        to the list for a single specified key.

        :param partition_dict: Dictionary containing lists of values
        :param key_to_update: Key to update by appending (N-1)
        :return: Updated dictionary
        """
        if partition_dict.get(key_to_update):
            min_value = min(partition_dict[key_to_update])
            partition_dict[key_to_update].append(int(min_value) - 1)
        return partition_dict

    def _create_layout(self):
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
                        self.offcanvas_kontrollutslag(),  # Replace with the module
                        self.kontaktcanvas(),
                        self.historikkmodal(),
                        self.hjelpetabellmodal(),
                        self.kommentarmodal(),
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
                                                dbc.Label(  # Replace with the control view module
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
                    ],
                ),
            ],
        )
        return layout

    def layout(self):
        pass

    def module_callbacks(self):
        """Register Dash callbacks for the Pi memorizer tab.

        Notes:
            - The `update_input` callback handles the interaction between the numeric keypad
              and the current sequence, score, and high score.
        """
        for unit in self.time_units:

            def generate_callback(unit):
                @callback(  # type: ignore[misc]
                    Output(f"altinnedit-{unit}", "value"),
                    Input(f"var-{unit}", "value"),
                )
                def callback_function(value):
                    return value

                return callback_function

            generate_callback(unit)

        @callback(  # type: ignore[misc]
            Output("altinnedit-ident", "value"),
            Input("var-ident", "value"),
        )
        def aar_to_tab(ident):
            return ident

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaer", "options"),
            Output("altinnedit-skjemaer", "value"),
            Input("altinnedit-ident", "value"),
            *self.create_callback_components("Input"),
        )
        def update_skjemaer(ident, *args):
            if ident is None or any(arg is None for arg in args):
                return [], None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                skjemaer = self.conn.query(
                    f"SELECT * FROM enheter WHERE ident = '{ident}'",
                    create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=None,
                        **partition_args,
                    ),
                )["skjemaer"][0]

                skjemaer = [item.strip() for item in skjemaer.split(",")]
                skjemaer_dd_options = [
                    {"label": item, "value": item} for item in skjemaer
                ]
                options = skjemaer_dd_options
                value = skjemaer_dd_options[0]["value"]
                return options, value
            except Exception as e:
                logger.error(f"Error in update_skjemaer: {e}", exc_info=True)
                return [], None

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "rowData"),
            Output("altinnedit-table-skjemaer", "columnDefs"),
            Input("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
            *self.create_callback_components("State"),
        )
        def update_sidebar_table(skjema, ident, *args):
            if skjema is None or ident is None or any(arg is None for arg in args):
                return None, None

            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"""SELECT skjemaversjon, dato_mottatt, editert, aktiv
                    FROM skjemamottak WHERE ident = '{ident}' AND aktiv = True
                    ORDER BY dato_mottatt DESC""",
                    create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=skjema,
                        **partition_args,
                    ),
                )
                columns = [
                    (
                        {"headerName": col, "field": col, "editable": True}
                        if col in ["editert", "aktiv"]
                        else {"headerName": col, "field": col}
                    )
                    for col in df.columns
                ]
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(f"Error in update_sidebar_table: {e}", exc_info=True)
                return None, None

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemaer", "selectedRows"),
            Input("altinnedit-table-skjemaer", "rowData"),
            prevent_initial_call=True,
        )
        def hovedside_update_valgt_rad(rows):
            if not rows:
                return None

            selected_row = rows[0]
            return [selected_row]

        @callback(  # type: ignore[misc]
            Output("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
        )
        def selected_skjemaversjon(selected_row):
            if not selected_row:
                return None

            skjemaversjon = selected_row[0]["skjemaversjon"]
            return skjemaversjon

        @callback(  # type: ignore[misc]
            Output("var-valgt_tabell", "value"),
            Input("altinnedit-option1", "value"),
        )
        def valgt_tabell_til_variabelvelger(tabell):
            if tabell is None:
                return None
            return tabell

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data") * self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def set_skjema_to_edited(edited, skjema, alert_store, *args):
            if edited is None or skjema is None or any(arg is None for arg in args):
                return None

            partition_args = dict(zip(self.time_units, args, strict=False))
            variabel = edited[0]["colId"]
            old_value = edited[0]["oldValue"]
            new_value = edited[0]["value"]
            skjemaversjon = edited[0]["data"]["skjemaversjon"]

            if variabel == "editert":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET editert = {new_value}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    return [
                        create_alert(
                            f"Skjema {skjemaversjon} sin editeringsstatus er satt til {new_value}.",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception:
                    return [
                        create_alert(
                            "En feil skjedde under oppdatering av editeringsstatusen",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
            elif variabel == "aktiv":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET aktiv = {new_value}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    return [
                        create_alert(
                            f"Skjema {skjemaversjon} sin aktivstatus er satt til {new_value}.",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception:
                    return [
                        create_alert(
                            "En feil skjedde under oppdatering av aktivstatusen",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]

        @callback(  # type: ignore[misc]
            Output("offcanvas-kontrollutslag", "is_open"),
            Input("altinnedit-option5", "n_clicks"),
            State("offcanvas-kontrollutslag", "is_open"),
        )
        def toggle_offcanvas_kontrollutslag(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfocanvas", "is_open"),
            Input("altinnedit-option2", "n_clicks"),
            State("skjemadata-kontaktinfocanvas", "is_open"),
        )
        def toggle_offcanvas_kontaktinfo(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal", "is_open"),
            Input("altinnedit-option4", "n_clicks"),
            State("skjemadata-historikkmodal", "is_open"),
        )
        def toggle_historikkmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-skjemaversjonsmodal", "is_open"),
            Input("altinnedit-skjemaversjon-button", "n_clicks"),
            State("skjemadata-skjemaversjonsmodal", "is_open"),
        )
        def toggle_skjemaversjonsmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-kommentarmodal", "is_open"),
            Input("altinnedit-option6", "n_clicks"),
            State("skjemadata-kommentarmodal", "is_open"),
        )
        def toggle_kommentarmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("altinnedit-kommentarmodal-table1", "rowData"),
            Output("altinnedit-kommentarmodal-table1", "columnDefs"),
            Input("altinnedit-option6", "n_clicks"),
            State("altinnedit-skjemaer", "value"),
            State("altinnedit-ident", "value"),
        )
        def kommentar_table(n_clicks, skjema, ident):
            if n_clicks is None:
                return no_update
            df = self.conn.query(
                f"SELECT * FROM skjemamottak WHERE ident = '{ident}'",
                partition_select={"skjema": [skjema]},
            )
            columns = [
                {
                    "headerName": col,
                    "field": col,
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output("skjemadata-kommentarmodal-aar-kommentar", "value"),
            Input("altinnedit-kommentarmodal-table1", "selectedRows"),
        )
        def comment_select(selected_row):
            if selected_row is not None:
                kommentar = selected_row[0]["kommentar"]
            else:
                kommentar = ""
            return kommentar

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("skjemadata-kommentarmodal-savebutton", "n_clicks"),
            State("altinnedit-kommentarmodal-table1", "selectedRows"),
            State("skjemadata-kommentarmodal-aar-kommentar", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def update_kommentar(n_clicks, selected_row, kommentar, skjema, alert_store):
            if n_clicks > 0 and selected_row is not None:
                try:
                    row_id = selected_row[0]["row_id"]
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET kommentar = '{kommentar}'
                        WHERE row_id = '{row_id}'
                        """,
                        partition_select={"skjema": [skjema]},
                    )
                    alert_store = [
                        create_alert(
                            "Kommentarfeltet er oppdatert!",
                            "success",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception as e:
                    alert_store = [
                        create_alert(
                            f"Oppdatering av kommentarfeltet feilet. {str(e)[:60]}",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                return alert_store

        @callback(  # type: ignore[misc]
            Output("skjemadata-hjelpetabellmodal", "is_open"),
            Input("altinnedit-option3", "n_clicks"),
            State("skjemadata-hjelpetabellmodal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-enhetsinfomodal", "is_open"),
            Input("altinnedit-enhetsinfo-button", "n_clicks"),
            State("skjemadata-enhetsinfomodal", "is_open"),
        )
        def toggle_enhetsinfomodal(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("offcanvas-kontrollutslag-table1", "rowData"),
            Output("offcanvas-kontrollutslag-table1", "columnDefs"),
            Output("altinnedit-option5", "style"),
            Output("altinnedit-option5", "children"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
        )
        def kontrollutslagstabell(selected_row, skjema, *args):
            if (
                selected_row is None
                or len(selected_row) == 0
                or skjema is None
                or any(arg is None for arg in args)
            ):
                return None, None, None, "Se kontrollutslag"
            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                skjemaversjon = selected_row[0]["skjemaversjon"]
                df = self.conn.query(
                    f"""SELECT t1.kontrollid, subquery.skildring, t1.utslag
                    FROM kontrollutslag AS t1
                    JOIN (
                        SELECT t2.kontrollid, t2.skildring
                        FROM kontroller AS t2
                    ) AS subquery ON t1.kontrollid = subquery.kontrollid
                    WHERE skjemaversjon = '{skjemaversjon}'
                    AND utslag = True""",
                    partition_select=create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=skjema,
                        **partition_args,
                    ),
                )
                columns = [{"headerName": col, "field": col} for col in df.columns]
                antall_utslag = len(df)

                if antall_utslag > 0:
                    style = {"color": "#dc3545", "background-color": "#343a40"}
                    button_text = f"Se kontrollutslag ({antall_utslag})"
                else:
                    style = None
                    button_text = "Se kontrollutslag"

                return df.to_dict("records"), columns, style, button_text
            except Exception as e:
                logger.error(f"Error in kontrollutslagstabell: {e}", exc_info=True)
                return None, None, None, "Se kontrollutslag"

        @callback(  # type: ignore[misc]
            Output("skjemadata-historikkmodal-table1", "rowData"),
            Output("skjemadata-historikkmodal-table1", "columnDefs"),
            Input("skjemadata-historikkmodal", "is_open"),
            State("altinnedit-option1", "value"),
            State("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
        )
        def historikktabell(is_open, tabell, selected_row, skjema, *args):
            if is_open:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    skjemaversjon = selected_row[0]["skjemaversjon"]
                    df = self.conn.query_changes(
                        f"""SELECT * FROM {tabell}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        ORDER BY datetime DESC
                        """,
                        partition_select=create_partition_select(
                            desired_partitions=self.time_units,
                            skjema=skjema,
                            **partition_args,
                        ),
                    )
                    if df is None:
                        df = pd.DataFrame(columns=["ingen", "data"])
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
                except Exception as e:
                    logger.error(f"Error in historikktabell: {e}", exc_info=True)
                    return None, None
            else:
                raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("skjemadata-sidebar-enhetsinfo", "children"),
            Input("skjemadata-enhetsinfomodal-table1", "rowData"),
        )
        def update_sidebar(enhetsinfo_rows):
            if not enhetsinfo_rows:
                return html.P("Ingen enhetsinfo tilgjengelig.")

            return [
                html.Div(
                    [html.Strong(row["variabel"] + ": "), html.Span(str(row["verdi"]))],
                    style={"margin-bottom": "5px"},
                )
                for row in enhetsinfo_rows
            ]

        for output_id, variable in self.variable_connection.items():

            @callback(  # type: ignore[misc]
                Output(output_id, "value", allow_duplicate=True),
                Input("skjemadata-enhetsinfomodal-table1", "rowData"),
                prevent_initial_call=True,
            )
            def update_variable(row_data, variable=variable):
                if row_data is None:
                    return ""
                for row in row_data:
                    if row.get("variabel") == variable:
                        return row.get("verdi", "")
                return ""

        @callback(  # type: ignore[misc]
            Output("var-altinnskjema", "value"),
            Input("altinnedit-skjemaer", "value"),
        )
        def altinnskjema_til_variabelvelger(skjema):
            if skjema is None:
                return no_update
            return skjema

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfo-navn", "value"),
            Output("skjemadata-kontaktinfo-epost", "value"),
            Output("skjemadata-kontaktinfo-telefon", "value"),
            Output("skjemadata-kontaktinfo-kommentar1", "value"),
            Output("skjemadata-kontaktinfo-kommentar2", "value"),
            Input("altinnedit-option2", "n_clicks"),
            State("altinnedit-skjemaversjon", "value"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def kontaktinfocanvas(n_clicks, skjemaversjon, skjema, *args):
            partition_args = dict(zip(self.time_units, args, strict=False))
            df_skjemainfo = self.conn.query(
                f"""SELECT
                kontaktperson, epost, telefon, kommentar_kontaktinfo, kommentar_krevende
                FROM kontaktinfo
                WHERE skjemaversjon = '{skjemaversjon}'
                """,
                partition_select=create_partition_select(
                    desired_partitions=self.time_units, skjema=skjema, **partition_args
                ),
            )
            if df_skjemainfo.empty:
                logger.info("Kontaktinfo table for ")
            kontaktperson = df_skjemainfo["kontaktperson"][0]
            epost = df_skjemainfo["epost"][0]
            telefon = df_skjemainfo["telefon"][0]
            kommentar1 = df_skjemainfo["kommentar_kontaktinfo"][0]
            kommentar2 = df_skjemainfo["kommentar_krevende"][0]
            button_text = "kontaktinfo"
            return kontaktperson, epost, telefon, kommentar1, kommentar2
