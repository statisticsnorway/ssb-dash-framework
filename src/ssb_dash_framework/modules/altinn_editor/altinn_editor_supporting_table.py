import logging
import re
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ...setup.variableselector import VariableSelector
from ...utils.eimerdb_helpers import SQL_COLUMN_CONCAT
from ...utils.eimerdb_helpers import create_partition_select

logger = logging.getLogger(__name__)


class AltinnEditorSupportTables:
    """This module provides supporting tables for the Altinn editor.

    It adds a button that opens a modal with tabs containing tables with extra informatiion.

    Note:
        Adding your own supporting tables is not supported at this time.
    """

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: dict[str, str],
    ) -> None:
        """Initializes the AltinnEditorSupportTables module.

        Args:
            time_units (list[str]): List of time units to be used in the module.
            conn (object): Database connection object.
            variable_selector_instance (VariableSelector): Instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
        """
        assert hasattr(
            conn, "query"
        ), (  # Necessary because of mypy
            "The database object must have a 'query' method."
        )
        self.time_units = time_units
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def support_tables_modal(self) -> dbc.Modal:
        """Return a modal component containing tab content."""
        hjelpetabellmodal = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Hjelpetabeller")),
                dbc.ModalBody(
                    html.Div(
                        [
                            html.P("Velg hvilken tidsenhet som skal rullere -1:"),
                            dcc.Dropdown(
                                id="skjemadata-hjelpetablellmodal-dd",
                                options=[
                                    {"label": unit, "value": unit}
                                    for unit in self.time_units
                                ],
                                value=self.time_units[0] if self.time_units else None,
                                clearable=False,
                                className="dbc",
                            ),
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        self.create_ag_grid(
                                            "skjemadata-hjelpetabellmodal-table1"
                                        ),
                                        tab_id="modal-hjelpetabeller-tab1",
                                        label="Endringer",
                                    ),
                                    dbc.Tab(
                                        self.create_ag_grid(
                                            "skjemadata-hjelpetabellmodal-table2"
                                        ),
                                        tab_id="modal-hjelpetabeller-tab2",
                                        label="Tabell2",
                                    ),
                                ],
                                id="skjemadata-hjelpetabellmodal-tabs",
                            ),
                        ],
                    ),
                ),
            ],
            id="skjemadata-hjelpetabellmodal",
            is_open=False,
            size="xl",
        )
        logger.debug("Created support tables modal")
        return hjelpetabellmodal

    def create_ag_grid(self, component_id: str) -> dag.AgGrid:
        """Returns a non-editable AgGrid component with a dark alpine theme."""
        return dag.AgGrid(
            defaultColDef={"editable": False},
            id=component_id,
            className="ag-theme-alpine-dark header-style-on-filter",
        )

    def _create_layout(self) -> html.Div:
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label(
                            "Hjelpetabeller",
                            className="mb-1",
                        ),
                        dbc.Button(
                            "Se hjelpetabeller",
                            id="altinn-support-tables-button",
                            className="w-100",
                        ),
                    ]
                ),
                self.support_tables_modal(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout for the Altinn Editor Support Tables module."""
        return self.module_layout

    def update_partition_select(
        self, partition_dict: dict[str, list[int]], key_to_update: str
    ) -> dict[str, list[int]]:
        """Updates the dictionary by adding the previous value (N-1) to the list for a single specified key.

        :param partition_dict: Dictionary containing lists of values
        :param key_to_update: Key to update by appending (N-1)
        :return: Updated dictionary
        """
        if partition_dict.get(key_to_update):
            min_value = min(partition_dict[key_to_update])
            partition_dict[key_to_update].append(int(min_value) - 1)
        return partition_dict

    def module_callbacks(self) -> None:
        """Registers the callbacks for the Altinn Editor Support Tables module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-hjelpetabellmodal", "is_open"),
            Input("altinn-support-tables-button", "n_clicks"),
            State("skjemadata-hjelpetabellmodal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks: None | int, is_open: bool) -> bool:
            if n_clicks is None:
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-hjelpetabellmodal-table1", "rowData"),
            Output("skjemadata-hjelpetabellmodal-table1", "columnDefs"),
            Input("skjemadata-hjelpetabellmodal-tabs", "active_tab"),
            Input("altinnedit-table-skjemaer", "selectedRows"),
            Input("skjemadata-hjelpetablellmodal-dd", "value"),
            State("altinnedit-option1", "value"),
            State("altinnedit-ident", "value"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
            prevent_initial_call=True,
        )
        def hjelpetabeller(
            tab: str,
            selected_row: list[dict[str, int | float | str]],
            rullerende_var: str,
            tabell: str,
            ident: str,
            skjema: str,
            *args: Any,
        ) -> tuple[list[dict[str, Any]], list[dict[str, str | bool]]]:
            if tab == "modal-hjelpetabeller-tab1":
                try:
                    partition_args = dict(zip(self.time_units, args, strict=False))
                    partition_select = create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=skjema,
                        **partition_args,
                    )
                    partition_select_no_skjema = create_partition_select(
                        desired_partitions=self.time_units,
                        skjema=None,
                        **partition_args,
                    )
                    updated_partition_select = self.update_partition_select(
                        partition_select, rullerende_var
                    )
                    column_name_expr_outer = SQL_COLUMN_CONCAT.join(
                        [f"s.{unit}" for unit in self.time_units]
                    )
                    column_name_expr_inner = SQL_COLUMN_CONCAT.join(
                        [f"t2.{unit}" for unit in self.time_units]
                    )

                    group_by_clause = ", ".join(
                        [f"s.{unit}" for unit in self.time_units]
                    )

                    query = f"""
                        SELECT
                            s.variabel,
                            {column_name_expr_outer} AS time_combination,
                            SUM(CAST(s.verdi AS NUMERIC)) AS verdi
                        FROM {tabell} AS s
                        JOIN (
                            SELECT
                                {column_name_expr_inner} AS time_combination,
                                t2.ident,
                                t2.skjemaversjon,
                                t2.dato_mottatt
                            FROM
                                skjemamottak AS t2
                            WHERE aktiv = True
                            QUALIFY
                                ROW_NUMBER() OVER (PARTITION BY time_combination, t2.ident ORDER BY t2.dato_mottatt DESC) = 1
                        ) AS mottak_subquery ON
                            {column_name_expr_outer} = mottak_subquery.time_combination
                            AND s.ident = mottak_subquery.ident
                            AND s.skjemaversjon = mottak_subquery.skjemaversjon
                        JOIN (
                        SELECT * FROM datatyper AS d
                        ) AS subquery ON s.variabel = subquery.variabel
                        WHERE s.ident = '{ident}' AND subquery.datatype = 'int'
                        GROUP BY s.variabel, subquery.radnr, {group_by_clause}
                        ORDER BY subquery.radnr
                        ;
                    """

                    df = self.conn.query(
                        query.format(ident=ident),
                        partition_select={
                            tabell: updated_partition_select,
                            "datatyper": partition_select_no_skjema,
                        },
                    )

                    df_wide = df.pivot(
                        index="variabel", columns="time_combination", values="verdi"
                    ).reset_index()

                    df_wide = df_wide.rename(
                        columns={
                            col: f"verdi_{col}" if col != "variabel" else col
                            for col in df_wide.columns
                        }
                    )

                    df_wide.columns.name = None

                    def extract_numeric_sum(col_name: str) -> int | float:
                        numbers = list(map(int, re.findall(r"\d+", col_name)))
                        return sum(numbers) if numbers else 0

                    time_columns_sorted = sorted(
                        [col for col in df_wide.columns if col.startswith("verdi_")],
                        key=extract_numeric_sum,
                    )

                    if len(time_columns_sorted) >= 2:
                        latest_col = max(time_columns_sorted, key=extract_numeric_sum)
                        prev_col = min(time_columns_sorted, key=extract_numeric_sum)
                        df_wide["diff"] = df_wide[latest_col] - df_wide[prev_col]
                        df_wide["pdiff"] = (df_wide["diff"] / df_wide[prev_col]) * 100
                        df_wide["pdiff"] = df_wide["pdiff"].round(2).astype(str) + " %"
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                        }
                        for col in df_wide.columns
                    ]
                    return df_wide.to_dict("records"), columns
                except Exception as e:
                    logger.error(f"Error in hjelpetabeller: {e}", exc_info=True)
                    raise PreventUpdate from e
            else:
                raise PreventUpdate
