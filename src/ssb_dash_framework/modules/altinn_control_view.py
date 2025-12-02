# TODO: Rewrite to window/tab implementation model

import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import ibis
from dash import callback
from dash import callback_context as ctx
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.exceptions import PreventUpdate
from eimerdb import EimerDBInstance

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.core_query_functions import conn_is_ibis
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)


default_col_def = {
    "filter": True,
    "resizable": True,
    "sortable": True,
    "floatingFilter": True,
    "editable": False,
}


class AltinnControlView(ABC):
    """Provides a layout and functionality for a modal that offers a tabular view of the controls."""

    _id_number: int = 0

    def __init__(
        self,
        time_units: list[str],
        control_dict: dict[str, Any],
        conn: object,
        outputs: list[str] | None = None,
    ) -> None:  # TODO add proper annotation for control_dict value
        """Initializes the AltinnControlView with time units, control dictionary, and database connection.

        Args:
            time_units (list): A list of the time units used.
            control_dict (dict): A dictionary with one control class per skjema.
            conn (object): The eimerdb connection.
            outputs (list[str] | None): Variable selector fields to output to. Defaults to ['ident']
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        if outputs is None:
            outputs = ["ident"]
        assert hasattr(
            conn, "query"
        ), "The database connection object must have a 'query' method."
        self.module_number = AltinnControlView._id_number
        self.module_name = self.__class__.__name__
        AltinnControlView._id_number += 1

        self.icon = "⚠️"
        self.label = "Kontroll"

        self.control_dict = control_dict
        self.conn = conn
        self.outputs = outputs
        self._is_valid()
        self.module_layout = self.create_layout()
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.module_callbacks()
        module_validator(self)

    def _is_valid(self) -> None:
        VariableSelector([], []).get_option("var-altinnskjema", search_target="id")
        VariableSelector([], []).get_option("var-ident", search_target="id")

    def create_layout(self) -> html.Div:
        """Generates the layout for the AltinnControlView module.

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
                                "🔄 Oppdater visning",
                                id=f"{self.module_number}-kontroll-refresh",
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Kjør kontroller (kan ta tid)",
                                id=f"{self.module_number}-kontroll-run-button",
                            ),
                            width="auto",
                        ),
                        dbc.Col(html.P(id=f"{self.module_number}-kontroll-var")),
                    ],
                    className="g-2",
                ),
                dbc.Row(
                    dag.AgGrid(
                        id=f"{self.module_number}-kontroller",
                        defaultColDef=default_col_def,
                        className="ag-theme-alpine header-style-on-filter",
                        columnSize="responsiveSizeToFit",
                        dashGridOptions={
                            "pagination": True,
                            "rowSelection": "single",
                            "rowHeight": 28,
                        },
                    ),
                    style={"flexShrink": 0},
                ),
                html.Hr(),
                dbc.Row(
                    dbc.Col(
                        dag.AgGrid(
                            id=f"{self.module_number}-kontrollutslag",
                            defaultColDef=default_col_def,
                            className="ag-theme-alpine header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={
                                "pagination": True,
                                "rowSelection": "single",
                                "rowHeight": 28,
                            },
                        ),
                        width=12,
                    )
                ),
            ],
        )
        return layout

    @abstractmethod
    def layout(self) -> html.Div:
        """Defines the layout for the AltinnControlView module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:
        """Registers Dash callbacks for the AltinnControlView module."""

        @callback(
            Output(f"{self.module_number}-kontroll-var", "children"),
            Input("var-altinnskjema", "value"),
            self.variableselector.get_all_inputs(),
        )
        def kontroller_show_selected_controls(skjema: str, *args: Any):
            logger.debug(f"Args:\nskjema: {skjema}\nargs: {args}")
            partition_args = dict(zip(self.time_units, args, strict=False))
            if partition_args is not None and skjema is not None:
                valgte_vars = (
                    f"valgt partisjon: {partition_args}\nvalgt skjema: {skjema}"
                )
                return valgte_vars

        @callback(
            Output(f"{self.module_number}-kontroller", "rowData"),
            Output(f"{self.module_number}-kontroller", "columnDefs"),
            Input("var-altinnskjema", "value"),
            Input(f"{self.module_number}-kontroll-refresh", "n_clicks"),
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            *self.variableselector.get_all_inputs(),
        )
        def get_kontroller_overview(
            skjema: str, refresh: int | None, rerun: int | None, *args: Any
        ):
            logger.debug(
                f"Args:\n"
                f"skjema: {skjema}\n"
                f"refresh: {refresh}\n"
                f"rerun: {rerun}\n"
                f"args: {args}"
            )
            if isinstance(self.conn, EimerDBInstance):
                args = [int(arg) for arg in args]
            logger.debug(dict(zip(self.time_units, args, strict=False)))
            control_class_instance = self.control_dict[skjema](
                time_units=self.time_units,
                applies_to_subset=dict(zip(self.time_units, args, strict=False))
                | {"skjema": [skjema]},
                conn=self.conn,
            )
            if (
                ctx.triggered_id == f"{self.module_number}-kontroll-run-button"
            ):  # TODO: Possibly better to replace with background callback.
                logger.info("Running controls")
                try:
                    control_class_instance.register_all_controls()
                    control_class_instance.execute_controls()
                except ValueError as e:
                    if str(e) == "No control methods found.":
                        logger.info("No control methods found.")
                        # Return alert handler stuff
                    else:
                        raise
            else:
                logger.info("Refreshing view without re-running controls.")

            if isinstance(self.conn, EimerDBInstance):
                conn = ibis.polars.connect()
                skjemamottak = self.conn.query(
                    "SELECT * FROM skjemamottak"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("skjemamottak", skjemamottak)
                kontroller = self.conn.query(
                    "SELECT * FROM kontroller"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("kontroller", kontroller)
                kontrollutslag = self.conn.query(
                    "SELECT * FROM kontrollutslag"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("kontrollutslag", kontrollutslag)
            elif conn_is_ibis(self.conn):
                conn = self.conn
            else:
                raise NotImplementedError(
                    f"Connection type '{type(self.conn)}' is currently not implemented."
                )
            skjemamottak = conn.table("skjemamottak")
            kontroller = conn.table("kontroller")
            kontrollutslag = conn.table("kontrollutslag")

            utslag = (
                kontrollutslag.filter(kontrollutslag.utslag == True)
                .group_by(kontrollutslag.kontrollid)
                .aggregate(ant_utslag=kontrollutslag.row_id.count())
            )

            subq = (
                skjemamottak.filter(skjemamottak.aktiv == True)
                .filter(skjemamottak.editert == False)
                .select("ident", "refnr")
            )

            uediterte = (
                kontrollutslag.join(
                    subq,
                    (kontrollutslag.ident == subq.ident)
                    & (kontrollutslag.refnr == subq.refnr),
                )
                .filter(kontrollutslag.utslag == True)
                .group_by(kontrollutslag.kontrollid)
                .aggregate(uediterte=kontrollutslag.row_id.count())
                .select("kontrollid", "uediterte")
            )

            result = (
                kontroller.join(utslag, kontroller.kontrollid == utslag.kontrollid)
                .join(uediterte, kontroller.kontrollid == uediterte.kontrollid)
                .select(
                    kontroller.skjema,
                    kontroller.kontrollid,
                    kontroller.type,
                    kontroller.skildring,
                    kontroller.kontrollvar,
                    kontroller.varsort,
                    utslag.ant_utslag,
                    uediterte.uediterte,
                )
            )
            result = result.to_pandas()
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": col == "varsort",
                    "flex": 2 if col == "skildring" else 1,
                    "tooltipField": col if col == "skildring" else None,
                }
                for col in result.columns
            ]
            columns[0]["checkboxSelection"] = True
            columns[0]["headerCheckboxSelection"] = True
            return result.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-kontrollutslag", "rowData"),
            Output(f"{self.module_number}-kontrollutslag", "columnDefs"),
            Input(f"{self.module_number}-kontroller", "selectedRows"),
            self.variableselector.get_all_inputs(),
            #            *self.create_callback_components("State"),
        )
        def get_kontrollutslag(current_row: list[dict[Any, Any]], *args: Any):
            logger.debug(f"Args:\ncurrent_row: {current_row}\nargs: {args}")
            if current_row is None or len(current_row) == 0:
                logger.debug("No current_row, raising PreventUpdate.")
                raise PreventUpdate
            if isinstance(self.conn, EimerDBInstance):
                conn = ibis.polars.connect()
                skjemamottak = self.conn.query(
                    "SELECT * FROM skjemamottak"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("skjemamottak", skjemamottak)
                kontrollutslag = self.conn.query(
                    "SELECT * FROM kontrollutslag"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("kontrollutslag", kontrollutslag)
            elif conn_is_ibis(self.conn):
                conn = self.conn
            else:
                raise NotImplementedError(
                    f"Connection type '{type(self.conn)}' is currently not implemented."
                )
            kontrollid = current_row[0]["kontrollid"]
            kontrollvar = current_row[0]["kontrollvar"]
            skjema = current_row[0]["skjema"]
            varsort = current_row[0]["varsort"]

            logger.debug(
                f"Variables from current_row:\nkontrollid: {kontrollid}\nkontrollvar: {kontrollvar}\nskjema: {skjema}\nvarsort: {varsort}"
            )
            if varsort is None:
                varsort = "DESC"
            skjemamottak = conn.table("skjemamottak")
            kontrollutslag = conn.table("kontrollutslag")
            # Subquery: filter active rows in skjemamottak
            s = skjemamottak.filter(skjemamottak.aktiv == True).select(
                skjemamottak.refnr,
                skjemamottak.editert,
                skjemamottak.ident,
            )

            # Main query
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
                    s.editert,
                    kontrollutslag.verdi,
                )
                .order_by(s.editert, kontrollutslag.verdi)
            )
            result = result.to_pandas()
            columns = [{"headerName": col, "field": col} for col in result.columns]
            columns[0]["checkboxSelection"] = True
            columns[0]["headerCheckboxSelection"] = True
            return result.to_dict("records"), columns

        @callback(
            *[
                self.variableselector.get_output_object(output)
                for output in self.outputs
            ],
            Input(f"{self.module_number}-kontrollutslag", "selectedRows"),
            prevent_initial_call="initial_duplicate",
        )
        def output_to_varselector(
            selected_row: list[dict[Any, Any]],
        ) -> Any | tuple[Any]:
            logger.debug(f"Selected row:\n{selected_row}")
            if selected_row is None:
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


class AltinnControlViewTab(TabImplementation, AltinnControlView):
    """AltinnControlView implemented as a tab."""

    def __init__(
        self, time_units: list[str], control_dict: dict[str, Any], conn: object
    ) -> None:
        """Initializes the AltinnControlViewTab module."""
        AltinnControlView.__init__(
            self,
            time_units=time_units,
            control_dict=control_dict,
            conn=conn,
        )
        TabImplementation.__init__(self)


class AltinnControlViewWindow(WindowImplementation, AltinnControlView):
    """AltinnControlView implemented as a window."""

    def __init__(
        self, time_units: list[str], control_dict: dict[str, Any], conn: object
    ) -> None:
        """Initializes the AltinnControlViewWindow module."""
        AltinnControlView.__init__(
            self,
            time_units=time_units,
            control_dict=control_dict,
            conn=conn,
        )
        WindowImplementation.__init__(self)
