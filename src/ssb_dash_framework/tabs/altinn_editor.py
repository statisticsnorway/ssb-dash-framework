import logging
import re

import pandas as pd
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
                    self.create_partition_select(skjema=skjema, **partition_args),
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
            Output(
                "skjemadata-hovedtabell-updatestatus", "children", allow_duplicate=True
            ),
            Input("altinnedit-table-skjemaer", "cellValueChanged"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def set_skjema_to_edited(edited, skjema, *args):
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
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    return f"Skjema {skjemaversjon} sin editeringsstatus er satt til {new_value}."
                except Exception:
                    return "En feil skjedde under oppdatering av editeringsstatusen"
            elif variabel == "aktiv":
                try:
                    self.conn.query(
                        f"""
                        UPDATE skjemamottak
                        SET aktiv = {new_value}
                        WHERE skjemaversjon = '{skjemaversjon}'
                        """,
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
                        ),
                    )
                    return f"Skjema {skjemaversjon} sin aktivstatus er satt til {new_value}."
                except Exception:
                    return "En feil skjedde under oppdatering av editeringsstatusen"

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
            Output("skjemadata-hjelpetabellmodal-table1", "rowData"),
            Output("skjemadata-hjelpetabellmodal-table1", "columnDefs"),
            Input("skjemadata-hjelpetabellmodal-tabs", "active_tab"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            Input("skjemadata-hjelpetablellmodal-dd", "value"),
            State("altinnedit-option1", "value"),
            State("altinnedit-ident", "value"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def hjelpetabeller(
            tab, selected_row, rullerende_var, tabell, ident, skjema, *args
        ):
            if tab == "modal-hjelpetabeller-tab1":
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    partition_select = self.create_partition_select(
                        skjema=skjema, **partition_args
                    )
                    partition_select_no_skjema = self.create_partition_select(
                        skjema=None, **partition_args
                    )
                    updated_partition_select = self.update_partition_select(
                        partition_select, rullerende_var
                    )
                    skjemaversjon = selected_row[0]["skjemaversjon"]
                    column_name_expr_outer = SQL_COLUMN_CONCAT.join(
                        [f"s.{unit}" for unit in self.time_units]
                    )
                    column_name_expr_inner = SQL_COLUMN_CONCAT.join(
                        [f"t2.{unit}" for unit in self.time_units]
                    )

                    group_by_clause = ", ".join(
                        [f"s.{unit}" for unit in self.time_units]
                    )

                    query = f"""
                        SELECT
                            s.variabel,
                            {column_name_expr_outer} AS time_combination,
                            SUM(CAST(s.verdi AS NUMERIC)) AS verdi
                        FROM {tabell} AS s
                        JOIN (
                            SELECT
                                {column_name_expr_inner} AS time_combination,
                                t2.ident,
                                t2.skjemaversjon,
                                t2.dato_mottatt
                            FROM
                                skjemamottak AS t2
                            WHERE aktiv = True
                            QUALIFY
                                ROW_NUMBER() OVER (PARTITION BY time_combination, t2.ident ORDER BY t2.dato_mottatt DESC) = 1
                        ) AS mottak_subquery ON
                            {column_name_expr_outer} = mottak_subquery.time_combination
                            AND s.ident = mottak_subquery.ident
                            AND s.skjemaversjon = mottak_subquery.skjemaversjon
                        JOIN (
                        SELECT * FROM datatyper AS d
                        ) AS subquery ON s.variabel = subquery.variabel
                        WHERE s.ident = '{ident}' AND subquery.datatype = 'int'
                        GROUP BY s.variabel, subquery.radnr, {group_by_clause}
                        ORDER BY subquery.radnr
                        ;
                    """

                    df = self.conn.query(
                        query.format(ident=ident),
                        partition_select={
                            tabell: updated_partition_select,
                            "datatyper": partition_select_no_skjema,
                        },
                    )

                    df_wide = df.pivot(
                        index="variabel", columns="time_combination", values="verdi"
                    ).reset_index()

                    df_wide = df_wide.rename(
                        columns={
                            col: f"verdi_{col}" if col != "variabel" else col
                            for col in df_wide.columns
                        }
                    )

                    df_wide.columns.name = None

                    def extract_numeric_sum(col_name):
                        numbers = list(map(int, re.findall(r"\d+", col_name)))
                        return sum(numbers) if numbers else 0

                    time_columns_sorted = sorted(
                        [col for col in df_wide.columns if col.startswith("verdi_")],
                        key=extract_numeric_sum,
                    )

                    if len(time_columns_sorted) >= 2:
                        latest_col = max(time_columns_sorted, key=extract_numeric_sum)
                        prev_col = min(time_columns_sorted, key=extract_numeric_sum)
                        df_wide["diff"] = df_wide[latest_col] - df_wide[prev_col]
                        df_wide["pdiff"] = (df_wide["diff"] / df_wide[prev_col]) * 100
                        df_wide["pdiff"] = df_wide["pdiff"].round(2).astype(str) + " %"
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                        }
                        for col in df_wide.columns
                    ]
                    return df_wide.to_dict("records"), columns
                except Exception as e:
                    logger.error(f"Error in hjelpetabeller: {e}", exc_info=True)
                    return None, None

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
                    partition_select=self.create_partition_select(
                        skjema=skjema, **partition_args
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
                        partition_select=self.create_partition_select(
                            skjema=skjema, **partition_args
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
