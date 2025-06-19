import logging
from collections.abc import Callable
from typing import Any

from ..modules.building_blocks.tables import EditingTable
from ..modules.building_blocks.tables import MultiTable
from ..utils import WindowImplementation

logger = logging.getLogger(__name__)


class EditingTableWindow(WindowImplementation, EditingTable):
    """A class to implement an EditingTable module inside a modal.

    It is used to create a modal window containing an EditingTable.
    This class inherits from both EditingTable and WindowImplementation, where WindowImplementation is a mixin that handles the modal functionality.
    """

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any] | None = None,
        output: str | None = None,
        output_varselector_name: str | None = None,
    ) -> None:
        """Initialize the EditingTableWindow.

        Args:
            label (str): The label for the modal.
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
        WindowImplementation.__init__(
            self,
        )


class MultiTableWindow(WindowImplementation, MultiTable):
    """A class to implement a MultiTable module inside a modal."""

    def __init__(
        self,
        label: str,
        table_list: list[EditingTable],
    ) -> None:
        """Initialize the MultitableWindow.

        Args:
            label (str): The label for the modal.
            table_list (list[EditingTable]): List of EditingTable instances to be included in the modal.
        """
        MultiTable.__init__(self, label=label, table_list=table_list)
        WindowImplementation.__init__(self)
