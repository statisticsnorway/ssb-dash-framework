from pandas.core.frame import DataFrame
import sqlite3
from dash_ag_grid import AgGrid
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import datetime as dt
import pandas as pd
import ibis
from ibis import _
from ibis.backends import BaseBackend
import logging
from typing import Any, Literal
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
from ..utils.alert_handler import create_alert

from klass import KlassCorrespondence
from klass import KlassVersion

ibis.options.interactive = True
logger = logging.getLogger(__name__)

SELECT_COLUMNS_FORETAK = [
    "foretaks_nr",
    "orgnr",
    "org_form",
    "navn",
    "sn07_1",
    "sn07_navn",
    "sn07_et",
    "sn2025_1",
    "sn2025_2", "sn2025_3",
    "sn2025_navn",
    "sn25_et",
    "sn2025_1_gdato",
    "fritekst",
    "kilde",
    "antall_ansatte",
    "omsetning",
    "sn07_options",
    "edited_cells"
]
SELECT_COLUMNS_BEDRIFT = [
    "orgnr",
    "org_form",
    "navn",
    "sn07_1",
    "sn07_navn",
    "sn07_et",
    "sn2025_1", 
    "sn2025_2", "sn2025_3",
    "sn2025_navn",
    "sn25_et",
    "sn2025_1_gdato",
    "fritekst",
    "kilde",
    "antall_ansatte_f",
    "omsetning_f",
    "sn07_options",
    "edited_cells"
]


def klass_korrespondanse_naring(naring: str) -> dict[str, Any]:
    """
    Function to fetch and return corresponding SN codes for SN 2007 when SN 2025 has been chosen.
    If either the naring or naring label differs between SN 2007 and SN 2025, it will show up the correspondance table.
    This can either be a 1 to 1 match between naring SN 2007 and naring SN 2025, where only the label differs.
    If so, then the corresponding naring and label for SN 2007 are returned.
    If muliple corresponding values exist, all are returned as options for the user to select the correct one.

    Otherwise, there is a 1 to 1 match between SN 2007 and SN 2025, and the 2025 naring and label is returned.

    Returns a dict with:
        - sn2025_code, sn2025_name
        - sn2007_options: list of {code, name} dicts (1 = auto-fill, >1 = user selects)
        - needs_selection: bool
    """
    korr = KlassCorrespondence(correspondence_id=2749)
    sn_2025_df = KlassVersion(version_id="3218").data
    sn_2007_df = KlassVersion(version_id="30").data

    sn2025_row = sn_2025_df[sn_2025_df.code == naring][["code", "name"]].reset_index(
        drop=True
    )
    sn2025_name = sn2025_row.name[0] if not sn2025_row.empty else ""

    korr_df = korr.data
    korr_df = korr_df[korr_df.sourceCode == naring]

    if korr_df.empty:
        # 1-1, no correspondence table entry -> use sn2025 as-is
        return {
            "sn2025_code": naring,
            "sn2025_name": sn2025_name,
            "sn2007_options": [{"code": naring, "name": sn2025_name}],
            "needs_selection": False,
        }

    options = korr_df[["targetCode", "targetName"]].drop_duplicates()
    sn2007_options = [
        {"code": r.targetCode, "name": r.targetName} for _, r in options.iterrows()
    ]

    return {
        "sn2025_code": naring,
        "sn2025_name": sn2025_name,
        "sn2007_options": sn2007_options,
        "needs_selection": len(sn2007_options) > 1,
    }


class Meldingsbasen:
    """ """

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
                dbc.Row(
                    children=[
                        dbc.Button(
                            "Send oppdateringer",
                            id="meldingsbasen-save-edits-button1",
                            className="meldingsbasen-button-update",
                        ),
                    ],
                    className="meldingsbasen-topbar",
                ),
                dbc.Row(
                    className="meldingsbasen-sidebar",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("omsetning"),
                                            dbc.CardBody(
                                                [
                                                    dbc.Input(
                                                        id="meldingsbasen-foretak-omsetning-card",
                                                        type="text",
                                                    ),
                                                ],
                                                className="meldingsbasen-foretak-card-body",
                                            ),
                                        ],
                                        className="meldingsbasen-foretak-card",
                                    ),
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("antall ansatte"),
                                            dbc.CardBody(
                                                [
                                                    dbc.Input(
                                                        id="meldingsbasen-foretak-ansatte-card",
                                                        type="text",
                                                    ),
                                                ],
                                                className="meldingsbasen-foretak-card-body",
                                            ),
                                        ],
                                        className="meldingsbasen-foretak-card",
                                    ),
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        className="meldingsbasen-checklist",
                                        id="meldingsbasen-checklist",
                                        options=[
                                            {
                                                "label": "Vis skjemadata",
                                                "value": "skjemadata",
                                            },
                                            {
                                                "label": "Vis enhetsinfo",
                                                "value": "enhetsinfo",
                                            },
                                        ],
                                        value=["skjemadata", "enhetsinfo"],
                                        switch=True,
                                    ),
                                    className="ms-auto d-flex align-items-center",
                                    width="auto",
                                ),
                            ]
                        ),
                    ],
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
                                        html.Label(
                                            "Foretak", className="meldingsbasen-label"
                                        ),
                                        AgGrid(
                                            id="meldingsbasen-foretak-grid",
                                            getRowId="params.data.orgnr",
                                            defaultColDef={
                                                "sortable": True,
                                                "filter": True,
                                                "resizable": True,
                                                "cellStyle": {"function": "editedCellStyle"},
                                            },
                                            columnSize="responsiveSizeToFit",
                                            rowData=[],
                                            columnDefs=[],
                                            dashGridOptions={
                                                "rowSelection": "single",
                                                "enableCellTextSelection": True,
                                                "stopEditingWhenCellsLoseFocus": True,
                                                "suppressRowClickSelection": False,
                                            },
                                            style={"width": "100%"},
                                        ),
                                    ],
                                ),
                                dcc.Store(id="meldingsbasen-bedrift-store"),
                                html.Div(
                                    className="meldingsbasen-bedrift-grid-container",
                                    children=[
                                        html.Label(
                                            "Bedrifter", className="meldingsbasen-label"
                                        ),
                                        AgGrid(
                                            id="meldingsbasen-bedrift-grid",
                                            getRowId="params.data.orgnr",
                                            defaultColDef={
                                                "sortable": True,
                                                "filter": True,
                                                "resizable": True,
                                                "cellStyle": {"function": "editedCellStyle"},
                                            },
                                            columnSize="responsiveSizeToFit",
                                            rowData=[],
                                            columnDefs=[],
                                            dashGridOptions={
                                                "rowSelection": "single",
                                                "enableCellTextSelection": True,
                                                "stopEditingWhenCellsLoseFocus": True,
                                                "suppressRowClickSelection": False,
                                            },
                                            style={"height": "100%", "width": "100%"},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        return layout

    def _enrich_naring_names(self, df: pd.DataFrame) -> pd.DataFrame:
        df["sn07_navn"] = None
        df["sn2025_navn"] = None

        sn_2025_df = KlassVersion(version_id="3218").data
        sn_2007_df = KlassVersion(version_id="30").data

        for idx, row in df.iterrows():
            if pd.notna(row.get("sn07_1")) and row["sn07_1"]:
                match = sn_2007_df[sn_2007_df.code == row["sn07_1"]]
                if not match.empty:
                    df.at[idx, "sn07_navn"] = match.iloc[0]["name"]

            if pd.notna(row.get("sn2025_1")) and row["sn2025_1"]:
                match = sn_2025_df[sn_2025_df.code == row["sn2025_1"]]
                if not match.empty:
                    df.at[idx, "sn2025_navn"] = match.iloc[0]["name"]

        return df

    def _handle_naring_edit(self, edited, rows, column_defs, alert_store):
        """
        Shared logic for handling sn2025_1 edits in both foretak and bedrift grids.
        Returns updated (row_data, column_defs, alert_data)
        """
        if not edited or edited[0].get("colId") != "sn2025_1":
            raise PreventUpdate

        changed = edited[0]
        orgnr = changed["data"]["orgnr"]
        new_naring = changed["data"]["sn2025_1"]

        df = pd.DataFrame(rows)
        row_idx = edited[0]["rowIndex"]
        row = df.iloc[row_idx]

        antall_ansatte = int(
            row.get("antall_ansatte") or row.get("antall_ansatte_f") or 0
        )
        omsetning = int(row.get("omsetning") or row.get("omsetning_f") or 0)
        print(f"antall_ansatte: {antall_ansatte}")
        print(f"omsetning: {omsetning}")

        # Update sn2025_1 in df
        df.loc[df["orgnr"] == orgnr, "sn2025_1"] = new_naring

        # Fetch correspondence
        result = klass_korrespondanse_naring(new_naring)

        if antall_ansatte > 9 or omsetning > 5_000_000:

            # Update sn2025 name row if you have one, or add tooltip/description col
            df.loc[df["orgnr"] == orgnr, "sn2025_navn"] = result["sn2025_name"]

            if not result["needs_selection"]:
                # 1-1 match, auto-fill sn07_1
                sn07 = result["sn2007_options"][0]
                sn07_code = sn07["code"]
                sn07_name = sn07["name"]
                df.loc[df["orgnr"] == orgnr, "sn07_1"] = sn07["code"]
                df.loc[df["orgnr"] == orgnr, "sn07_navn"] = sn07["name"]

                alert_store = [
                    create_alert(
                        f"sn2025_1 for {orgnr} endret til {new_naring}, og sn07_1 endret til {sn07_code}!",
                        "success",
                        ephemeral=True,
                        duration=6,
                    ),
                    *alert_store,
                ]
            else:
                # Multiple options — put them in sn07_1 cell as dropdown options
                options = [o["code"] for o in result["sn2007_options"]]
                option_labels = [
                    f"{o['code']} {o['name']}" for o in result["sn2007_options"]
                ]

                if "sn07_options" not in df.columns:
                    df["sn07_options"] = None

                # Mark the cell as needing selection — store options in a separate col
                df.loc[df["orgnr"] == orgnr, "sn07_1"] = None
                df.at[df[df["orgnr"] == orgnr].index[0], "sn07_options"] = [
                    {"code": str(o["code"]), "name": str(o["name"])}
                    for o in result["sn2007_options"]
                ]
                # df.at[df[df["orgnr"] == orgnr].index[0], "sn07_options"] = result[
                #     "sn2007_options"
                # ]  # store for JS renderer

                # # Update column def for sn07_1 to use dropdown with these specific options
                # for col_group in column_defs:
                #     for child in col_group.get("children", []):
                #         if child["field"] == "sn07_1":
                #             child["cellRenderer"] = "DropdownRenderer"
                #             child["editable"] = False
                #             child["cellRendererParams"] = {
                #                 "optionsField": "sn07_options",
                #                 "valueField": "code",
                #                 "labelField": "name",
                #             }

                alert_store = [
                    create_alert(
                        f"sn2025_1 for {orgnr} endret til {new_naring}! sn07_1 må velges manuelt.",
                        "success",
                        ephemeral=True,
                        duration=6,
                    ),
                    *alert_store,
                ]

            return df.to_dict("records"), column_defs, alert_store

        # Leave sn07_1 blank
        df.loc[df["orgnr"] == orgnr, "sn07_1"] = None
        df.loc[df["orgnr"] == orgnr, "sn07_et"] = None
        sn25_name = result["sn2025_name"]

        alert_store = [
            create_alert(
                f"sn2025_1 for {orgnr} endret til {new_naring}, og sn07_1 endret til blank (liten enhet, oms < 5 mil og/eller antall ansatte < 9)",
                "success",
                ephemeral=True,
                duration=8,
            ),
            *alert_store,
        ]
        return df.to_dict("records"), column_defs, alert_store

    def _split_sn07_selection(self, edited, rows, column_defs, alert_store):
        """
        After user has selected an SN value in sn07_1, it splits the code from the name/label into their separate columns.
        The code is moved to the "sn07_1" column, and the name to the "sn07_navn" column.
        Example input:
            sn07_1 (from "edited" data): "01.190 Dyrking av ettårige vekster ellers"
        Output:
            sn07_1 -> "01.190"
            sn07_navn -> "Dyrking av ettårige vekster ellers"
        """
        if not edited or edited[0].get("colId") != "sn07_1":
            raise PreventUpdate

        selected = edited[0]["data"]["sn07_1"]
        # selected_code = selected[:6]  # fetch sn-code
        orgnr = edited[0]["data"]["orgnr"]

        df = pd.DataFrame(rows)
        row_idx = df[df["orgnr"] == orgnr].index[0]

        # Look up name from stored options
        name = ""
        if "sn07_options" in df.columns:
            sn07_options = df.at[row_idx, "sn07_options"]
            if sn07_options and isinstance(sn07_options, list):
                match = next((o for o in sn07_options if o["code"] == selected), None)
                if match:
                    name = match["name"]
                    selected = match["code"]  # ensure only code is stored

        df.at[row_idx, "sn07_1"] = selected
        df.at[row_idx, "sn07_navn"] = name.strip()
        df.at[row_idx, "sn07_options"] = None  # clear options after selection

        # Reset sn07_1 column def back to plain text
        for col_group in column_defs:
            for child in col_group.get("children", []):
                if child["field"] == "sn07_1":
                    child.pop("cellRenderer", None)
                    child.pop("cellRendererParams", None)
                    child["editable"] = True

        alert_store = [
            create_alert(
                f"sn07_1 for {orgnr} oppdatert til {selected}!",
                "success",
                ephemeral=True,
                duration=6,
            ),
            *alert_store,
        ]
        return df.to_dict("records"), column_defs, alert_store

    def _check_sn_input(self, edited, alert_store) -> tuple[Literal[bool], list[Any]]:
        """
        Logical checks for the sn2025_1 column to make sure the user puts in a valid value.
        """
        edit = edited[0]["data"]["sn2025_1"]
        old_value = edited[0]["oldValue"]
        print(f"blank_before: {old_value}")
        if not edit and old_value != None:
            return False, alert_store

        orgnr: Any = edited[0]["data"]["orgnr"]

        if not isinstance(edit, str) or len(edit) != 6 or "." not in edit:
            alert_store = [
                create_alert(
                    f"Feil næringsformat for {orgnr}: Du skrev: {edit}, forventet format: xx.xxx. Eksempelvis: 01.190.",
                    "danger",
                    ephemeral=True,
                    duration=10,
                ),
                *alert_store,
            ]
            return False, alert_store

        sn_klass_check = klass_korrespondanse_naring(edit)
        if (
            sn_klass_check["sn2025_name"] == ""
            or sn_klass_check["sn2007_options"][0]["name"] == ""
        ):
            alert_store = [
                create_alert(
                    f"{edit} er ikke en godkjent SN 2025 næringskode!",
                    "danger",
                    ephemeral=True,
                    duration=8,
                ),
                *alert_store,
            ]
            return False, alert_store

        return True, alert_store

    def _mark_edited(self, rows: list[dict], orgnr: str, cols: str | list[str]) -> list[dict]:
        """Marks a cell as edited in the edited_cells tracking dict for a given row."""
        for row in rows:
            if row.get("orgnr") == orgnr:
                edited_cells = row.get("edited_cells") or {}
                if not isinstance(edited_cells, dict):
                    edited_cells = {}
                if type(cols) == list:
                    for column in cols:
                        edited_cells[column] = True
                else:
                    edited_cells[cols] = True
                row["edited_cells"] = edited_cells
                break
        return rows

    def _edit_tracking(self, edited, edited_col: str, orgnr: str, rows, column_defs, alert_store):
        """
        Handles how edits are handled and logged for foretak and bedrift for columns:
        - sn2025_1: Checks if the SN value is valid, and updates sn07_1 with blank, 1-1 match, or dropdown selector.
        - sn07_et & sn25_et: Updates dropdown value to selected.
        - sn07_1: When updated, splits SN code & SN label/name into sn07_1 and sn07_navn, respectively.
        - fritekst: Updates text box with input.
        - sn2025_1_gdato: Updates date to correct format.

        All edits are tracked using the function 'mark_edited', to log edits and colour edited cells. 
        """
        changed = edited[0]
        df = pd.DataFrame(rows)

        # ensure tracking column exists
        if "edited_cells" not in df.columns:
            df["edited_cells"] = [{} for _ in range(len(df))]

        if edited_col == "sn2025_1":
            valid_check, alert_store = self._check_sn_input(edited, alert_store)
            if valid_check == False:
                df.loc[df["orgnr"] == orgnr, "sn2025_1"] = changed["oldValue"]
                return df.to_dict("records"), column_defs, alert_store
            row_data, column_defs, alert_store = self._handle_naring_edit(
                edited, rows, column_defs, alert_store
            )
            row_data = self._mark_edited(row_data, orgnr, ["sn2025_1", "sn07_1"])
            return row_data, column_defs, alert_store

        elif edited_col in ("sn07_et", "sn25_et"):
            alert_store = [
                create_alert(
                    f"Endringstype ({edited_col}) for {orgnr} oppdatert til '{changed['value']}'!",
                    "success",
                    ephemeral=True,
                    duration=4,
                ),
                *alert_store,
            ]
            row_data = self._mark_edited(rows, orgnr, edited_col)
            return row_data, column_defs, alert_store

        elif edited_col == "sn07_1":
            row_data, column_defs, alert_store = self._split_sn07_selection(
                edited, rows, column_defs, alert_store
            )
            row_data = self._mark_edited(row_data, orgnr, edited_col)
            return row_data, column_defs, alert_store

        elif edited_col == "fritekst":
            alert_store = [
                create_alert(
                    f"Fritekst for {orgnr} oppdatert til '{changed['value']}'!",
                    "success",
                    ephemeral=True,
                    duration=8,
                ),
                *alert_store,
            ]
            row_data = self._mark_edited(rows, orgnr, edited_col)
            return row_data, column_defs, alert_store

        elif edited_col == "sn2025_1_gdato":
            new_date = changed["data"]["sn2025_1_gdato"]
            new_date = pd.to_datetime(new_date, errors="coerce")

            if pd.notna(new_date):
                new_date = new_date.strftime("%Y-%m-%d")
            else:
                new_date = None
            print(new_date)
            df = pd.DataFrame(rows)
            df.loc[df["orgnr"] == orgnr, "sn2025_1_gdato"] = new_date

            alert_store = [
                create_alert(
                    f"Dato for {orgnr} oppdatert til {new_date}!",
                    "success",
                    ephemeral=True,
                    duration=4,
                ),
                *alert_store,
            ]
            row_data = self._mark_edited(df.to_dict("records"), orgnr, "sn2025_1_gdato")
            return row_data, column_defs, alert_store

        raise PreventUpdate

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
                    f"SELECT foretaks_nr, orgnr, navn, sn07_1, sn07_1_rdato, sn07_1_gdato, sn2025_1, sn2025_2, sn2025_3, sn2025_1_rdato, sn2025_1_gdato, org_form, omsetning, antall_ansatte FROM ssb_foretak WHERE orgnr = '{orgnr_foretak}'",
                    conn,
                )

            s = self.conn.table("core_skjemadata_mapped")
            s = (
                s.filter(_.aar == aar)
                .filter(_.ident == orgnr_foretak)
                .filter(_.refnr.isin(active_no_duplicates_refnr_list(self.conn)))
                .filter(_.variabel == "naeringskode")
                .select(["ident", "refnr", "verdi"])
                .to_pandas()
            )
            s = s.rename(columns={"ident": "orgnr", "verdi": "naeringskode"})
            s = s.drop_duplicates(subset="orgnr")
            df = df.merge(s, how="left", on="orgnr")

            e = self.conn.table("enhetsinfo")
            e = (
                e.filter(_.aar == aar)
                .filter(_.ident == orgnr_foretak)
                .filter(_.variabel == "nace_2007")
                .select(["ident", "verdi"])
                .to_pandas()
            )
            e = e.rename(columns={"ident": "orgnr", "verdi": "nace_2007"})
            e = e.drop_duplicates(subset="orgnr")
            df = df.merge(e, how="left", on="orgnr")

            df["sn07_et"] = None
            df["sn25_et"] = None
            df["fritekst"] = ""
            df["kilde"] = ""
            if "sn07_1" not in df.columns:
                df["sn07_1"] = None
            if "sn2025_1" not in df.columns:
                df["sn2025_1"] = None
            if "sn2025_1_gdato" not in df.columns:
                df["sn2025_1_gdato"] = None
            if "naeringskode" not in df.columns:
                df["naeringskode"] = None
            if "nace_2007" not in df.columns:
                df["nace_2007"] = None

            df = self._enrich_naring_names(df)

            df["edited_cells"] = [{}  for _ in range(len(df))]

            return df.to_dict("records")

        # 2. Display foretak grid - fires on store change OR checklist change (no data fetching)
        @callback(
            Output("meldingsbasen-foretak-grid", "rowData", allow_duplicate=True),
            Output("meldingsbasen-foretak-grid", "columnDefs", allow_duplicate=True),
            Output("meldingsbasen-foretak-omsetning-card", "value"),
            Output("meldingsbasen-foretak-ansatte-card", "value"),
            Input("meldingsbasen-foretak-store", "data"),
            Input("meldingsbasen-checklist", "value"),
            prevent_initial_call=True,
        )
        def show_foretak_grid(store_data, vis_kolonner):
            if not store_data:
                raise PreventUpdate

            skjemadata = "skjemadata" in vis_kolonner
            enhetsinfo = "enhetsinfo" in vis_kolonner

            df = pd.DataFrame(store_data)

            cols = SELECT_COLUMNS_FORETAK.copy()
            if skjemadata:
                cols.append("naeringskode")
            if enhetsinfo:
                cols.append("nace_2007")
            cols = [c for c in cols if c in df.columns]
            df = df[cols]

            df["sn2025_1_gdato"] = pd.to_datetime(
                df["sn2025_1_gdato"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            omsetning = store_data[0].get("omsetning", "")
            antall_ansatte = store_data[0].get("antall_ansatte", "")

            bof_children = [
                {"field": "orgnr", "headerName": "orgnr"},
                {"field": "org_form", "headerName": "org_form"},
                {"field": "navn", "headerName": "navn"},
                {"field": "sn07_1", "headerName": "sn07_1",
                "cellRenderer": "DropdownRenderer",
                "editable": False,
                "cellRendererParams": {
                    "optionsField": "sn07_options",
                    "valueField": "code",
                    "labelField": "name",
                }
                },
                {
                    "field": "sn07_navn",
                    "headerName": "sn07 navn",
                    "editable": False,
                    "wrapText": True,
                    "width": 600,
                    "autoHeight": True,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
                {
                    "field": "sn07_et",
                    "headerName": "sn07_et",
                    "editable": True,
                    "cellRenderer": "DropdownRenderer",
                    "cellRendererParams": {"values": ["endring", "korreksjon"]},
                },
                {"field": "sn2025_1", "headerName": "sn2025_1", "editable": True},
                {
                    "field": "sn2025_navn",
                    "headerName": "sn2025 navn",
                    "editable": False,
                    "wrapText": True,
                    "width": 600,
                    "autoHeight": True,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
                {
                    "field": "sn25_et",
                    "headerName": "sn25_et",
                    "editable": True,
                    "cellRenderer": "DropdownRenderer",
                    "cellRendererParams": {"values": ["endring", "korreksjon"]},
                },
                {
                    "field": "sn2025_1_gdato",
                    "headerName": "sn2025_1_gdato",
                    "editable": True,
                    "singleClickEdit": True,
                    "width": 300,
                },
                {
                    "field": "fritekst",
                    "headerName": "fritekst",
                    "editable": True,
                    "wrapText": True,
                    "width": 600,
                    "autoHeight": True,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
            ]
            column_defs = [{"headerName": "BoF", "children": bof_children}]
            if skjemadata:
                column_defs.append(
                    {
                        "headerName": "Altinn3",
                        "children": [
                            {"field": "naeringskode", "headerName": "naeringskode"}
                        ],
                    }
                )
            if enhetsinfo:
                column_defs.append(
                    {
                        "headerName": "Enhetsinfo",
                        "children": [{"field": "nace_2007", "headerName": "nace_2007"}],
                    }
                )

            return df.to_dict("records"), column_defs, omsetning, antall_ansatte

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

            refnr = foretak_store[0].get("refnr", "")
            omsetning = foretak_store[0].get("omsetning", "")
            antall_ansatte = foretak_store[0].get("antall_ansatte", "")
            foretaks_nr = foretak_store[0].get("foretaks_nr", "")

            with sqlite3.connect(SSB_BEDRIFT_PATH) as conn:
                df = pd.read_sql_query(
                    f"""SELECT orgnr, navn, sn07_1, sn07_1_rdato, sn07_1_gdato, sn2025_1, sn2025_2, sn2025_3, sn2025_1_rdato, sn2025_1_gdato, org_form FROM ssb_bedrift WHERE foretaks_nr = '{foretaks_nr}';""",
                    conn,
                )
            if refnr:
                s = self.conn.table("core_skjemadata_mapped")
                s = (
                    s.filter(_.aar == aar)
                    .filter(_.refnr == refnr)
                    .filter(_.variabel == "virkNaeringskode")
                    .select(["ident", "verdi"])
                    .to_pandas()
                )
                s = s.rename(columns={"ident": "orgnr", "verdi": "virkNaeringskode"})
                s = s.drop_duplicates(subset="orgnr")
                df = df.merge(s, how="left", on="orgnr")

            e = self.conn.table("enhetsinfo")
            e = (
                e.filter(_.aar == aar)
                .filter(_.foretak == orgnr_foretak)
                .filter(_.variabel == "nace_2007")
                .select(["ident", "verdi"])
                .to_pandas()
            )
            e = e.rename(columns={"ident": "orgnr", "verdi": "nace_2007"})
            e = e.drop_duplicates(subset="orgnr")

            df = df.merge(e, how="left", on="orgnr")

            df["omsetning_f"] = omsetning  # fra foretak
            df["antall_ansatte_f"] = antall_ansatte  # fra foretak
            df["sn07_et"] = None
            df["sn25_et"] = None
            df["fritekst"] = ""
            df["kilde"] = ""
            if "sn07_1" not in df.columns:
                df["sn07_1"] = None
            if "sn2025_1" not in df.columns:
                df["sn2025_1"] = None
            if "sn2025_1_gdato" not in df.columns:
                df["sn2025_1_gdato"] = None
            if "virkNaeringskode" not in df.columns:
                df["virkNaeringskode"] = None
            if "nace_2007" not in df.columns:
                df["nace_2007"] = None

            if orgnr_bedrift:
                df = df.sort_values(
                    by="orgnr",
                    key=lambda x: x.map(lambda v: 0 if v == orgnr_bedrift else 1),
                )

            df = self._enrich_naring_names(df)

            df["edited_cells"] = [{}  for _ in range(len(df))]

            return df.to_dict("records")

        # 4. Display bedrift grid - fires on store change OR checklist change (no data fetching)
        @callback(
            Output("meldingsbasen-bedrift-grid", "rowData", allow_duplicate=True),
            Output("meldingsbasen-bedrift-grid", "columnDefs", allow_duplicate=True),
            Input("meldingsbasen-bedrift-store", "data"),
            Input("meldingsbasen-checklist", "value"),
            prevent_initial_call=True,
        )
        def show_bedrift_grid(store_data, vis_kolonner):
            if not store_data:
                raise PreventUpdate

            skjemadata = "skjemadata" in vis_kolonner
            enhetsinfo = "enhetsinfo" in vis_kolonner

            df = pd.DataFrame(store_data)

            cols = SELECT_COLUMNS_BEDRIFT.copy()
            if skjemadata:
                cols.append("virkNaeringskode")
            if enhetsinfo:
                cols.append("nace_2007")
            cols = [c for c in cols if c in df.columns]
            df = df[cols]

            df["sn2025_1_gdato"] = pd.to_datetime(
                df["sn2025_1_gdato"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            bof_children = [
                {"field": "orgnr", "headerName": "orgnr"},
                {"field": "org_form", "headerName": "org_form"},
                {"field": "navn", "headerName": "navn"},
                {"field": "sn07_1", "headerName": "sn07_1",
                "cellRenderer": "DropdownRenderer",
                "editable": False,
                "cellRendererParams": {
                    "optionsField": "sn07_options",
                    "valueField": "code",
                    "labelField": "name",
                }
                },
                {
                    "field": "sn07_navn",
                    "headerName": "sn07 navn",
                    "editable": False,
                    "wrapText": True,
                    "autoHeight": True,
                    "width": 600,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
                {
                    "field": "sn07_et",
                    "headerName": "sn07_et",
                    "editable": True,
                    "cellRenderer": "DropdownRenderer",
                    "cellRendererParams": {"values": ["endring", "korreksjon"]},
                },
                {"field": "sn2025_1", "headerName": "sn2025_1", "editable": True},
                {
                    "field": "sn2025_navn",
                    "headerName": "sn2025 navn",
                    "editable": False,
                    "wrapText": True,
                    "autoHeight": True,
                    "width": 600,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
                {
                    "field": "sn25_et",
                    "headerName": "sn25_et",
                    "editable": True,
                    "cellRenderer": "DropdownRenderer",
                    "cellRendererParams": {"values": ["endring", "korreksjon"]},
                },
                {
                    "field": "sn2025_1_gdato",
                    "headerName": "sn2025_1_gdato",
                    "editable": True,
                    "singleClickEdit": True,
                    "width": 300,
                },
                {
                    "field": "fritekst",
                    "headerName": "fritekst",
                    "editable": True,
                    "wrapText": True,
                    "width": 600,
                    "autoHeight": True,
                    # "cellStyle": {"whiteSpace": "normal"},
                },
            ]
            column_defs = [{"headerName": "BoF", "children": bof_children}]
            if skjemadata:
                column_defs.append(
                    {
                        "headerName": "Altinn3",
                        "children": [
                            {
                                "field": "virkNaeringskode",
                                "headerName": "virkNaeringskode",
                            }
                        ],
                    }
                )
            if enhetsinfo:
                column_defs.append(
                    {
                        "headerName": "Enhetsinfo",
                        "children": [{"field": "nace_2007", "headerName": "nace_2007"}],
                    }
                )

            return df.to_dict("records"), column_defs

        @callback(
            Output("meldingsbasen-bedrift-grid", "rowData", allow_duplicate=True),
            Output("meldingsbasen-bedrift-grid", "columnDefs", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input("meldingsbasen-bedrift-grid", "cellValueChanged"),
            State("meldingsbasen-bedrift-grid", "rowData"),
            State("meldingsbasen-bedrift-grid", "columnDefs"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def edit_bedrift(edited, rows, column_defs, alert_store):
            """
            Tracks edits in bedrift-grid, updates cells accordingly, depending on edited column.
            """
            alert_store = alert_store or []
            edited_col = edited[0]["colId"]
            
            if edited_col not in ("sn2025_1", "sn07_1", "sn2025_1_gdato", "sn07_et", "sn25_et", "fritekst"):
                raise PreventUpdate

            orgnr = edited[0]["data"]["orgnr"]
            
            rows, column_defs, alert_store = self._edit_tracking(edited, edited_col, orgnr, rows, column_defs, alert_store)
            print(rows)
            return rows, column_defs, alert_store

        @callback(
            Output("meldingsbasen-foretak-grid", "rowData", allow_duplicate=True),
            Output("meldingsbasen-foretak-grid", "columnDefs", allow_duplicate=True),
            Output("alert_store", "data", allow_duplicate=True),
            Input("meldingsbasen-foretak-grid", "cellValueChanged"),
            State("meldingsbasen-foretak-grid", "rowData"),
            State("meldingsbasen-foretak-grid", "columnDefs"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def edit_foretak(edited, rows, column_defs, alert_store):
            """
            Tracks edits in foretak-grid, updates cells accordingly, depending on edited column.
            """
            alert_store = alert_store or []
            edited_col = edited[0]["colId"]
            
            if edited_col not in ("sn2025_1", "sn07_1", "sn2025_1_gdato", "sn07_et", "sn25_et", "fritekst"):
                raise PreventUpdate

            orgnr = edited[0]["data"]["orgnr"]
            
            rows, column_defs, alert_store = self._edit_tracking(edited, edited_col, orgnr, rows, column_defs, alert_store)
            print(rows)
            
            return rows, column_defs, alert_store

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input("meldingsbasen-save-edits-button1", "n_clicks"),
            State("meldingsbasen-foretak-grid", "rowData"),
            State("meldingsbasen-bedrift-grid", "rowData"),
            State("alert_store", "data"),
            State("var-aar", "value"),
            prevent_initial_call=True,
        )
        def save_edits(n_clicks, foretak_rows, bedrift_rows, alert_store, aar):
            if not n_clicks:
                raise PreventUpdate

            alert_store = alert_store or []
            timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

            edited_foretak = [r for r in (foretak_rows or []) if r.get("edited_cells")]
            edited_bedrift = [r for r in (bedrift_rows or []) if r.get("edited_cells")]

            # necessary fields for meldingsbasen
            necessary_fields = ["orgnr", "org_form", "sn07_1", "sn07_dat", "sn07_et", "kilde", "fritekst", "sn2025_1", "sn2025_2", "sn2025_3", "sn25_dat", "sn25_et"]

            if not edited_foretak and not edited_bedrift:
                alert_store = [
                    create_alert("Ingen endringer å sende!", "warning", ephemeral=True, duration=4),
                    *alert_store,
                ]
                return alert_store

            output_lines = [f"=== Oppdateringer sendt: {timestamp} ===\n"]

            for row in edited_foretak:
                edited_cols = row.get("edited_cells", {})
                output_lines.append(f"FORETAK {row['orgnr']}:")
                for col in edited_cols:
                    for field in necessary_fields:
                        output_lines.append(f"  {col}: {row.get(field)}")
                output_lines.append("")

            for row in edited_bedrift:
                edited_cols = row.get("edited_cells", {})
                output_lines.append(f"BEDRIFT {row['orgnr']}:")
                for col in edited_cols:
                    for field in necessary_fields:
                        output_lines.append(f"  {col}: {row.get(field)}")
                output_lines.append("")

            file_path = f"/buckets/frasky/naringer/naringsendringer_til_bof/p{aar}/naringsendringer_p{timestamp}_v1.txt"

            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n".join(output_lines))
                f.write("\n")

            alert_store = [
                create_alert(
                    f"Oppdateringer sendt! {len(edited_foretak)} foretak, {len(edited_bedrift)} bedrifter.",
                    "success", ephemeral=True, duration=6,
                ),
                *alert_store,
            ]
            return alert_store


class MeldingsbasenTab(TabImplementation, Meldingsbasen):
    """MeldingsbasenTab is an implementation of the Meldingsbasen module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the MeldingsbasenTab class."""
        Meldingsbasen.__init__(
            self,
            time_units=time_units,
            conn=conn,
        )
        TabImplementation.__init__(self)


class MeldingsbasenWindow(WindowImplementation, Meldingsbasen):
    """MeldingsbasenWindow is an implementation of the Meldingsbasen module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], conn: object) -> None:
        """Initializes the MeldingsbasenWindow class."""
        Meldingsbasen.__init__(self, time_units=time_units, conn=conn)
        WindowImplementation.__init__(self)
