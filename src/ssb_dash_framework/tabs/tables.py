import logging
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils.alert_handler import create_alert

logger = logging.getLogger(__name__)


class EditingTableLong:
    """A component for editing database tables using a Dash AgGrid table.

    This class provides a layout and functionality to:
    - Select a database table from a dropdown menu.
    - Load data into an editable Dash AgGrid table.
    - Update database values based on user edits in the table.

    Attributes:
        label (str): The label for the tab or component.
        database (object): Database connection or interface for querying and updating data.
        tables (list[str]): List of available table names for selection.
        var_input (str): Variable input key for identifying records in the database.
        states (list[str]): Keys representing dynamic states to filter data.
        get_data (callable): Function to fetch data from the database.
        update_table (callable): Function to update database records based on edits in the table.
        dropdown_options (list[dict]): List of options for the dropdown menu, derived from `tables`.
    """

    def __init__(
        self,
        label: str,
        database: object,
        tables,
        #  variable_name: str,
        id_var: str,
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any],
    ) -> None:
        """Initialize the EditingTable component.

        Args:
            label (str): Label for the tab or component.
            database (object): Database connection or interface for querying and updating data.
            tables (list[str]): List of available table names for selection.
            var_input (str): Variable input key used to identify records (e.g., "orgb", "orgf").
            states (list[str]): Keys representing dynamic states to filter data (e.g., "aar", "termin").
            get_data_func (callable): Function for retrieving data from the database.
            update_table_func (callable): Function for updating data in the database.
        """
        self.label = label
        # self.var_col = variable_name
        self.database = database

        if not isinstance(id_var, str):
            raise TypeError("Invalud value for id_var, should be type str.")
        self.variableselector = VariableSelector(
            selected_inputs=[id_var], selected_states=states
        )

        self.get_data = get_data_func

        self.get_data_args = [
            x for x in self.variableselector.selected_variables if x not in [id_var]
        ]

        self.update_table = update_table_func

        dropdown_options = [
            {"label": table, "value": table} for table in tables
        ]  # make default value all tables starting with "skjemadata_"?
        self.dropdown_options = dropdown_options

        self.callbacks()

    def layout(self) -> html.Div:
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
                        dcc.Dropdown(
                            id="tab-tabelleditering-dd1",
                            options=self.dropdown_options,
                            value=self.dropdown_options[0]["value"],
                            placeholder="Velg tabell",
                            className="dbc",
                        ),
                        dag.AgGrid(
                            defaultColDef={"editable": True},
                            id="tab-tabelleditering-table1",
                            className="ag-theme-alpine-dark header-style-on-filter",
                        ),
                        html.P(id="tab-tabelleditering-status1"),
                    ],
                ),
            ],
        )
        logger.debug("Generated layout")
        return layout

    def callbacks(self) -> None:
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
            Output("tab-tabelleditering-table1", "rowData"),
            Output("tab-tabelleditering-table1", "columnDefs"),
            Input("tab-tabelleditering-dd1", "value"),
            *dynamic_states,
        )
        def load_to_table(
            tabell: str, *dynamic_states: list[str]
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            """Load data into the Dash AgGrid table.

            Args:
                tabell (str): Name of the selected database table.
                ident (str): Identifier for filtering records (e.g., "var-bedrift").
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
                df = self.get_data(self.database, tabell, *dynamic_states)
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
            Input("tab-tabelleditering-table1", "cellValueChanged"),
            State("tab-tabelleditering-dd1", "value"),
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
                self.update_table(self.database, tabell, variable, new_value, row_id)

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

        logger.debug("Generated callbacks")
