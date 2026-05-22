import logging

import dash_ag_grid as dag
import pandas as pd
import tzlocal
from dash import Input
from dash import Output
from dash import callback
from dash import html
from ibis import _
from psycopg_pool import ConnectionPool
import dash_bootstrap_components as dbc

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_refnr
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units

from .....utils.config_tools.connection import _get_connection_object
from .....utils.config_tools.connection import get_connection
from ..core import DataEditorHelperButton

logger = logging.getLogger(__name__)

local_tz = tzlocal.get_localzone()


class DataEditorHistory(DataEditorHelperButton):
    """This module provides supporting tables for the DataEditor.

    It adds a button that opens a modal with tabs containing tables with extra informatiion.

    Note:
        Adding your own supporting tables is not supported at this time.
    """

    _id_number = 0

    def __init__(
        self,
        applies_to_tables: list[str] | None = None,
        applies_to_forms: list[str] | None = None,
    ) -> None:
        """Initializes the DataEditorEditorSupportTables module."""
        self.module_number = DataEditorHistory._id_number
        self.module_name = self.__class__.__name__
        DataEditorHistory._id_number += 1
        self.variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[get_refnr(), *[x for x in get_time_units().keys()]],
        )
        self.modal_body = self._create_modal_body()

        super().__init__(label="Historikk")

        self.module_callbacks()

    def _create_modal_body(self) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        dbc.Label("Skjul insert-data"),
                        dbc.Checklist(
                            options=[{"label": "Altinn3", "value": 1}],
                            value=[1],
                            id=f"{self.module_name}-{self.module_number}-toggle",
                            inline=True,
                            switch=True,
                        ),
                    ],
                    className=f"{self.module_name}-toggle-bar",
                ),
                html.Div(
                    dag.AgGrid(
                        id=f"{self.module_name}-{self.module_number}-table",
                        dashGridOptions={"enableCellTextSelection": True},
                        defaultColDef={"filter": True, "resizable": True},
                        columnSize="responsiveSizeToFit",
                    ),
                    className=f"{self.module_name}-table",
                ),
            ],
            className=f"{self.module_name}-body",
        )

    def module_callbacks(self):
        connection_object = _get_connection_object()

        @callback(
            Output(f"{self.module_name}-{self.module_number}-table", "rowData"),
            Output(f"{self.module_name}-{self.module_number}-table", "columnDefs"),
            Input(f"{self.module_name}-{self.module_number}-modal", "is_open"),
            Input(f"{self.module_name}-{self.module_number}-toggle", "value"),
            *self.variableselector.get_all_callback_objects(),
        )
        def update_history_view(is_open, insert_toggle: bool, refnr, *args):

            if isinstance(connection_object, ConnectionPool):
                logger.debug("Using ConnectionPool logic.")
                with get_connection() as conn:
                    t = conn.table("skjemadataendringshistorikk")
                    query = t.filter(_.refnr == refnr).order_by(_.endret_tid.desc())
                    if insert_toggle:
                        query = query.filter(
                            _.process_type != "Altinn3"
                        )  # Filtering here to not show the original insert in the history table as the original data will be visible as "old value" in the changelog.
                    df = query.to_pandas()
                    df["endret_tid"] = (
                        pd.to_datetime(df["endret_tid"], utc=True)
                        .dt.tz_convert(local_tz)
                        .dt.floor("s")
                        .dt.tz_localize(None)
                        .dt.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    columns = [
                        {
                            "headerName": col,
                            "field": col,
                            "filter": True,
                            "resizable": True,
                            "hide": col
                            in [
                                "skjema",
                                "refnr",
                            ],
                        }
                        for col in df.columns
                    ]
                    return df.to_dict("records"), columns
            # elif isinstance(connection_object, EimerDBInstance):
            #     try:
            #         partition_args = dict(zip([x for x in get_time_units().keys()], args, strict=False))
            #         df = connection_object.query_changes(
            #             f"""SELECT * FROM {tabell}
            #             WHERE refnr = '{refnr}'
            #             ORDER BY datetime DESC
            #             """,
            #             partition_select=create_partition_select(
            #                 desired_partitions=self.time_units,
            #                 skjema=skjema,
            #                 **partition_args,
            #             ),
            #         )
            #         if df is None:
            #             df = pd.DataFrame(columns=["ingen", "data"])
            #         columns = [
            #             {
            #                 "headerName": col,
            #                 "field": col,
            #                 "filter": True,
            #                 "resizable": True,
            #             }
            #             for col in df.columns
            #         ]
            #         return df.to_dict("records"), columns
            #     except Exception as e:
            #         logger.error(f"Error in historikktabell: {e}", exc_info=True)
            #         return None, None
            else:
                raise NotImplementedError(
                    f"Connection of type {type(connection_object)} is not currently supported."
                )
