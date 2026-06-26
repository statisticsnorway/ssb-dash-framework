import logging
from typing import Any
import dash_ag_grid as dag
import pandas as pd
import tzlocal
from dash import Input
from dash import Output
from dash import callback
from dash import html
from ibis import _
from psycopg_pool import ConnectionPool
import dash_bootstrap_components as dbc
from dash import dcc

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from ssb_dash_framework.utils.config_tools.set_variables import get_ident
from ssb_dash_framework.utils.core_query_functions import create_filter_dict, ibis_filter_with_dict

from  ssb_dash_framework.utils.config_tools.connection import _get_connection_object
from  ssb_dash_framework.utils.config_tools.connection import get_connection
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

    def create_info_card(self, title: str, component_id: str, var_type: str):
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
                                width=2,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="Kontaktperson",
                                    component_id="dataeditor-kontaktinfo-card-kontaktperson",
                                    var_type="number",
                                ),
                                width=2,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="E-post",
                                    component_id="dataeditor-kontaktinfo-card-epost",
                                    var_type="text",
                                ),
                                width=2,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="Telefon",
                                    component_id="dataeditor-kontaktinfo-card-tlf",
                                    var_type="text",
                                ),
                                width=2,
                            ),
                        ],
                        className="g-2 align-items-end",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                self.create_info_card(
                                    title="Kommentar kontaktinfo",
                                    component_id="dataeditor-kontaktinfo-card-kommentar",
                                    var_type="text",
                                ),
                                width=2,
                            ),
                            dbc.Col(
                                self.create_info_card(
                                    title="Kommentar krevende",
                                    component_id="dataeditor-kontaktinfo-card-krevende",
                                    var_type="text",
                                ),
                                width=2,
                            ),
                        ],
                        className="g-2 align-items-end",
                    ),
                ]
            ),
            className=f"{self.module_name}-body",
        )

    def module_callbacks(self):
        connection_object = _get_connection_object()
        variableselector = VariableSelector(
            selected_inputs=["ident", *get_time_units().keys()],
            selected_states=[],
        )

        @callback(
            Output(
                component_id="dataeditor-kontaktinfo-card-organisasjonsnummer",
                component_property="value",
            ),
            Output(component_id="dataeditor-kontaktinfo-card-skjema", component_property="value"),
            Output(
                component_id="dataeditor-kontaktinfo-card-kontaktperson",
                component_property="value",
            ),
            Output(
                component_id="dataeditor-kontaktinfo-card-epost", component_property="value"
            ),
            Output(component_id="dataeditor-kontaktinfo-card-tlf", component_property="value"),
            Output(component_id="dataeditor-kontaktinfo-card-kommentar", component_property="value"),
            Output(
                component_id="dataeditor-kontaktinfo-card-krevende", component_property="value"
            ),
            variableselector.get_input(get_ident()),
            *[variableselector.get_input(unit) for unit in get_time_units().keys()],

        )
        def create_info_cards_kontaktinfo(ident: str, *args: Any) -> tuple[str, str, str, str, str, str, str]:
            """Returns a tuple of strings with the values for info cards for the kontaktinfo module in DataEditor.
            These cards will hold kontaktinfo foretak.
            """
            time_unit_list = [x for x in get_time_units().keys()]
            time_units = args[: len(time_unit_list)]
            print(time_units)

            filter_dict = create_filter_dict(time_unit_list, time_units)
            print(filter_dict)

            if isinstance(connection_object, ConnectionPool):
                logger.debug("Using ConnectionPool logic.")
                with get_connection(necessary_tables=["kontaktinfo"]) as conn:
                    t = conn.table("kontaktinfo")
                    data = t.filter(_.ident == ident).filter(
                            ibis_filter_with_dict(filter_dict)
                        ).execute()
                print(data)

                orgnr = data["ident"].iloc[0]
                skjema = data["skjema"].iloc[0]
                kontaktperson = data["kontaktperson"].iloc[0]
                epost = data["epost"].iloc[0]
                tlf = data["telefon"].iloc[0]
                kommentar_kontaktinfo = data["kommentar_kontaktinfo"].iloc[0]
                kommentar_krevende = data["kommentar_krevende"].iloc[0]

                return (
                    orgnr,
                    skjema,
                    kontaktperson,
                    epost,
                    tlf,
                    kommentar_kontaktinfo,
                    kommentar_krevende,
                )

            else:
                raise NotImplementedError(
                    f"Connection of type {type(connection_object)} is not currently supported."
                )
