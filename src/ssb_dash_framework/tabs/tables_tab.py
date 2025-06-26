import logging
from collections.abc import Callable
from typing import Any

from ..modules.building_blocks.tables import EditingTable
from ..utils import TabImplementation

logger = logging.getLogger(__name__)


class EditingTableTab(TabImplementation, EditingTable):
    """A class to implement a module inside a tab."""

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
        number_format=None,
        **kwargs
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
            **kwargs
        )
        TabImplementation.__init__(
            self,
        )
