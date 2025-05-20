import logging
from collections.abc import Callable
from typing import Any

from dash import html

from ..modules.tables import EditingTable
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
        ident: str | None = None,
        varselector_ident: str | None = None,
    ) -> None:
        """Initialize the EditingTableTab.

        This class is used to create a tab to put in the tab_list.

        Args:
            label (str): The label for the tab.
            inputs (list[str]): The list of input IDs.
            states (list[str]): The list of state IDs.
            get_data_func (Callable[..., Any]): Function to get data for the table.
            update_table_func (Callable[..., Any]): Function to update the table.
            ident (str | None, optional): Identifier for the table. Defaults to None.
            varselector_ident (str | None, optional): Identifier for the variable selector. Defaults to None.
        """
        EditingTable.__init__(
            self,
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            update_table_func=update_table_func,
            ident=ident,
            varselector_ident=varselector_ident,
        )
        TabImplementation.__init__(
            self,
        )

    def layout(self) -> html.Div:
        """Generate the layout for the module as a tab."""
        layout = TabImplementation.layout(self)
        logger.debug("Generated layout")
        return layout
