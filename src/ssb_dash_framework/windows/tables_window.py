import logging
from collections.abc import Callable
from typing import Any

from ..modules.tables import EditingTable
from ..utils import WindowImplementation

logger = logging.getLogger(__name__)


class EditingTableWindow(EditingTable, WindowImplementation):

    def __init__(
        self,
        label: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        update_table_func: Callable[..., Any],
        ident=None,
        varselector_ident=None,
    ):
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
        WindowImplementation.__init__(
            self,
        )

    def layout(self):
        layout = WindowImplementation.layout(self)
        return layout
