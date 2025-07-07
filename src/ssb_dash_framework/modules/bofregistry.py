import logging
import sqlite3
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)

SSB_FORETAK_PATH = "/buckets/shared/vof/oracle-hns/ssb_foretak.db"
SSB_BEDRIFT_PATH = "/buckets/shared/vof/oracle-hns/ssb_bedrift.db"


def ssb_foretak_modal() -> dbc.Modal:
    """Create a modal for displaying bof data.

    Returns:
        dbc.Modal: A modal component containing an AgGrid table for bof data.
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("ssb_foretak")),
            dbc.ModalBody(
                [
                    dag.AgGrid(
                        id="bofregistry-ssb_foretak-table",
                        className="ag-theme-alpine-dark header-style-on-filter bofregistry-modal-aggrid",
                        defaultColDef={
                            "editable": True,
                            "filter": True,
                            "resizable": True,
                            "floatingFilter": True,
                        },
                        columnSize="responsiveSizeToFit",
                    )
                ],
                className="flex-grow-1 p-0 bofregistry-modal-body",
            ),
        ],
        id="bofregistry-modal-ssb_foretak",
        is_open=False,
        size="xl",
        scrollable=True,
        className="d-flex flex-column bofregistry-modal",
    )


def ssb_bedrift_modal() -> dbc.Modal:
    """Create a modal for displaying bof data.

    Returns:
        dbc.Modal: A modal component containing an AgGrid table for bof data.
    """
    ssb_bedrift_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("ssb_bedrift")),
            dbc.ModalBody(
                [
                    dag.AgGrid(
                        id="bofregistry-ssb_bedrift-table",
                        className="ag-theme-alpine-dark header-style-on-filter bofregistry-modal-aggrid",
                        defaultColDef={
                            "editable": True,
                            "filter": True,
                            "resizable": True,
                            "floatingFilter": True,
                        },
                        columnSize="responsiveSizeToFit",
                    )
                ],
                className="flex-grow-1 p-0 bofregistry-modal-body",
            ),
        ],
        id="bofregistry-modal-ssb_bedrift",
        is_open=False,
        size="xl",
        scrollable=True,
        className="d-flex flex-column bofregistry-modal",
    )
    return ssb_bedrift_modal


class BofInformation(ABC):
    """Module for displaying and managing information from BoF.

    This component:
    - Displays detailed information about selected foretak using cards and ag-grids.
    - Interacts with sqlite files to display information for the currently selected foretak.
    - The sqlite files can be accessed from the oracle-hns shared bucket from the vof team.

    Attributes:
        label (str): Label for the tab, displayed as "🗃️ BoF Foretak".

    Methods:
        generate_card(title, component_id, var_type): Generates a Dash Bootstrap card for displaying information.
        layout(): Abstract method, needs to generate the layout for the BoF Foretak module.
        callbacks(): Registers Dash callbacks for handling user interactions.
    """

    _id_number: int = 0

    def __init__(
        self,
        label: str | None = None,
        variableselector_foretak_name: str | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the BofInformation tab component.

        Args:
            label (str): The label for the tab, displayed as "🗃️ BoF Foretak".
            variableselector_foretak_name (str): The name of the variable selector that holds the foretak number, default is "foretak".
            icon (str): The icon to be displayed in the tab, default is "🗃️".
        """
        self.module_number = BofInformation._id_number
        self.module_name = self.__class__.__name__
        BofInformation._id_number += 1
        if icon is None:
            self.icon = "🗃️"
        else:
            self.icon = icon

        if label is None:
            label = "BoF Foretak"
        self.label = label
        if variableselector_foretak_name is None:
            variableselector_foretak_name = "foretak"
        self.variableselector = VariableSelector(
            selected_inputs=[variableselector_foretak_name], selected_states=[]
        )
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()
        module_validator(self)

    def _is_valid(self):
        self._check_connection()

    def _check_connection(self):
        conn = sqlite3.connect(SSB_FORETAK_PATH)
        df = pd.read_sql_query("SELECT * FROM ssb_foretak LIMIT 1", conn)
        if df.empty:
            raise Exception(
                "Data from ssb_bedrift is empty, check that you can connect to the database."
            )
        conn.close()

        conn = sqlite3.connect(SSB_BEDRIFT_PATH)
        df = pd.read_sql_query("SELECT * FROM ssb_bedrift LIMIT 1", conn)
        if df.empty:
            raise Exception(
                "Data from ssb_bedrift is empty, check that you can connect to the database."
            )
        conn.close()

    def generate_card(self, title: str, component_id: str, var_type: str) -> dbc.Card:
        """Generate a Dash Bootstrap card for displaying data.

        Args:
            title (str): Title displayed in the card header.
            component_id (str): ID assigned to the input component inside the card.
            var_type (str): Input type for the component (e.g., "text").

        Returns:
            dbc.Card: A styled card containing an input field.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(title),
                dbc.CardBody(
                    [
                        dbc.Input(id=component_id, type=var_type),
                    ],
                    className="bofregistry-card-body",
                ),
            ],
            className="bofregistry-card",
        )
        return card

    def _create_layout(self) -> html.Div:
        """Generate the layout for the BoF Foretak tab."""
        layout = html.Div(
            className="bofregistry",
            children=[
                ssb_foretak_modal(),
                ssb_bedrift_modal(),
                dbc.Row(
                    [
                        dbc.Col(
                            self.generate_card(
                                "Orgnr",
                                "tab-bof_foretak-orgnrcard",
                                "text",
                            ),
                            width=2,
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Navn",
                                "tab-bof_foretak-navncard",
                                "text",
                            ),
                            width=10,
                        ),
                    ],
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self.generate_card(
                                "foretaks_nr",
                                "tab-bof_foretak-foretaksnrcard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Nace",
                                "tab-bof_foretak-nacecard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Statuskode",
                                "tab-bof_foretak-statuscard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Sektor 2014",
                                "tab-bof_foretak-sektorcard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "omsetning",
                                "tab-bof_foretak-omsetning",
                                "text",
                            ),
                        ),
                    ],
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self.generate_card(
                                "Organisasjonsform",
                                "tab-bof_foretak-orgformcard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Ansatte",
                                "tab-bof_foretak-ansattecard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Ansatte tot.",
                                "tab-bof_foretak-totansattecard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Kommunenummer",
                                "tab-bof_foretak-kommunecard",
                                "text",
                            ),
                        ),
                        dbc.Col(
                            self.generate_card(
                                "Type",
                                "tab-bof_foretak-typecard",
                                "text",
                            ),
                        ),
                    ],
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(),
                        dbc.Col(),
                        dbc.Col(),
                        dbc.Col(
                            dbc.Button(
                                "Vis mer foretaksinformasjon",
                                id="tab-vof-foretak-button1",
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Vis mer bedriftsinformasjon",
                                id="tab-vof-foretak-button2",
                            ),
                            width="auto",
                        ),
                    ],
                    className="mb-2",
                ),
                html.Div(
                    html.P(
                        "Tilhørende bedrifter",
                        className="bofregistry-table-bedrift-header",
                    ),
                    className="mb-2",
                ),
                html.Div(
                    dag.AgGrid(
                        id="tab-bof_foretak-table1",
                        className="ag-theme-alpine-dark header-style-on-filter bofregistry-table-bedrift-aggrid",
                        columnSize="responsiveSizeToFit",
                        defaultColDef={
                            "filter": True,
                            "resizable": True,
                            "sortable": True,
                            "floatingFilter": True,
                            "editable": False,
                        },
                        dashGridOptions={
                            "pagination": True,
                            "rowSelection": "single",
                            "rowHeight": 25,
                        },
                    ),
                ),
            ],
        )

        logger.debug("Generated layout")
        return layout

    @abstractmethod
    def layout(self) -> html.Div | dbc.Tab:
        """Define the layout for the BofInformation module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div | dbc.Tab: A Dash HTML Div component representing the layout of the module or a dbc.Tab to be displayed directly.
        """
        pass

    def module_callbacks(self) -> None:
        """Register Dash callbacks for the BoF Foretak tab.

        Notes:
            - The `bof_data` callback fetches and updates data in the cards based on the selected foretak.
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output("bofregistry-modal-ssb_foretak", "is_open"),
            Input("tab-vof-foretak-button1", "n_clicks"),
            State("bofregistry-modal-ssb_foretak", "is_open"),
        )
        def toggle_bof_modal(n_clicks: int, is_open: bool) -> bool:
            logger.debug("Toggling bof modal")
            if n_clicks > 0:
                if is_open:
                    return False
                else:
                    return True
            else:
                raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("bofregistry-modal-ssb_bedrift", "is_open"),
            Input("tab-vof-foretak-button2", "n_clicks"),
            State("bofregistry-modal-ssb_bedrift", "is_open"),
        )
        def toggle_bedrift_modal(n_clicks: int, is_open: bool) -> bool:
            logger.debug("Toggling bedrift modal")
            if n_clicks > 0:
                if is_open:
                    return False
                else:
                    return True
            raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("bofregistry-ssb_foretak-table", "rowData"),
            Output("bofregistry-ssb_foretak-table", "columnDefs"),
            Input("tab-vof-foretak-button1", "n_clicks"),
            State("tab-bof_foretak-orgnrcard", "value"),
        )
        def ssb_bof_foretak(
            n_clicks: int, orgnr: str
        ) -> tuple[list[dict[Any, Any]], list[dict[str, Any]]]:
            if n_clicks > 0:
                conn = sqlite3.connect(SSB_FORETAK_PATH)
                df = pd.read_sql_query(
                    f"SELECT * FROM ssb_foretak WHERE orgnr = '{orgnr}'", conn
                )
                df = df.melt()
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                    }
                    for col in df.columns
                ]
                return df.to_dict("records"), columns
            raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("bofregistry-ssb_bedrift-table", "rowData"),
            Output("bofregistry-ssb_bedrift-table", "columnDefs"),
            Input("tab-vof-foretak-button2", "n_clicks"),
            State("tab-bof_foretak-table1", "selectedRows"),
        )
        def ssb_bof_bedrift(
            n_clicks: int, selected_row: list[dict[str, Any]]
        ) -> tuple[list[dict[Any, Any]], list[dict[str, Any]]]:
            orgnr = selected_row[0]["orgnr"]
            if n_clicks > 0:
                conn = sqlite3.connect(SSB_BEDRIFT_PATH)
                df = pd.read_sql_query(
                    f"SELECT * FROM ssb_bedrift WHERE orgnr = '{orgnr}'", conn
                )
                df = df.melt()
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                    }
                    for col in df.columns
                ]
                return df.to_dict("records"), columns
            raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("tab-bof_foretak-orgnrcard", "value"),
            Output("tab-bof_foretak-navncard", "value"),
            Output("tab-bof_foretak-nacecard", "value"),
            Output("tab-bof_foretak-statuscard", "value"),
            Output("tab-bof_foretak-ansattecard", "value"),
            Output("tab-bof_foretak-sektorcard", "value"),
            Output("tab-bof_foretak-kommunecard", "value"),
            Output("tab-bof_foretak-orgformcard", "value"),
            Output("tab-bof_foretak-foretaksnrcard", "value"),
            Output("tab-bof_foretak-totansattecard", "value"),
            Output("tab-bof_foretak-omsetning", "value"),
            Output("tab-bof_foretak-typecard", "value"),
            *dynamic_states,
        )
        def bof_data(
            orgf: str,
        ) -> tuple[str, str, str, str, int, str, str, str, str, int, str, str]:
            """Fetch BoF Foretak data based on the selected organization number.

            Args:
                orgf (str): The organization number of the selected foretak.

            Returns:
                tuple: A tuple containing information about the foretak.

            Notes:
                - If `orgf` is None, no data is returned.
                - The callback queries the DuckDB database for the selected organization number.
            """
            if orgf is not None:
                conn = sqlite3.connect(SSB_FORETAK_PATH)
                df = pd.read_sql_query(
                    f"SELECT * FROM ssb_foretak WHERE orgnr = '{orgf}'",
                    conn,
                )

                df["ansatte_totalt"] = df["ansatte_totalt"].fillna(0)

                orgnr = df["orgnr"][0]
                navn = df["navn"][0]
                nace = df["sn07_1"][0]
                statuskode = df["statuskode"][0]
                ansatte = df["antall_ansatte"][0]
                sektor = df["sektor_2014"][0]
                kommune = df["f_kommunenr"][0]
                orgform = df["org_form"][0]
                foretaks_nr = df["foretaks_nr"][0]
                ansatte_tot = df["ansatte_totalt"][0]
                omsetning = df["omsetning"][0]
                typen = df["sf_type"][0]
                return (
                    orgnr,
                    navn,
                    nace,
                    statuskode,
                    ansatte,
                    sektor,
                    kommune,
                    orgform,
                    foretaks_nr,
                    ansatte_tot,
                    omsetning,
                    typen,
                )

        @callback(  # type: ignore[misc]
            Output("tab-bof_foretak-table1", "rowData"),
            Output("tab-bof_foretak-table1", "columnDefs"),
            Input("tab-bof_foretak-foretaksnrcard", "value"),
        )
        def populate_bedrifter(
            foretaksnr: str,
        ) -> tuple[list[dict[Any, Any]], list[dict[str, Any]]]:
            if foretaksnr is not None:
                conn = sqlite3.connect(SSB_BEDRIFT_PATH)
                df = pd.read_sql_query(
                    f"""SELECT bedrifts_nr, orgnr, navn, sn07_1, org_form, sysselsatte, ansatte_totalt, omsetning, statuskode, statuskode_gdato, statuskode_rdato
                    FROM ssb_bedrift WHERE foretaks_nr = '{foretaksnr}';""",
                    conn,
                )
                columns = (
                    [  # col == "bedrifts_nr" results to true if col is bedrifts_nr
                        {
                            "headerName": col,
                            "field": col,
                            "checkboxSelection": col == "bedrifts_nr",
                            "headerCheckboxSelection": col == "bedrifts_nr",
                        }
                        for col in df.columns
                    ]
                )
                return df.to_dict("records"), columns
            raise PreventUpdate

        logger.debug("Generated callbacks")
