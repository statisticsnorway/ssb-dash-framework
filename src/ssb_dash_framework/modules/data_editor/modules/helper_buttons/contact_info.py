import logging
from ssb_dash_framework.modules.data_editor.modules.helper_buttons.meta import (
    ContactInfo,
)
from typing import Any
import pandas as pd
from dash import Input, no_update
from dash import Output
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate
from ibis import _

import dash_bootstrap_components as dbc
from dash import dcc
from .....utils.alert_handler import AlertHandler

from .....setup.variableselector import VariableSelector
from .editor_helper_button import DataEditorHelperButton
from .meta import ContactInfo

logger = logging.getLogger(__name__)


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
        self.modal_body = self._create_modal_body()

        super().__init__(label="Kontaktinfo")

        self.module_callbacks()

    def create_info_card(
        self,
        title: str,
        component_id: str,
        var_type: str | int,
        style: dict | None = None,
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
                                                        {
                                                            "label": "",
                                                            "value": "1",
                                                            "disabled": True,
                                                        }
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
            inputs={"refnr": VariableSelector.get_refnr(Input)},
        )
        def create_info_cards_kontaktinfo(
            refnr: str,
        ) -> tuple[str, str, str, str, str, list[str], str, str, dict[str, str], str]:
            """Returns a tuple of strings with the values for info cards for the kontaktinfo module in DataEditor.
            These cards will hold kontaktinfo foretak.
            """
            if not refnr:
                raise PreventUpdate

            try:
                info: ContactInfo = self.fetcher.get_contact_info(
                    refnr
                )  # pyright: ignore

            except Exception as e:
                msg = f"Getting contact info failed with error: {e}"
                logger.exception(msg)
                AlertHandler.warning(msg)
                info = ContactInfo.empty()

            comment_count = sum(
                [
                    bool(info.kommentar_kontaktinfo),
                    bool(info.kommentar_krevende),
                ]
            )
            indicator_style = (
                {"display": "block"} if comment_count > 0 else {"display": "none"}
            )

            return (
                info.ident,
                info.skjema,
                info.kontaktperson,
                info.epost,
                info.telefon,
                [info.bekreftet_kontaktinfo] if info.bekreftet_kontaktinfo else [],
                info.kommentar_kontaktinfo,
                info.kommentar_krevende,
                indicator_style,
                str(comment_count) if comment_count > 0 else "",
            )
