import uuid
import logging

import dash_ag_grid as dag
from dash import Input, Output, no_update
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate

from ......setup.variableselector import VariableSelector
from ......utils.alert_handler import AlertHandler
#from ......utils.config_tools.set_variables import get_ident
#from ......utils.config_tools.set_variables import get_refnr
#from ......utils.config_tools.set_variables import get_time_units
from ..meta import MicrolayoutMeta
from ....utils import EditorSettings

logger = logging.getLogger(__name__)

class DynamicListEditor(html.Div):
    def __init__(
        self,
        fetcher: MicrolayoutMeta,
        settings: EditorSettings,
        wildcard: str,
        _id: str | None = None,
        **kwargs,
    ):
        if _id is None:
            _id = str(uuid.uuid4())

        table_id = f"table-{_id}"

        layout = [dag.AgGrid(id=table_id, style={"width": 1000})]
        super().__init__(id=_id, children=layout, **kwargs)

        @callback(
            Output(table_id, "rowData"),
            Output(table_id, "columnDefs"),
            inputs={
                "refnr": VariableSelector.get_refnr(Input),
                "ident": VariableSelector.get_ident(Input),
                "period": VariableSelector.get_timevar(Input),
            },
        )
        def update_table(refnr, ident, period):
            if not refnr or not ident or not period:
                raise PreventUpdate
            
            try:
                data = fetcher.get_dynamic_list(settings, wildcard, refnr)
            except Exception as e:
                msg = f"Getting dynamic list failed with error: {e}"
                logger.warning(msg)
                AlertHandler.warning(msg)
                return (no_update, no_update)

            keys = set()
            for item in data:
                item_list = list(item.keys())
                keys.update(item_list)
            column_defs = []
            for key in keys:
                column_defs.append({"field": key})

            return data, column_defs
