import logging

from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils.alert_handler import create_alert
from .altinn_components import AltinnComponents

logger = logging.getLogger(__name__)

SQL_COLUMN_CONCAT = " || '_' || "


class AltinnSkjemadataEditor(AltinnComponents):
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

    def __init__(
        self,
        time_units: list[str],
        variable_connection: dict,
        conn: object,
    ) -> None:
        """Initialize the PimemorizerTab component.

        Attributes:
            label (str): The label for the tab.
            conn (str): An EimerDB class instance.
            variable_connection (dict): A dictionary that connects the variables in the app with the enhetsinfotabell.
            time_units (list): A list of strings, where each string is a time unit.
        """
        super().__init__(time_units)
        self.variableselector = VariableSelector(
            selected_inputs=["ident", *time_units],
            selected_states=[],  # Hard coding ident for now, using variableselector to re-use error message if ident or time_units is missing.
        )
        self.label = "🗊 Altinn3-skjemadata"
        self.variable_connection = variable_connection
        self.conn = conn
        self.is_valid()
        self.callbacks()

    def is_valid(self):  # TODO add validation
        pass

    def get_skjemadata_table_names(self):
        """Retrieves the names of all the skjemadata-tables in the eimerdb."""
        all_tables = list(self.conn.tables.keys())
        skjemadata_tables = [
            element for element in all_tables if element.startswith("skjemadata")
        ]
        skjemadata_dd_options = [
            {"label": item, "value": item} for item in skjemadata_tables
        ]
        return skjemadata_dd_options

    def create_partition_select(self, skjema=None, **kwargs):
        partition_select = {
            unit: [kwargs[unit]] for unit in self.time_units if unit in kwargs
        }
        if skjema is not None:
            partition_select["skjema"] = [skjema]
        return partition_select

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

    def callbacks(self) -> None:
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
            self.variableselector.get_inputs(),
        )
        def aar_to_tab(ident, *args):
            return ident

        @callback(  # type: ignore[misc]
            Output("skjemadata-enhetsinfomodal-table1", "rowData"),
            Output("skjemadata-enhetsinfomodal-table1", "columnDefs"),
            Input("altinnedit-ident", "value"),
            *self.create_callback_components("Input"),
        )
        def update_enhetsinfotabell(ident, *args):
            if ident is None or any(arg is None for arg in args):
                logger.debug(
                    f"update_enhetsinfotabell is lacking input, returning None. ident is {ident} Received args: %s",
                    args,
                )
                return None, None
            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                df = self.conn.query(
                    f"SELECT * FROM enhetsinfo WHERE ident = '{ident}'",
                    self.create_partition_select(skjema=None, **partition_args),
                )
                df.drop(columns=["row_id"], inplace=True)
                columns = [{"headerName": col, "field": col} for col in df.columns]
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(f"Error in update_enhetsinfotabell: {e}", exc_info=True)
                return None, None

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
                    self.create_partition_select(skjema=None, **partition_args),
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
            Output("var-valgt_tabell", "value"),
            Input("altinnedit-option1", "value"),
        )
        def valgt_tabell_til_variabelvelger(tabell):
            if tabell is None:
                return None
            return tabell

        @callback(  # type: ignore[misc]
            Output("altinnedit-table-skjemadata", "rowData"),
            Output("altinnedit-table-skjemadata", "columnDefs"),
            Input("altinnedit-skjemaversjon", "value"),
            Input("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
        )
        def hovedside_update_altinnskjema(skjemaversjon, tabell, skjema, *args):
            schema = self.conn.tables[tabell]["schema"]
            columns = {field["name"] for field in schema}
            if "variabel" in columns and "verdi" in columns:
                long_format = True
            else:
                long_format = False

            if (
                skjemaversjon is None
                or tabell is None
                or skjema is None
                or any(arg is None for arg in args)
            ):
                return None, None
            if long_format == True:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    df = self.conn.query(
                        f"""
                        SELECT t.*, subquery.radnr
                        FROM {tabell} AS t
                        JOIN (
                            SELECT aar, radnr, tabell, variabel
                            FROM datatyper
                        ) AS subquery
                        ON subquery.aar = t.aar AND subquery.variabel = t.variabel
                        WHERE t.skjemaversjon = '{skjemaversjon}'
                        AND subquery.tabell = '{tabell}'
                        ORDER BY subquery.radnr ASC
                        """,
                        partition_select={
                            tabell: self.create_partition_select(
                                skjema=skjema, **partition_args
                            ),
                            "datatyper": self.create_partition_select(
                                skjema=None, **partition_args
                            ),
                        },
                    )
                    df.drop(columns=["radnr"], inplace=True)
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                            "flex": 2 if col == "variabel" else 1,
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
                except Exception as e:
                    logger.error(
                        f"Error in hovedside_update_altinnskjema (long format): {e}",
                        exc_info=True,
                    )
                    return None, None
            else:
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    df = self.conn.query(
                        f"""
                        SELECT * FROM {tabell}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                            "hide": col == "row_id",
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
                except Exception as e:
                    logger.error(
                        f"Error in hovedside_update_altinnskjema (non-long format): {e}",
                        exc_info=True,
                    )
                    return None, None

        @callback(  # type: ignore[misc]
            Output("var-statistikkvariabel", "value"),
            Input("altinnedit-table-skjemadata", "cellClicked"),
            State("altinnedit-table-skjemadata", "rowData"),
        )
        def select_variabel(click, row_data):
            if row_data is None:
                return no_update
            return row_data[click["rowIndex"]]["variabel"]

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
            Output("alert_store", "data", allow_duplicate=True),
            Input("altinnedit-table-skjemadata", "cellValueChanged"),
            State("altinnedit-option1", "value"),
            State("altinnedit-skjemaer", "value"),
            State("alert_store", "data"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def update_table(edited, tabell, skjema, alert_store, *args):
            if edited is None:
                raise PreventUpdate
            else:
                partition_args = dict(zip(self.time_units, args, strict=False))
                tables_editable_dict = {}
                data_dict = self.conn.tables

                for table, details in data_dict.items():
                    if table.startswith("skjemadata") and "schema" in details:
                        field_editable_dict = {
                            field["name"]: field.get("app_editable", False)
                            for field in details["schema"]
                        }
                        tables_editable_dict[table] = field_editable_dict

                table_editable_dict = tables_editable_dict[tabell]
                edited_column = edited[0]["colId"]

                schema = self.conn.tables[tabell]["schema"]
                columns = {field["name"] for field in schema}
                if "variabel" in columns and "verdi" in columns:
                    long_format = True
                else:
                    long_format = False

                if table_editable_dict[edited_column] == True:
                    old_value = edited[0]["oldValue"]
                    new_value = edited[0]["value"]
                    row_id = edited[0]["data"]["row_id"]
                    ident = edited[0]["data"]["ident"]

                    try:
                        self.conn.query(
                            f"""UPDATE {tabell}
                            SET {edited_column} = '{new_value}'
                            WHERE row_id = '{row_id}'
                            """,
                            partition_select=self.create_partition_select(
                                skjema=skjema, **partition_args
                            ),
                        )
                        if long_format == True:
                            variabel = edited[0]["data"]["variabel"]
                            alert_store = [
                                create_alert(
                                    f"ident: {ident}, variabel: {variabel} er oppdatert fra {old_value} til {new_value}!",
                                    "success",
                                    ephemeral=True,
                                ),
                                *alert_store,
                            ]
                        else:
                            alert_store = [
                                create_alert(
                                    f"ident: {ident}, {edited_column} er oppdatert fra {old_value} til {new_value}!",
                                    "success",
                                    ephemeral=True,
                                ),
                                *alert_store,
                            ]
                    except Exception as e:
                        alert_store = [
                            create_alert(
                                f"Oppdateringa feilet. {str(e)[:60]}",
                                "danger",
                                ephemeral=True,
                            ),
                            *alert_store,
                        ]
                    return alert_store
                else:
                    return f"Kolonnen {edited_column} kan ikke editeres!"

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
                partition_select=self.create_partition_select(
                    skjema=skjema, **partition_args
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
