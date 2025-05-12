import logging
from collections.abc import Callable
from typing import Any

from ..modules.tables import EditingTable

logger = logging.getLogger(__name__)


class EditingTableTab(EditingTable):

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
        super().__init__(
            label=label,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            update_table_func=update_table_func,
            ident=ident,
            varselector_ident=varselector_ident,
        )

    def layout(self):
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
