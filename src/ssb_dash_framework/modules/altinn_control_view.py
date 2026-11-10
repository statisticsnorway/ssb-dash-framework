import logging
import threading
import time
from typing import Any, Literal

from dash import html, no_update
from dash import callback, dcc
from dash import callback_context as ctx
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import ibis
from ibis.expr.types.relations import Table

from ..setup.variableselector import VariableSelector
from ..utils import ModuleBase
from ..utils.alert_handler import AlertHandler
from ..utils.config_tools.connection import get_connection

logger = logging.getLogger(__name__)


default_col_def = {
    "filter": True,
    "resizable": True,
    "sortable": True,
    "floatingFilter": True,
    "editable": False,
}


class ControlView(ModuleBase):
    """Provides a layout and functionality for a modal that offers a tabular view of the controls."""

    def __init__(
        self,
        control_dict: dict[str, Any],
        outputs: list[str] | None = None,
    ) -> None:  # TODO add proper annotation for control_dict value
        """Initializes the ControlView with time units, control dictionary, and database connection.

        Args:
            control_dict: A dictionary with one control class per skjema.
            outputs: Variable selector fields to output to. Defaults to ['ident']
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        if outputs is None:
            outputs = ["ident"]

        self.icon = DashIconify(icon="feather:alert-triangle", width=24)
        self.label = "Kontroll"

        self.control_dict = control_dict
        self.outputs = outputs
        self._state = {"running": False, "finished": 0.0}
        super().__init__()

    def layout(self) -> html.Div:
        """
        Defines the layout for the ControlView module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            layout: A Div element containing two tables, kontroller and kontrollutslag.
        """
        layout = html.Div(
            style={"width": "100%"},
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                [
                                    DashIconify(
                                        icon="feather:refresh-cw",
                                        width=18,
                                        className="me-2",
                                    ),
                                    "Oppdater visning",
                                ],
                                id=f"{self.module_number}-kontroll-refresh",
                                className="ssb-btn primary-btn d-flex align-items-center",
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Kjør kontroller (kan ta tid)",
                                id=f"{self.module_number}-kontroll-run-button",
                                className="ssb-btn primary-btn",
                                disabled=False,
                            ),
                            width="auto",
                        ),
                    ],
                    className="g-2 align-items-center",
                ),
                dbc.Row(
                    dbc.Col(
                        dag.AgGrid(
                            id=f"{self.module_number}-kontroller",
                            defaultColDef=default_col_def,
                            className="ag-theme-alpine ag-theme-ssb header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                            rowData=[],
                            dashGridOptions={
                                "loading": False,
                                "pagination": True,
                                "rowSelection": "single",
                                "rowHeight": 28,
                                "overlayNoRowsTemplate": "Trykk «Oppdater visning» for å laste inn kontrollene, "
                                "eller «Kjør kontroller (kan ta tid)» for å kjøre dem på nytt.",
                            },
                            dangerously_allow_code=True,
                        ),
                        width=12,
                    ),
                    className="mt-4",
                ),
                dbc.Row(
                    dbc.Col(
                        dag.AgGrid(
                            id=f"{self.module_number}-kontrollutslag",
                            defaultColDef=default_col_def,
                            className="ag-theme-alpine ag-theme-ssb header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                            rowData=[],
                            dashGridOptions={
                                "pagination": True,
                                "rowSelection": "single",
                                "rowHeight": 28,
                                "overlayNoRowsTemplate": "Velg en kontroll i tabellen over for å se utslagene.",
                                "loading": False,
                            },
                            dangerously_allow_code=True,
                        ),
                        width=12,
                    ),
                    className="mt-4",
                ),
            ],
        )
        return layout

    def _run_all(self, period: Any) -> None:
        time_unit_variable = getattr(VariableSelector._time_unit, "name")
        try:
            for s in list(self.control_dict):
                logger.info(f"\nKjører kontroller for: {s}.")
                instance = self.control_dict[s](
                    time_units=[time_unit_variable],
                    applies_to_subset={
                        "skjema": [s],
                        time_unit_variable: period,
                    },
                )
                try:
                    instance.register_all_controls()
                    instance.execute_controls()
                except ValueError as e:
                    if "No control methods found" not in str(e):
                        logger.error(f"Controls failed for {s}", exc_info=True)
                except Exception:
                    logger.error(f"Controls failed for {s}", exc_info=True)
        finally:
            self._state["running"] = False
            self._state["finished"] = time.time()
            logger.info("Kontrollkjøring ferdig (thread)")

    def module_callbacks(self) -> None:
        """Registers Dash callbacks for the ControlView module."""

        @callback(
            Output("kontroll-poll", "disabled", allow_duplicate=True),
            Output(f"{self.module_number}-kontroll-run-button", "disabled", allow_duplicate=True),
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            VariableSelector.get_timevar(State),
            prevent_initial_call=True,
        )
        def start_controls(click: int | None, period: Any):
            if self._state["running"]:
                AlertHandler.info("Kontroller kjører allerede.", ephemeral=True)
                raise PreventUpdate
            self._state["running"] = True
            AlertHandler.info(
                "Kjører kontroller. Dette kan ta litt tid. Du får beskjed når det er ferdig.",
                ephemeral=True,
            )
            try:
                threading.Thread(
                    target=self._run_all, args=(period,), daemon=True
                ).start()
            except Exception:
                self._state["running"] = False
                raise
            return False, True

        @callback(
            Output("kontroll-done", "data"),
            Output(f"{self.module_number}-kontroll-run-button", "disabled"),
            Output("kontroll-poll", "disabled"),
            Input("kontroll-poll", "n_intervals"),
            State("kontroll-done", "data"),
        )
        def poll(_: int | None, seen: float | None):
            running = self._state["running"]
            finished = self._state["finished"]
            notify = finished if finished and finished != seen else no_update
            return notify, running, not running

        @callback(
            Output(f"{self.module_number}-kontroller", "rowData"),
            Output(f"{self.module_number}-kontroller", "columnDefs"),
            Input(f"{self.module_number}-kontroll-refresh", "n_clicks"),
            Input("kontroll-done", "data"),
            VariableSelector.get_timevar(State),
            prevent_initial_call=True,
        )
        def get_kontroller_overview(
            refresh: int | None,
            kontroller_done,
            period: Any,
        ):
            logger.debug(
                f"Args:\n"
                f"refresh: {refresh}\n"
                f"kontroller_done: {kontroller_done}\n"
                f"period: {period}"
            )
            time_unit_variable: str = getattr(VariableSelector._time_unit, "name")

            logger.debug({time_unit_variable: period})
            defined_schemas = list(self.control_dict.keys())

            with get_connection(
                necessary_tables=["skjemamottak", "kontroller", "kontrollutslag"]
            ) as conn:

                skjemamottak = conn.table("skjemamottak")
                skjemamottak = skjemamottak.filter(
                    (skjemamottak[time_unit_variable] == period)
                    & (skjemamottak.skjema.isin(defined_schemas))
                    & (skjemamottak.aktiv == True)
                )

                if "status" in skjemamottak.columns:
                    status_column, status_value = "status", "Ubehandlet"
                    status_filter = (
                        skjemamottak[status_column].cast("string") == status_value
                    )
                else:
                    status_column, status_value = "editert", False
                    status_filter = skjemamottak[status_column] == status_value

                kontroller = conn.table("kontroller").filter(
                    (conn.table("kontroller")[time_unit_variable] == period)
                    & (conn.table("kontroller").skjema.isin(defined_schemas))
                )

                kontrollutslag = conn.table("kontrollutslag").filter(
                    (conn.table("kontrollutslag")[time_unit_variable] == period)
                    & (conn.table("kontrollutslag").skjema.isin(defined_schemas))
                )

                # only unedited
                subq = (
                    skjemamottak.filter(status_filter).select(
                        "ident", "refnr", "skjema"
                    )
                ).distinct()

                # only active
                aktive = skjemamottak.select("ident", "refnr", "skjema").distinct()

                utslag = (
                    kontrollutslag.join(
                        aktive,
                        (kontrollutslag.ident == aktive.ident)
                        & (kontrollutslag.refnr == aktive.refnr)
                        & (kontrollutslag.skjema == aktive.skjema),
                    )
                    .filter(kontrollutslag.utslag == True)
                    .group_by([kontrollutslag.skjema, kontrollutslag.kontrollid])
                    .aggregate(ant_utslag=ibis._.count())
                )

                uediterte = (
                    kontrollutslag.join(
                        subq,
                        (kontrollutslag.ident == subq.ident)
                        & (kontrollutslag.refnr == subq.refnr)
                        & (kontrollutslag.skjema == subq.skjema),
                    )
                    .filter(kontrollutslag.utslag == True)
                    .group_by([kontrollutslag.skjema, kontrollutslag.kontrollid])
                    .aggregate(uediterte=ibis._.count())
                    .select("skjema", "kontrollid", "uediterte")
                )

                result = (
                    kontroller.left_join(
                        utslag,
                        (kontroller.skjema == utslag.skjema)
                        & (kontroller.kontrollid == utslag.kontrollid),
                    )
                    .left_join(
                        uediterte,
                        (kontroller.skjema == uediterte.skjema)
                        & (kontroller.kontrollid == uediterte.kontrollid),
                    )
                    .select(
                        kontroller.skjema,
                        kontroller.kontrollid,
                        kontroller.type,
                        kontroller.beskrivelse,
                        kontroller.sorting_var,
                        kontroller.sorting_order,
                        utslag.ant_utslag.fill_null(0).name("ant_utslag"),
                        uediterte.uediterte.fill_null(0).name("uediterte"),
                    )
                )
                result = result.filter(
                    result.ant_utslag != 0
                )  # hide those with no output
                result = result.to_pandas().sort_values(
                    by=["ant_utslag", "kontrollid"], ascending=[False, True]
                )
                columns = [
                    {
                        "headerName": col,
                        "field": col,
                        "hide": col == "sorting_order",
                        "flex": 2 if col == "beskrivelse" else 1,
                        "tooltipField": col if col == "beskrivelse" else None,
                    }
                    for col in result.columns
                ]
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True

                AlertHandler.info("Kontrollvisning oppdatert.", ephemeral=True)

                return result.to_dict("records"), columns

        @callback(
            Input("kontroll-done", "data"),
            prevent_initial_call=True,
        )
        def notify_kontroller_done(finished):
            if finished:
                AlertHandler.info("Kontrollkjøring ferdig.", ephemeral=True)

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-kontrollutslag", "rowData"),
            Output(f"{self.module_number}-kontrollutslag", "columnDefs"),
            Input(f"{self.module_number}-kontroller", "selectedRows"),
            VariableSelector.get_timevar(State),
        )
        def get_kontrollutslag(current_row: list[dict[Any, Any]], period: Any):
            logger.debug(f"Args:\ncurrent_row: {current_row}\nperiod: {period}")
            if current_row is None or len(current_row) == 0:
                logger.debug("No current_row, raising PreventUpdate.")
                raise PreventUpdate
            with get_connection(
                necessary_tables=["skjemamottak", "kontrollutslag"]
            ) as conn:
                kontrollid = current_row[0]["kontrollid"]
                skjema = current_row[0]["skjema"]
                sorting_var = current_row[0]["sorting_var"]
                sorting_order = current_row[0]["sorting_order"]
                time_unit_variable: str = getattr(VariableSelector._time_unit, "name")

                logger.debug(
                    f"Variables from current_row:\nkontrollid: {kontrollid}\nsorting_var: {sorting_var}\nsorting_order: {sorting_order}"
                )
                if sorting_order is None:
                    sorting_order = "DESC"
                skjemamottak = conn.table("skjemamottak")
                status_column: Literal["status", "editert"] = (
                    "status" if "status" in skjemamottak.columns else "editert"
                )

                # subquery: filter active rows in skjemamottak
                s: Table = (
                    skjemamottak.filter(
                        (skjemamottak.aktiv == True)
                        & (skjemamottak[time_unit_variable] == period)
                        & (skjemamottak.skjema == skjema)
                    )
                    .select(
                        skjemamottak.refnr,
                        skjemamottak[status_column],
                        skjemamottak.ident,
                    )
                    .distinct()
                )

                kontrollutslag = conn.table("kontrollutslag")
                kontrollutslag = kontrollutslag.filter(
                    (kontrollutslag[time_unit_variable] == period)
                    & (kontrollutslag.skjema == skjema)
                )

                result = (
                    kontrollutslag.join(
                        s,
                        (kontrollutslag.refnr == s.refnr)
                        & (kontrollutslag.ident == s.ident),
                    )
                    .filter(
                        (kontrollutslag.kontrollid == kontrollid)
                        & (kontrollutslag.utslag == True)
                    )
                    .select(
                        kontrollutslag.ident,
                        kontrollutslag.refnr,
                        kontrollutslag.kontrollid,
                        kontrollutslag.utslag,
                        s[status_column],
                        kontrollutslag.verdi,
                    )
                    .order_by(s[status_column], kontrollutslag.verdi)
                )
                result = result.to_pandas()

            columns = [{"headerName": col, "field": col} for col in result.columns]
            columns[0]["checkboxSelection"] = True
            columns[0]["headerCheckboxSelection"] = True
            return result.to_dict("records"), columns

        @callback(
            *[VariableSelector.get_output_object(output) for output in self.outputs],
            Input(f"{self.module_number}-kontrollutslag", "selectedRows"),
            prevent_initial_call="initial_duplicate",
        )
        def output_to_varselector(
            selected_row: list[dict[Any, Any]],
        ) -> Any | tuple[Any]:

            logger.debug(f"Selected row:\n{selected_row}")
            if not selected_row:
                logger.debug("Raising PreventUpdate due to selected_row being None")
                raise PreventUpdate
            if len(selected_row) > 1:
                raise ValueError(
                    "Too many rows selected, logic won't work with more than one row."
                )

            if len(self.outputs) == 1:

                return selected_row[0][self.outputs[0]]
            elif len(self.outputs) > 1:

                return tuple(selected_row[0][output] for output in self.outputs)
            else:
                raise ValueError(
                    f"Something is wrong with 'self.outputs'. Should be a list with at least one string inside of it. Is currently: {self.outputs}"
                )
