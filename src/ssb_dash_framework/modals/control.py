import logging
from typing import Any
from typing import cast

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate

from ..utils.functions import sidebar_button

# +

logger = logging.getLogger(__name__)

ident_options = [
    {
        "orgb": ("var-bedrift", "value"),
        "orgf": ("var-foretak", "value"),
    }
]


class Control:
    """Provides a layout and functionality for a modal that offers an overview of data checks and control results.

    Attributes:
        ident (str): Name of the identification variable, e.g., 'orgf'.
    """

    def __init__(self, ident: str) -> None:
        """Initialize the control module.

        This method sets up the identification variable, loads the quality report from a JSON file,
        and prepares data tables for control documentation and outputs.

        Args:
            ident (str): The key for the identification variable, e.g., 'orgf'.

        Attributes Set:
            ident (str): The resolved name of the identification variable.
        """
        self.ident = ident_options[0][ident]
        self.callbacks()

    def layout(self) -> html.Div:
        """Generates the layout for the control modal.

        Returns:
            dash.html.Div: Layout containing the control modal and interactive components.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader([dbc.ModalTitle("⚠️ Kontroller")]),
                        dbc.ModalBody(
                            [
                                dag.AgGrid(
                                    id="control-table-overview",
                                    columnDefs=[
                                        {"field": x}
                                        for x in [
                                            "kontroll_id",
                                            "kontrolltype",
                                            "feilbeskrivelse",
                                            "Enheter i datasettet",
                                            "Enheter kontrollert",
                                            "Kontrollutslag",
                                        ]
                                    ],
                                ),
                                dag.AgGrid(
                                    id="control-table-detailed",
                                    columnDefs=[
                                        {"field": x}
                                        for x in ["observasjon_id", "feilbeskrivelse"]
                                    ]
                                    + [
                                        {
                                            "field": "kontrollnavn",
                                            "hide": True,
                                            "filter": True,
                                        }
                                    ],
                                ),
                            ]
                        ),
                    ],
                    id="control-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("⚠️", "Kontroller", "sidebar-control-button"),
            ]
        )
        logger.debug("Generated layout")
        return layout

    def callbacks(self) -> None:
        """Sets up interactivity for the control modal, including linking table clicks and navigation back to the main view."""

        @callback(
            Output("control-modal", "is_open"),
            Input("sidebar-control-button", "n_clicks"),
            State("control-modal", "is_open"),
        )
        def controlmodal_toggle(n: int | None, is_open: bool) -> bool:
            """Toggles the open/close state of the control modal.

            Args:
                n (int | None): Number of clicks on the sidebar button.
                is_open (bool): Current state of the modal.

            Returns:
                bool: Updated state of the modal.
            """
            if n:
                return not is_open
            return is_open

        @callback(
            Output("control-table-detailed", "filterModel"),
            Input("control-table-overview", "cellClicked"),
            State("control-table-overview", "rowData"),
        )
        def control_main_click(
            click: dict[str, int | dict[str, Any] | None] | None,
            rowdata: list[dict[str, Any]],
        ) -> dict[str, dict[str, str]]:
            """Links clicks on the control overview table to filter the detailed control results table.

            Args:
                click (dict | None): Data about the clicked cell in the overview table.
                rowdata (dict): Data from the rows in the overview table.

            Returns:
                dict: Filter model to apply to the detailed results table.

            Raises:
                PreventUpdate: Stops the callback if click is None.
            """
            if not click or not isinstance(click.get("rowIndex"), int):
                raise PreventUpdate
            row_index = cast(int, click["rowIndex"])
            try:
                kontroll = rowdata[row_index]["kontroll_id"]
            except (IndexError, KeyError) as e:
                raise PreventUpdate from e
            return {
                "kontrollnavn": {
                    "filterType": "text",
                    "type": "contains",
                    "filter": kontroll,
                }
            }

        @callback(
            Output(self.ident[0], self.ident[1]),
            Input("control-table-detailed", "cellClicked"),
            State("control-table-detailed", "rowData"),
        )
        def control_detail_click(
            click: dict[str, int | dict[str, Any] | None] | None,
            rowdata: list[dict[str, Any]],
        ) -> str:
            """Links clicks in the detailed control results table to select the identification variable value.

            Args:
                click (dict | None): Data about the clicked cell in the detailed table.
                rowdata (dict): Data from the rows in the detailed table.

            Returns:
                str: Selected identification variable value.

            Raises:
                PreventUpdate: Stops the callback if click is None.
            """
            if not click or not isinstance(click.get("rowIndex"), int):
                raise PreventUpdate

            row_index = cast(int, click["rowIndex"])
            try:
                observation = rowdata[row_index]["observasjon_id"]
            except (IndexError, KeyError) as e:
                raise PreventUpdate from e

            if not isinstance(observation, str):
                logger.warning(
                    f"observation_id should be str, is {type(observation).__name__}"
                )
            return str(observation)

        logger.debug("Generated callbacks")
