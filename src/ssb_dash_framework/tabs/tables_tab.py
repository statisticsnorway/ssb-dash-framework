import logging
from collections.abc import Callable
from typing import Any

import dash_bootstrap_components as dbc

from ..modules.tables import EditingTable
from ..modules.tables import MultiTable
from ..utils import TabImplementation

logger = logging.getLogger(__name__)


class EditingTableTab(EditingTable, TabImplementation):
    """A class to implement a module inside a tab."""

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any],
        output: str | None = None,
        output_varselector_name: str | None = None,
    ) -> None:
        """Initialize the EditingTableTab.

        This class is used to create a tab to put in the tab_list.

        Args:
            label (str): The label for the tab.
            inputs (list[str]): The list of input IDs.
            states (list[str]): The list of state IDs.
            get_data_func (Callable[..., Any]): Function to get data for the table.
            update_table_func (Callable[..., Any]): Function to update the table.
            output (str | None, optional): Identifier for the table. Defaults to None.
            output_varselector_name (str | None, optional): Identifier for the variable selector. Defaults to None.
        """
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            update_table_func=update_table_func,
            output=output,
            output_varselector_name=output_varselector_name,
        )
        TabImplementation.__init__(
            self,
        )

    def layout(self) -> dbc.Tab:
        """Generate the layout for the module as a tab."""
        layout = TabImplementation.layout(self)
        logger.debug("Generated layout")
        return layout


class MultiTableTab(MultiTable, TabImplementation):
    """A class to implement a multitable module inside a tab."""

    def __init__(
        self,
        label: str,
        table_list: list[EditingTable],
    ) -> None:
        """Initialize the MultiTableTab.

        This class is used to create a tab to put in the tab_list.

        Args:
            label (str): The label for the tab.
            table_list (list[EditingTable]): List of EditingTable instances to be included in the multitable.
        """
        MultiTable.__init__(self, label=label, table_list=table_list)
        TabImplementation.__init__(self)

    def layout(self) -> dbc.Tab:
        """Generate the layout for the multitable module as a tab."""
        layout = TabImplementation.layout(self)
        logger.debug("Generated layout")
        return layout
