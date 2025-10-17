import logging
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorControl:
    """Module for viewing control results for the selected observation in the Altinn Editor."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor Control module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
            AssertionError: If the connection object does not have a 'query' method.
        """
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variableselector = variable_selector_instance
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def _create_layout(self) -> html.Div:
        """Creates the layout for the Altinn Editor Control module."""
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

    def layout(self) -> html.Div:
        """Returns the layout of the Altinn Editor Control module."""
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
                            className="ag-theme-alpine header-style-on-filter",
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

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Altinn Editor Control module."""

        @callback(  # type: ignore[misc]
            Output("offcanvas-control", "is_open"),
            Input("altinnedit-option5", "n_clicks"),
            State("offcanvas-control", "is_open"),
        )
        def toggle_offcanvas_kontrollutslag(
            n_clicks: None | int, is_open: bool
        ) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("offcanvas-control-table1", "rowData"),
            Output("offcanvas-control-table1", "columnDefs"),
            Output("altinnedit-option5", "style"),
            Output("altinnedit-option5", "children"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            State("altinnedit-skjemaer", "value"),
            self.variableselector.get_all_states(),
        )
        def kontrollutslagstabell(
            selected_row: list[dict[str, int | float | str]], skjema: str, *args: Any
        ) -> tuple[
            list[dict[str, Any]] | None,
            list[dict[str, str | bool]] | None,
            dict[str, str] | None,
            str,
        ]:
            logger.debug(
                f"Args:\n"
                f"selected_row: {selected_row}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )
            if (
                selected_row is None
                or len(selected_row) == 0
                or skjema is None
                or any(arg is None for arg in args)
            ):
                return None, None, None, "Se kontrollutslag"
            try:
                partition_args = dict(zip(self.time_units, args, strict=False))
                refnr = selected_row[0]["refnr"]
                df = self.conn.query(
                    f"""SELECT t1.kontrollid, subquery.skildring, t1.utslag
                    FROM kontrollutslag AS t1
                    JOIN (
                        SELECT t2.kontrollid, t2.skildring
                        FROM kontroller AS t2
                    ) AS subquery ON t1.kontrollid = subquery.kontrollid
                    WHERE refnr = '{refnr}'
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
