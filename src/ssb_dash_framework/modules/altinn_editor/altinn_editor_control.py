import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorControl:

    def __init__(self, time_units, conn, variable_selector_instance):
        self.time_units = time_units
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _create_layout(self) -> html.Div:
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label("Kontroller", className="mb-1"),
                        dbc.Button(
                            "Se kontrollutslag",
                            id="altinnedit-option5",
                            className="w-100",
                        ),
                    ]
                ),
                self.offcanvas_kontrollutslag(),
            ]
        )

    def layout(self):
        return self.module_layout

    def offcanvas_kontrollutslag(self) -> html.Div:
        """Returns an offcanvas component containing a table for kontrollutslag."""
        return html.Div(
            [
                dbc.Offcanvas(
                    html.Div(
                        dag.AgGrid(
                            defaultColDef={"editable": False},
                            id="offcanvas-control-table1",
                            className="ag-theme-alpine-dark header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                        ),
                    ),
                    id="offcanvas-control",
                    title="Kontrollutslag",
                    is_open=False,
                    placement="end",
                    backdrop=False,
                    style={"width": "50%", "height": "100%"},
                ),
            ]
        )

    def module_callbacks(self):
        @callback(  # type: ignore[misc]
            Output("offcanvas-control", "is_open"),
            Input("altinnedit-option5", "n_clicks"),
            State("offcanvas-control", "is_open"),
        )
        def toggle_offcanvas_kontrollutslag(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("offcanvas-control-table1", "rowData"),
            Output("offcanvas-control-table1", "columnDefs"),
            Output("altinnedit-option5", "style"),
            Output("altinnedit-option5", "children"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
        )
        def kontrollutslagstabell(selected_row, skjema, *args):
            if (
                selected_row is None
                or len(selected_row) == 0
                or skjema is None
                or any(arg is None for arg in args)
            ):
                return None, None, None, "Se kontrollutslag"
            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                skjemaversjon = selected_row[0]["skjemaversjon"]
                df = self.conn.query(
                    f"""SELECT t1.kontrollid, subquery.skildring, t1.utslag
                    FROM kontrollutslag AS t1
                    JOIN (
                        SELECT t2.kontrollid, t2.skildring
                        FROM kontroller AS t2
                    ) AS subquery ON t1.kontrollid = subquery.kontrollid
                    WHERE skjemaversjon = '{skjemaversjon}'
                    AND utslag = True""",
                    partition_select=create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=skjema,
                        **partition_args,
                    ),
                )
                columns = [{"headerName": col, "field": col} for col in df.columns]
                antall_utslag = len(df)

                if antall_utslag > 0:
                    style = {"color": "#dc3545", "background-color": "#343a40"}
                    button_text = f"Se kontrollutslag ({antall_utslag})"
                else:
                    style = None
                    button_text = "Se kontrollutslag"

                return df.to_dict("records"), columns, style, button_text
            except Exception as e:
                logger.error(f"Error in kontrollutslagstabell: {e}", exc_info=True)
                return None, None, None, "Se kontrollutslag"
