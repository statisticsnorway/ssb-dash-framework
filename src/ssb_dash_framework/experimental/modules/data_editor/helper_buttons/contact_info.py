import logging
from typing import Any
import dash_ag_grid as dag
import pandas as pd
import tzlocal
from dash import Input
from dash import Output
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate
from ibis import _
from psycopg_pool import ConnectionPool
import dash_bootstrap_components as dbc
from dash import dcc

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from ssb_dash_framework.utils.config_tools.set_variables import get_ident
from ssb_dash_framework.utils.core_query_functions import (
    create_filter_dict,
    ibis_filter_with_dict,
)

from ssb_dash_framework.utils.config_tools.connection import _get_connection_object
from ssb_dash_framework.utils.config_tools.connection import get_connection
from ..core import DataEditorHelperButton

logger = logging.getLogger(__name__)

local_tz = tzlocal.get_localzone()


class DataEditorContactInfo(DataEditorHelperButton):
    """This module provides supporting tables for the DataEditor.

    It adds a button that opens a modal with contact info for the delivered Altinn 3 survey.
    """

    _id_number = 0

    def __init__(
        self,
        applies_to_tables: list[str] | None = None,
        applies_to_forms: list[str] | None = None,
    ) -> None:
        """Initializes the DataEditorContactInfo module."""
        self.module_number = DataEditorContactInfo._id_number
        self.module_name = self.__class__.__name__
        DataEditorContactInfo._id_number += 1
        self.variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[get_refnr(), *[x for x in get_time_units().keys()]],
        )
        self.modal_body = self._create_modal_body()

        super().__init__(label="Kontaktinfo")

        self.module_callbacks()

    def create_info_card(
        self, title: str, component_id: str, var_type: str | int, style: dict | None = None
    ):
        card_info = html.Div(
            className="ssb-input",
            children=[
                html.Label(title),
                html.Div(
                    className="input-wrapper",
                    children=[
                        dbc.Input(
                            id=component_id,
                            type=var_type,
                            style=style,
                            readonly=True,
                        )
                    ],
                ),
            ],
        )
        return card_info

    def _create_modal_body(self) -> html.Div:
        return html.Div(
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                self.create_info_card(
                                    title="Organisasjonsnummer",
                                    component_id="dataeditor-kontaktinfo-card-organisasjonsnummer",
                                    var_type="text",
                                ),
                                width=2,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="Skjema",
                                    component_id="dataeditor-kontaktinfo-card-skjema",
                                    var_type="text",
                                ),
                                width=1,
                            ),
                            
                            dbc.Col(
                                self.create_info_card(
                                    title="Kontaktperson",
                                    component_id="dataeditor-kontaktinfo-card-kontaktperson",
                                    var_type="text",
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="E-post",
                                    component_id="dataeditor-kontaktinfo-card-epost",
                                    var_type="text",
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="Telefon",
                                    component_id="dataeditor-kontaktinfo-card-tlf",
                                    var_type="text",
                                ),
                                width=1,
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Label(
                                            "Kontaktinfo bekreftet?",
                                            style={"visibility": "visible"},
                                        ),
                                        html.Div(
                                            className="ssb-checkbox d-flex align-items-center",
                                            children=[
                                                dcc.Checklist(
                                                    id="dataeditor-kontaktinfo-bekreftet",
                                                    options=[
                                                        {"label": "", "value": "1", "disabled": True}
                                                    ],
                                                    value=[],
                                                ),
                                            ],
                                            style={"height": "44px"},
                                        ),
                                    ],
                                    className="ssb-input",
                                ),
                                width=2,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Generell kommentar",
                                        className="ssb-input",
                                    ),
                                    dbc.Textarea(
                                        id="dataeditor-kontaktinfo-card-kommentar",
                                        className="microlayout-textarea-field",
                                        readonly=True,
                                    ),
                                ],
                                className="microlayout-textarea",
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Kommentar krevende",
                                        className="ssb-input",
                                    ),
                                    dbc.Textarea(
                                        id="dataeditor-kontaktinfo-card-krevende",
                                        className="microlayout-textarea-field",
                                        readonly=True,
                                    ),
                                ],
                                className="microlayout-textarea",
                            ),
                        ],
                        className="mb-2",
                    ),
                ],
                className=f"{self.module_name}-body",
            ),
        )

    def module_callbacks(self):
        connection_object = _get_connection_object()
        variableselector = VariableSelector(
            selected_inputs=["refnr"],
            selected_states=[],
        )

        @callback(
            Output(
                component_id="dataeditor-kontaktinfo-card-organisasjonsnummer",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-skjema",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-kontaktperson",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-epost",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-tlf",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-bekreftet",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-kommentar",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-krevende",
                component_property="value",
            ),
            Output(
                component_id=f"{self.module_name}-{self.module_number}-indicator",
                component_property="style",
            ),
            Output(
                component_id=f"{self.module_name}-{self.module_number}-indicator",
                component_property="children",
            ),
            variableselector.get_input(get_refnr()),
        )
        def create_info_cards_kontaktinfo(
            refnr: str,
        ) -> tuple[str, str, str, str, str, list[str], str, str, dict[str, str], str]:
            """Returns a tuple of strings with the values for info cards for the kontaktinfo module in DataEditor.
            These cards will hold kontaktinfo foretak.
            """
            if not refnr:
                raise PreventUpdate

            if isinstance(connection_object, ConnectionPool):
                logger.debug("Using ConnectionPool logic.")
                with get_connection(necessary_tables=["kontaktinfo"]) as conn:
                    t = conn.table("kontaktinfo")
                    data = t.filter(_.refnr == refnr).execute()

                orgnr = data["ident"].item()
                skjema = data["skjema"].item()
                kontaktperson = data["kontaktperson"].item()
                epost = data["epost"].item()
                tlf = data["telefon"].item()
                bekreftet = data["bekreftet_kontaktinfo"].item()
                kommentar_kontaktinfo = data["kommentar_kontaktinfo"].item()
                kommentar_krevende = data["kommentar_krevende"].item()
                comment_count = sum(
                    [
                        bool(kommentar_kontaktinfo),
                        bool(kommentar_krevende),
                    ]
                )
                indicator_style = (
                    {"display": "block"} if comment_count > 0 else {"display": "none"}
                )
                print(f"comment_count: {comment_count}")

                return (
                    orgnr,
                    skjema,
                    kontaktperson,
                    epost,
                    tlf,
                    [bekreftet] if bekreftet else [],
                    kommentar_kontaktinfo,
                    kommentar_krevende,
                    indicator_style,
                    str(comment_count) if comment_count > 0 else "",
                )

            else:
                raise NotImplementedError(
                    f"Connection of type {type(connection_object)} is not currently supported."
                )
