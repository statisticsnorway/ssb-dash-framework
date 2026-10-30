import logging

from typing import Any, Literal

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import ibis
from dash import callback
from dash import callback_context as ctx
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

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
        # time_units: list[str],
        control_dict: dict[str, Any],
        outputs: list[str] | None = None,
    ) -> None:  # TODO add proper annotation for control_dict value
        """Initializes the ControlView with time units, control dictionary, and database connection.

        Args:
            time_units: A list of the time units used.
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
        super().__init__()

    def layout(self) -> html.Div:
        """Generates the layout for the ControlView module.

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
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            html.P(
                                id=f"{self.module_number}-kontroll-var",
                                className="mb-0",
                            )
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

    def module_callbacks(self) -> None:
        """Registers Dash callbacks for the ControlView module."""

        @callback(
            Output(f"{self.module_number}-kontroll-var", "children"),
            VariableSelector.get_input("altinnskjema"),
            VariableSelector.get_timevar(Input),
        )
        def kontroller_show_selected_controls(skjema: str | None, period: str | None):
            logger.debug(f"Args:\nskjema: {skjema}\nperiod: {period}")
            time_unit_variable: str = getattr(VariableSelector._time_unit, "name")
            partition_args = {time_unit_variable: period}
            if skjema is not None:
                valgte_vars = f"valgt partisjon: {partition_args}\nvalgt skjema: {skjema if skjema else 'Velg skjema for å starte'}"
                return valgte_vars

        @callback(
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            prevent_initial_call=True,
        )
        def alert_user_of_controls(click: int | None):
            AlertHandler.info(
                "Kjører kontroller, dette kan ta litt tid, du får beskjed når den er ferdig. Ikke klikk på knappen igjen.",
                ephemeral=True,
                duration=10,
            )

        @callback(
            Output(f"{self.module_number}-kontroller", "rowData"),
            Output(f"{self.module_number}-kontroller", "columnDefs"),
            Input(f"{self.module_number}-kontroll-refresh", "n_clicks"),
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            VariableSelector.get_timevar(Input),
            prevent_initial_call=True,
        )
        def get_kontroller_overview(
            refresh: int | None,
            rerun: int | None,
            period: Any,
        ):
            logger.debug(
                f"Args:\n"
                f"refresh: {refresh}\n"
                f"rerun: {rerun}\n"
                f"period: {period}"
            )
            time_unit_variable: str = getattr(VariableSelector._time_unit, "name")

            logger.debug({time_unit_variable: period})
            defined_schemas = list(self.control_dict.keys())
            if (
                ctx.triggered_id == f"{self.module_number}-kontroll-run-button"
            ):  # TODO: Possibly better to replace with background callback.
                logger.info("Running controls")

                for s in defined_schemas:
                    control_class_instance = self.control_dict[s](
                        time_units=[time_unit_variable],
                        applies_to_subset={"skjema": [s], time_unit_variable: period},
                    )
                    try:
                        control_class_instance.register_all_controls()
                        control_class_instance.execute_controls()
                    except ValueError as e:
                        if "No control methods found" in str(e):
                            logger.info(f"No control methods found for {s}.")
                        else:
                            raise e
            else:
                logger.info("Refreshing view without re-running controls.")
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
                    skjemamottak.filter(status_filter)
                    .select("ident", "refnr")
                ).distinct()

                # only active 
                aktive = skjemamottak.select("ident", "refnr").distinct()

                utslag = (
                    kontrollutslag.join(
                        aktive,
                        (kontrollutslag.ident == aktive.ident)
                        & (kontrollutslag.refnr == aktive.refnr),
                    )
                    .filter(kontrollutslag.utslag == True)
                    .group_by([kontrollutslag.skjema, kontrollutslag.kontrollid])
                    .aggregate(ant_utslag=ibis._.count())
                )

                uediterte = (
                    kontrollutslag.join(
                        subq,
                        (kontrollutslag.ident == subq.ident)
                        & (kontrollutslag.refnr == subq.refnr),
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
                if ctx.triggered_id == f"{self.module_number}-kontroll-run-button":
                    AlertHandler.info(
                        f"Kontrollkjøring ferdig for {len(defined_schemas)} skjemaer",
                        ephemeral=True,
                    )
                else:
                    AlertHandler.info("Kontrollvisning oppdatert.")

                return result.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-kontrollutslag", "rowData"),
            Output(f"{self.module_number}-kontrollutslag", "columnDefs"),
            Input(f"{self.module_number}-kontroller", "selectedRows"),
            VariableSelector.get_timevar(Input),
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

                # Subquery: filter active rows in skjemamottak
                s = skjemamottak.filter(skjemamottak.aktiv == True).select(
                    skjemamottak.refnr,
                    skjemamottak[status_column],
                    skjemamottak.ident,
                )

                print("skjemamottak check for 152cc8ee3435:")
                print(s.filter(s.refnr == "152cc8ee3435"))

                kontrollutslag = conn.table("kontrollutslag")
                # Main query
                result = (
                    kontrollutslag.join(
                        s,
                        (kontrollutslag.refnr == s.refnr)
                        & (kontrollutslag.ident == s.ident),
                    )
                    .filter(
                        (kontrollutslag.kontrollid == kontrollid)
                        & (kontrollutslag.skjema == skjema)
                        & (kontrollutslag[time_unit_variable] == period)
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

            print("result check for 152cc8ee3435:")
            print(result.filter(result.refnr == "152cc8ee3435"))
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
