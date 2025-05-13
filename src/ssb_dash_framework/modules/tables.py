import logging
from abc import ABC
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
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
        database (object): Database connection or interface for querying and updating data.
        var_input (str): Variable input key for identifying records in the database.
        states (list[str]): Keys representing dynamic states to filter data.
        get_data (callable): Function to fetch data from the database.
        update_table (callable): Function to update database records based on edits in the table.
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
            database (object): A database connection or interface used for querying and updating data.
            tables (list[str]): A list of available table names for selection.
            id_var (str): The identifier variable used to uniquely identify records in the database.
            states (list[str]): A list of keys representing dynamic states to filter data (e.g., "aar", "termin").
            get_data_func (Callable[..., Any]): A function for retrieving data from the database.
            update_table_func (Callable[..., Any]): A function for updating data in the database.

        Raises:
            TypeError: If `id_var` is not of type `str`.
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
            except:
                logger.debug(f"{i} already exists as option, will skip adding it.")
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
                dynamic_states (list): Dynamic state parameters for filtering data.

            Returns:
                tuple: Contains:
                    - rowData (list[dict]): Records to display in the table.
                    - columnDefs (list[dict]): Column definitions for the table.

            Raises:
                Exception: If the loading fails, it raises an exception to help troubleshooting.

            Notes:
                - Columns are dynamically generated based on the table's schema.
                - The "row_id" column is hidden by default but used for updates.
                - Adds checkbox selection to the first column for bulk actions.
            """
            try:
                df = self.get_data(tabell, *dynamic_states)
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": True if col == "row_id" else False,
                    }
                    for col in df.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
                return df.to_dict("records"), columns
            except Exception as e:
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
        ) -> dbc.Alert:
            """Update the database based on edits made in the AgGrid table.

            Args:
                edited (list[dict]): Information about the edited cell, including:
                    - colId: The column name of the edited cell.
                    - oldValue: The previous value of the cell.
                    - value: The new value of the cell.
                    - data: The row data, including the "row_id".
                tabell (str): The name of the table being edited.
                error_log (list of dbc.Alert): List of currently existing alerts in the alert handler module.
                dynamic_states (list): Dynamic state parameters for filtering data.

            Returns:
                dbc.Alert: A status message indicating the success or failure of the update.

            Raises:
                PreventUpdate: If no edit has taken place, the callback does not run.

            Notes:
                - Calls `update_table` to apply the change to the database.
                - If successful, returns a confirmation message.
                - If failed, returns an error message.
            """
            if not edited:
                raise PreventUpdate
            states_values = dynamic_states[: len(self.variableselector.states)]
            state_params = {
                key: value
                for key, value in zip(
                    self.variableselector.states, states_values, strict=False
                )
            }

            args = []
            for key in self.variableselector.states:
                var = state_params.get(key)
                if var is not None:
                    args.append(var)
            variable = edited[0]["colId"]
            old_value = edited[0]["oldValue"]
            new_value = edited[0]["value"]
            row_id = edited[0]["data"]["row_id"]
            logger.debug(f"Edited:\n{edited}")
            try:
                self.update_table(tabell, variable, new_value, row_id)

                error_log.append(
                    create_alert(
                        f"{variable} updatert fra {old_value} til {new_value}",
                        "info",
                        ephemeral=True,
                    )
                )

                return error_log

            except Exception as e:
                logger.error(msg=e, exc_info=True)
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
            def table_to_main_table(clickdata: dict[str, list[dict[str, Any]]]) -> str:
                """Passes the selected observation identifier to `variabelvelger`.

                Args:
                    clickdata (dict): Data from the clicked point in the HB visualization.

                Returns:
                    str: Identifier of the selected observation.

                Raises:
                    PreventUpdate: if clickdata is None.
                """
                print(clickdata)
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
