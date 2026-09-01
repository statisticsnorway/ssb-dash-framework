import uuid

import dash_ag_grid as dag
from dash import Output
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate

from ......setup.variableselector import VariableSelector
from ......utils.config_tools.set_variables import get_ident
from ......utils.config_tools.set_variables import get_refnr
from ......utils.config_tools.set_variables import get_time_units
from ....meta import FetcherMeta
from ....utils import EditorSettings


class DynamicListEditor(html.Div):
    def __init__(
        self,
        fetcher: FetcherMeta,
        settings: EditorSettings,
        wildcard: str,
        _id: str | None = None,
        **kwargs,
    ):
        if _id is None:
            _id = str(uuid.uuid4())

        table_id = f"table-{_id}"

        selector = VariableSelector(
            [get_refnr(), get_ident(), get_time_units().name], []
        )

        layout = [dag.AgGrid(id=table_id, style={"width": 1000})]
        super().__init__(id=_id, children=layout, **kwargs)

        @callback(
            Output(table_id, "rowData"),
            Output(table_id, "columnDefs"),
            inputs={
                "refnr": selector.get_input(get_refnr()),
                "ident": selector.get_input(get_ident()),
                "period": selector.get_input(get_time_units().name),
            },
        )
        def update_table(refnr, ident, period):
            if not refnr or not ident or not period:
                raise PreventUpdate
            refnr = "394ee263060d"
            data = fetcher.get_dynamic_list(settings, wildcard, refnr)

            keys = set()
            for item in data:
                item_list = list(item.keys())
                keys.update(item_list)
            column_defs = []
            for key in keys:
                column_defs.append({"field": key})

            return data, column_defs
