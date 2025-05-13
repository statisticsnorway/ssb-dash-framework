import logging
from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector  # TODO TEMP!!!!
from ..setup.variableselector import VariableSelectorOption  # TODO TEMP!!!!
from ..utils.alert_handler import create_alert

logger = logging.getLogger(__name__)


class EditingTable(ABC):
    """A component for editing data using a Dash AgGrid table.

    This class provides a layout and functionality to:
    - Select a database table from a dropdown menu.
    - Load data into an editable Dash AgGrid table.
    - Update database values based on user edits in the table.

    Attributes:
        label (str): The label for the tab or component.
        ident (str | None): Identifier for the table, used for callbacks.
        varselector_ident (str | None): Identifier for the variable selector.
        variableselector (VariableSelector): A variable selector for managing inputs and states.
        get_data (Callable[..., Any]): Function to fetch data from the database.
        update_table (Callable[..., Any]): Function to update database records based on edits in the table.
        module_layout (html.Div): The layout of the component.
    """

    _id_number = 0

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any],
        ident: str | None = None,
        varselector_ident: str | None = None,
    ) -> None:
        """Initialize the EditingTable component.

        Args:
            label (str): The label for the tab or component.
            inputs (list[str]): A list of input variable names.
            states (list[str]): A list of state variable names for filtering data.
            get_data_func (Callable[..., Any]): A function for retrieving data from the database.
            update_table_func (Callable[..., Any]): A function for updating data in the database.
            ident (str | None, optional): Identifier for the table. Defaults to None.
            varselector_ident (str | None, optional): Identifier for the variable selector. Defaults to None.
        """
        self._editingtable_n = EditingTable._id_number
        self.module_name = self.__class__.__name__
        EditingTable._id_number += 1
        self.label = label
        self.ident = ident
        self.varselector_ident = varselector_ident

        for i in [*inputs, *states]:
            try:
                VariableSelectorOption(i)
            except ValueError:
                logger.debug(f"{i} already exists as an option, skipping.")

        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.get_data = get_data_func
        self.get_data_args = [x for x in self.variableselector.selected_variables]
        self.update_table = update_table_func
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _create_layout(self) -> html.Div:
        """Generate the layout for the EditingTable component.

        Returns:
            html.Div: A Div element containing:
                - A dropdown menu to select a database table.
                - An editable Dash AgGrid table for displaying and modifying data.
                - A status message for updates.
        """
        layout = html.Div(
            style={"height": "100vh", "display": "flex", "flexDirection": "column"},
            children=[
                html.Div(
                    children=[
                        dag.AgGrid(
                            defaultColDef={"editable": True},
                            id=f"{self._editingtable_n}-tabelleditering-table1",
                            className="ag-theme-alpine-dark header-style-on-filter",
                        ),
                        html.P(id=f"{self._editingtable_n}-tabelleditering-status1"),
                    ],
                ),
            ],
        )
        logger.debug("Generated layout")
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the EditingTable module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Register Dash callbacks for the EditingTable component.

        Notes:
            - The `load_ag_grid` callback loads data into the table based on the selected table
              and filter states.
            - The `update_table` callback updates database values when a cell value is changed.
        """
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(  # type: ignore[misc]
            Output(f"{self._editingtable_n}-tabelleditering-table1", "rowData"),
            Output(f"{self._editingtable_n}-tabelleditering-table1", "columnDefs"),
            *dynamic_states,
        )
        def load_to_table(
            tabell: str, *dynamic_states: list[str]
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            """Load data into the Dash AgGrid table.

            Args:
                tabell (str): Name of the selected database table.
                dynamic_states (list[str]): Dynamic state parameters for filtering data.

            Returns:
                tuple: Contains:
                    - rowData (list[dict]): Records to display in the table.
                    - columnDefs (list[dict]): Column definitions for the table.

            Raises:
                Exception: If there is an error loading data into the table.
            """
            try:
                df = self.get_data(tabell, *dynamic_states)
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": col == "row_id",
                    }
                    for col in df.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error("Error loading data into table", exc_info=True)
                raise e

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self._editingtable_n}-tabelleditering-table1", "cellValueChanged"),
            State("alert_store", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def update_table(
            edited: list[dict[str, dict[str, Any] | Any]],
            tabell: str,
            error_log: list[dict[str, Any]],
            *dynamic_states: list[str],
        ) -> list[dict[str, Any]]:
            """Update the database based on edits made in the AgGrid table.

            Args:
                edited (list[dict]): Information about the edited cell.
                tabell (str): The name of the table being edited.
                error_log (list[dict]): List of existing alerts in the alert handler.
                dynamic_states (list[str]): Dynamic state parameters for filtering data.

            Returns:
                list[dict]: Updated error log with success or failure messages.

            Raises:
                PreventUpdate: If no edits were made.
            """
            if not edited:
                raise PreventUpdate
            logger.debug(f"Edited:\n{edited}")
            try:
                variable = edited[0]["colId"]
                old_value = edited[0]["oldValue"]
                new_value = edited[0]["value"]
                row_id = edited[0]["data"]["row_id"]
                self.update_table(tabell, variable, new_value, row_id)

                error_log.append(
                    create_alert(
                        f"{variable} updatert fra {old_value} til {new_value}",
                        "info",
                        ephemeral=True,
                    )
                )
                return error_log

            except Exception:
                logger.error("Error updating table", exc_info=True)
                error_log.append(
                    create_alert(
                        f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                        "warning",
                        ephemeral=True,
                    )
                )
                return error_log

        if self.ident and self.varselector_ident:
            logger.debug(
                "Adding callback for returning clicked ident to variable selector"
            )
            output_object = self.variableselector.get_output_object(
                variable=self.varselector_ident
            )

            @callback(  # type: ignore[misc]
                output_object,
                Input(f"{self._editingtable_n}-tabelleditering-table1", "cellClicked"),
                prevent_initial_call=True,
            )
            def table_to_main_table(clickdata: dict[str, Any]) -> str:
                """Passes the selected observation identifier to `variabelvelger`.

                Args:
                    clickdata (dict): Data from the clicked point in the HB visualization.

                Returns:
                    str: Identifier of the selected observation.

                Raises:
                    PreventUpdate: if clickdata is None.
                """
                if not clickdata:
                    raise PreventUpdate
                if clickdata["colId"] != self.ident:
                    raise PreventUpdate
                ident = clickdata["value"]
                if not isinstance(ident, str):
                    logger.debug(f"{ident} is not a string, is type {type(ident)}")
                    raise PreventUpdate
                logger.debug(f"Transfering {ident} to {self.varselector_ident}")
                return ident

        logger.debug("Generated callbacks")
