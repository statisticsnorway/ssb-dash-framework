import logging
from abc import ABC
from abc import abstractmethod
from pathlib import Path
import json
import ibis
from ibis import _
from dash import callback_context as ctx

from dash import html, Output, callback, dcc, Input, State
from dash.exceptions import PreventUpdate
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from ..setup.variableselector import VariableSelector
from ..utils.module_validation import module_validator
from ..utils.implementations import TabImplementation
from ..utils.implementations import WindowImplementation
from ..utils.core_query_functions import ibis_filter_with_dict
from ..utils.alert_handler import create_alert
from ..utils.functions import get_config_path

logger = logging.getLogger(__name__)

logger.warning("This module is under development and might have many drastic changes.")

def set_time_units(): ...


def get_time_units():
    return ...


class Bedriftstabell(ABC):
    _id_number: int = 0
    _required_variables = ["altinnskjema"]

    def __init__(
        self,
        table_name,
        conn,
    ):
        self.module_number = Bedriftstabell._id_number
        self.module_name = self.__class__.__name__
        Bedriftstabell._id_number += 1
        self.icon = "?"
        self.label = "Bedriftstabell"
        self.conn = conn
        self.variableselector = VariableSelector(
            selected_inputs=["altinnskjema", "ident"],
            selected_states=["aar"],
        )
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _make_card(self, variable, value):
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(variable, className="card-title"),
                        html.P(
                            value,
                            className="card-text",
                        ),
                    ]
                ),
            ],
            className="bedrift-card",
        )

    def _create_layout(self):
        settings_modal = html.Div(
            [
                dbc.Button(
                    "Innstillinger",
                    id=f"{self.module_number}-bedriftstabell-settings-button",
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                [
                                    "Innstillinger",
                                    dbc.Col(
                                        dbc.Button(
                                            "Lagre innstillinger",
                                            id=f"{self.module_number}-bedriftstabell-settings-save",
                                        )
                                    ),
                                ]
                            )
                        ),
                        dbc.ModalBody(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Row("Kolonner som skal vises"),
                                            dbc.Row(
                                                dcc.Checklist(
                                                    id=f"{self.module_number}-bedriftstabell-columns-checklist"
                                                )
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Row("Andre valg"),
                                            dbc.Row(
                                                dcc.Checklist(
                                                    id=f"{self.module_number}-bedriftstabell-others-checklist",
                                                    options=["Fjorårsdata"],
                                                )
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ),
                    ],
                    id=f"{self.module_number}-bedriftstabell-settings-modal",
                    is_open=False,
                ),
            ]
        )

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Hent tabell (igjen)",
                                id=f"{self.module_number}-bedriftstabell-settings-run",
                            )
                        ),
                        dbc.Col(settings_modal),
                    ],
                    justify="between",
                ),
                html.Hr(),
                dbc.Row(id=f"{self.module_number}-bedriftstabell-showing"),
                html.Hr(),
                dbc.Row(dbc.Col(dag.AgGrid(id=f"{self.module_number}-bedriftstabell"))),
            ],
            fluid=True,
        )

    @abstractmethod
    def layout():
        pass

    def _get_settings(self, skjemanummer):
        try:
            config_path = Path(
                f"{get_config_path(module_name='bedriftstabell')}/{skjemanummer}.json"
            )
            with config_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as e:
            return None

    def module_callbacks(self):
        @callback(
            Output(f"{self.module_number}-bedriftstabell-columns-checklist", "value"),
            Output(f"{self.module_number}-bedriftstabell-others-checklist", "value"),
            self.variableselector.get_input("altinnskjema"),
        )
        def retrieve_settings_for_form(skjema):
            config = self._get_settings(skjema)
            if config is not None:
                return config["columns_to_show"], config["other_options"]
            else:
                return None, None

        @callback(
            Output(f"{self.module_number}-bedriftstabell-settings-modal", "is_open"),
            Input(f"{self.module_number}-bedriftstabell-settings-button", "n_clicks"),
        )
        def bedrift_open_settings(click):
            if click:
                return True
            return False

        @callback(
            Output(f"{self.module_number}-bedriftstabell-columns-checklist", "options"),
            Input(f"{self.module_number}-bedriftstabell-settings-button", "n_clicks"),
            Input(f"{self.module_number}-bedriftstabell", "columnDefs"),
        )
        def checklist_get_column_options(n_click, columndefs):
            if columndefs:
                return [x["field"] for x in columndefs]
            else:
                return ["No data in table"]

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-bedriftstabell-settings-save", "n_clicks"),
            State("alert_store", "data"),
            State(f"{self.module_number}-bedriftstabell-columns-checklist", "value"),
            State(f"{self.module_number}-bedriftstabell-others-checklist", "value"),
            self.variableselector.get_state("altinnskjema"),
            prevent_initial_call=True,
        )
        def bedrift_save_settings(
            click, alert_store, selected_columns, selected_options, skjemanummer
        ):
            if not click:
                raise PreventUpdate
            if skjemanummer == "":
                raise PreventUpdate
            config_path = get_config_path(module_name="bedriftstabell")
            with open(f"{config_path}/{skjemanummer}.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "columns_to_show": selected_columns if selected_columns else [],
                        "other_options": selected_options if selected_options else [],
                    },
                    f,
                    indent=4,
                )
            return [
                create_alert(
                    f"Lagret innstillinger for {skjemanummer}.",
                    "info",
                    ephemeral=True,
                ),
                *alert_store,
            ]

        @callback(
            Output(f"{self.module_number}-bedriftstabell", "rowData"),
            Output(f"{self.module_number}-bedriftstabell", "columnDefs"),
            Output(f"{self.module_number}-bedriftstabell-showing", "children"),
            Input(f"{self.module_number}-bedriftstabell-settings-run", "n_clicks"),
            self.variableselector.get_input("altinnskjema"),
            self.variableselector.get_input("ident"),
            State(f"{self.module_number}-bedriftstabell-columns-checklist", "value"),
            *self.variableselector.get_all_callback_objects(),
            prevent_initial_call=True,
        )
        def bedriftstabell_get_data(run_click, skjema, ident, columns_to_show, *args):
            print("bedriftstabell args:", args)
            print("varselectorbedrift: ", self.variableselector.selected_variables)

            f = self.conn.table("foretak")
            foretak = list(f.to_pandas()["orgnr_foretak"].unique())
            if ident not in foretak:
                print("Raising PreventUpdate")
                raise PreventUpdate
            key_map = {"altinnskjema": "skjema", "ident": "orgnr_foretak"}

            filterdict = {
                key_map.get(key, key): value
                for key, value in zip(self.variableselector.selected_variables, args)
            }
            print("filterdict ", filterdict)

            b = self.conn.table("skjemadata_bedriftstabell")
            b = b.join(f, b.ident == f.orgnr_bedrift)
            b = b.filter(ibis_filter_with_dict(filterdict))

            df = b.to_pandas()
            print("shape: ", df.shape)
            if columns_to_show is None:
                columns_to_show = [col for col in df.columns]
            print("columns_to_show: ", columns_to_show)
            return (
                df.to_dict("records"),
                [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": (
                            True
                            if col in ["row_id", "row_ids"]
                            or col not in columns_to_show
                            else False
                        ),
                    }
                    for col in df.columns
                ],
                [
                    dbc.Col(self._make_card(variable=key, value=value))
                    for key, value in filterdict.items()
                ],
            )


class BedriftstabellTab(TabImplementation, Bedriftstabell):

    def __init__(self, table_name, conn) -> None:

        Bedriftstabell.__init__(self, table_name, conn)
        TabImplementation.__init__(self)


class BedriftstabellWindow(WindowImplementation, Bedriftstabell):

    def __init__(self, table_name, conn) -> None:

        Bedriftstabell.__init__(self, table_name, conn)
        WindowImplementation.__init__(
            self,
        )
