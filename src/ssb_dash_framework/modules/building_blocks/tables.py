import logging
from collections.abc import Callable
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

from ...setup.variableselector import VariableSelector
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class EditingTable:
    """A component for editing data using a Dash AgGrid table.

    This class provides a layout and functionality to:
    - Select a database table from a dropdown menu.
    - Load data into an editable Dash AgGrid table.
    - Update database values based on user edits in the table.

    Attributes:
        label (str): The label for the tab or component.
        output (str | None): Identifier for the table, used for callbacks.
        output_varselector_name (str | None): Identifier for the variable selector.
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
        update_table_func: Callable[..., Any] | None = None,
        output: str | list[str] | None = None,
        output_varselector_name: str | list[str] | None = None,
        number_format=None,
        **kwargs,
    ) -> None:
        """Initialize the EditingTable component.

        Args:
            label (str): The label for the tab or component, used for display purposes.
            inputs (list[str]): A list of input variable names that will trigger callbacks.
            states (list[str]): A list of state variable names used that will not trigger callbacks, but can be provided as args.
            get_data_func (Callable[..., Any]): A function for retrieving data from the database.
            update_table_func (Callable[..., Any]): A function for updating data in the database.
                Note, the update_table_func is provided with the cellValueChanged from the Dash AgGrid in addition the inputs and states values.
            output (str | list[str] | None, optional): Identifier for the table, used for callbacks. Defaults to None.
            output_varselector_name (str | list[str] | None, optional): Identifier for the variable selector. If list, make sure it is in the same order as output. Defaults to None.
                If `output` is provided but `output_varselector_name` is not, it will default to the value of `output`.

        Note:
            kwargs are passed to the AgGrid to allow more customization. An example option would be adding dashGridOptions = {"singleClickEdit": True}
        """
        self.kwargs = kwargs

        self.module_number = EditingTable._id_number
        self.module_name = self.__class__.__name__
        EditingTable._id_number += 1
        self.label = label
        self.output = output
        self.output_varselector_name = output_varselector_name or output

        if number_format is None:
            self.number_format = "d3.format(',.1f')(params.value).replace(/,/g, ' ')"
        else:
            self.number_format = number_format

        self.variableselector = VariableSelector(
            selected_inputs=inputs, selected_states=states
        )
        self.get_data = get_data_func
        self.get_data_args = [x for x in self.variableselector.selected_variables]
        self.update_table_func = update_table_func
        self.module_layout = self._create_layout()
        self.module_callbacks()
        self._is_valid()

        module_validator(self)

    def _is_valid(self) -> None:
        """Check if the module is valid."""
        if not isinstance(self.label, str):
            raise TypeError(
                f"label {self.label} is not a string, is type {type(self.label)}"
            )
        if self.output is not None and self.output_varselector_name is not None:
            if isinstance(self.output, str) and not isinstance(
                self.output_varselector_name, str
            ):
                raise TypeError(
                    f"output is a string while output_varselector_name {self.output_varselector_name} is not a string, is type {type(self.output_varselector_name)}"
                )
            elif isinstance(self.output, list) and isinstance(
                self.output_varselector_name, list
            ):
                if len(self.output) != len(self.output_varselector_name):
                    raise ValueError(
                        f"output {self.output} and output_varselector_name {self.output_varselector_name} are not the same length"
                    )

    def _create_layout(self, **kwargs) -> html.Div:
        """Generate the layout for the EditingTable component.

        Returns:
            html.Div: A Div element containing:
                - A dropdown menu to select a database table.
                - An editable Dash AgGrid table for displaying and modifying data.
                - A status message for updates.
        """
        layout = html.Div(
            className="editingtable",
            children=[
                dag.AgGrid(
                    defaultColDef=self.kwargs.get(
                        "defaultColDef", {"editable": True}
                    ),  # This is to make sure the user can override the defaultColDef
                    id=f"{self.module_number}-tabelleditering-table1",
                    className="ag-theme-alpine-dark header-style-on-filter editingtable-aggrid-style",
                    **{k: v for k, v in self.kwargs.items() if k != "defaultColDef"},
                )
            ],
        )
        logger.debug("Generated layout")
        return layout

    def layout(self) -> html.Div | dbc.Tab:
        """Define the layout for the EditingTable module.

        Because this module can be used as a a component in other modules, it needs to have a layout method that is not abstract.
        For implementations as tab or window, this method should still be overridden.

        Returns:
            html.Div | dbc.Tab: A Dash HTML Div component representing the layout of the module or a dbc.Tab to be displayed directly.
        """
        return self._create_layout()

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

        @callback(
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            *dynamic_states,
        )
        def load_to_table(
            *dynamic_states: list[str],
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            """Load data into the Dash AgGrid table.

            Args:
                error_log (list[dict[str, Any]]): List of existing alerts in the alert handler.
                dynamic_states (list[str]): Dynamic state parameters for filtering data.

            Returns:
                tuple: Contains:
                    - rowData (list[dict]): Records to display in the table.
                    - columnDefs (list[dict]): Column definitions for the table.

            Raises:
                Exception: If there is an error loading data into the table.
            """
            logger.debug(
                f"Loading data to table with label {self.label}, module_number: {self.module_number}"
            )
            try:
                df = self.get_data(*dynamic_states)
                logger.debug(
                    f"{self.label} - {self.module_number}: Data from get_data: {df}"
                )
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": col == "row_id",
                        "valueFormatter": (
                            {"function": self.number_format}
                            if pd.api.types.is_numeric_dtype(df[col])
                            else None
                        ),
                    }
                    for col in df.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
                logger.debug(f"{self.label} - {self.module_number}: Returning data")
                return df.to_dict("records"), columns
            except Exception as e:
                logger.error(
                    f"{self.label} - {self.module_number}: Error loading data into table",
                    exc_info=True,
                )
                raise e

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            Input(f"{self.module_number}-tabelleditering-table1", "cellValueChanged"),
            State("alert_store", "data"),
            *dynamic_states,
            prevent_initial_call=True,
        )
        def update_table(
            edited: list[dict[str, dict[str, Any] | Any]],
            error_log: list[dict[str, Any]],
            *dynamic_states: list[str],
        ) -> list[dict[str, Any]]:
            """Update the database based on edits made in the AgGrid table.

            Args:
                edited (list[dict]): Information about the edited cell.
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
            if self.update_table_func is None:
                logger.error("No update function provided")
                error_log.append(
                    create_alert(
                        "Ingen oppdateringsfunksjon er definert",
                        "warning",
                        ephemeral=True,
                    )
                )
                return error_log, None

            variable = edited[0]["colId"]
            old_value = edited[0]["oldValue"]
            new_value = edited[0]["value"]

            try:
                self.update_table_func(edited, *dynamic_states)
                error_log.append(
                    create_alert(
                        f"{variable} updatert fra {old_value} til {new_value}",
                        "info",
                        ephemeral=True,
                    )
                )
                return error_log, None

            except Exception:
                logger.error("Error updating table", exc_info=True)
                error_log.append(
                    create_alert(
                        f"Oppdatering av {variable} fra {old_value} til {new_value} feilet!",
                        "error",
                        ephemeral=True,
                    )
                )
                return error_log, None

        if self.output and self.output_varselector_name:
            logger.debug(
                "Adding callback for returning clicked output to variable selector"
            )
            if isinstance(self.output, str) and isinstance(
                self.output_varselector_name, str
            ):
                output_objects = [
                    self.variableselector.get_output_object(
                        variable=self.output_varselector_name
                    )
                ]
                output_columns = [self.output]
            elif isinstance(self.output, list) and isinstance(
                self.output_varselector_name, list
            ):
                output_objects = [
                    self.variableselector.get_output_object(variable=var)
                    for var in self.output_varselector_name
                ]
                output_columns = self.output
            else:
                logger.error(
                    f"output {self.output} is not a string or list, is type {type(self.output)}"
                )
                raise TypeError(
                    f"output {self.output} is not a string or list, is type {type(self.output)}"
                )
            logger.debug(f"Output object: {output_objects}")

            def make_table_to_main_table_callback(
                output: Output, column: str, output_varselector_name: str
            ) -> None:
                @callback(
                    output,
                    Input(
                        f"{self.module_number}-tabelleditering-table1", "cellClicked"
                    ),
                    prevent_initial_call=True,
                )
                def table_to_main_table(clickdata: dict[str, Any]) -> str:
                    if not clickdata:
                        raise PreventUpdate
                    if clickdata["colId"] != column:
                        raise PreventUpdate
                    output = clickdata["value"]
                    if not isinstance(output, str):
                        logger.debug(
                            f"{output} is not a string, is type {type(output)}"
                        )
                        raise PreventUpdate
                    logger.debug(f"Transfering {output} to {output_varselector_name}")
                    return output

            for i in range(len(output_objects)):
                make_table_to_main_table_callback(
                    output_objects[i],
                    output_columns[i],
                    (
                        self.output_varselector_name[i]
                        if isinstance(self.output_varselector_name, list)
                        else self.output_varselector_name
                    ),
                )

        logger.debug("Generated callbacks")
