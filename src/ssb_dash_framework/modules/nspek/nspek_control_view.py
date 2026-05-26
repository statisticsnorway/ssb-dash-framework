import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc

# import ibis
from dash import callback
from dash import callback_context as ctx
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

# from eimerdb import EimerDBInstance
from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)

default_col_def = {
    # "filter": True,
    "resizable": True,
    "sortable": True,
    # "floatingFilter": True,
    "editable": False,
}


class NspekControlView(ABC):
    """Nspek variant av ControlView - tett på original implementasjon,
    men med control_dict og uten hard dependency på altinnskjema.
    """

    _id_number: int = 0

    def __init__(
        self,
        time_units: list[str],
        control_dict: dict[str, Any],
        outputs: list[str] | None = None,
    ) -> None:

        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )

        if outputs is None:
            outputs = ["ident", "foretak", "aar"]
        self.module_number = NspekControlView._id_number
        self.module_name = self.__class__.__name__
        NspekControlView._id_number += 1

        self.icon = "⚖️"
        self.label = "Kontroll"

        self.control_dict = control_dict
        self.outputs = outputs
        # self._is_valid()
        self.module_layout = self.create_layout()
        self.variableselector = VariableSelector(
            selected_inputs=time_units,
            selected_states=[],
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        self.module_callbacks()
        module_validator(self)

    def create_layout(self) -> html.Div:
        """Generates the layout for the ControlView module.

        Returns:
            layout: A Div element containing two tables, kontroller and kontrollutslag.
        """
        return html.Div(
            style={"width": "100%"},
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Oppdater visning",
                                id=f"{self.module_number}-kontroll-refresh",
                                className="ssb-btn primary-btn",
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
                            style={"display": "none"},
                        ),
                        dbc.Col(html.P(id=f"{self.module_number}-kontroll-var")),
                    ],
                    className="g-2 mb-2",
                ),
                dbc.Row(
                    dbc.Col(
                        dag.AgGrid(
                            id=f"{self.module_number}-kontroller",
                            defaultColDef=default_col_def,
                            className="ag-theme-alpine ag-theme-ssb mb-2 header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={
                                # "pagination": True,
                                "rowSelection": "single",
                                "rowHeight": 30,
                            },
                            style={"height": "500px"},
                        ),
                        style={"flexShrink": 0},
                        width=12,
                    ),
                ),
                html.Hr(),
                dbc.Row(
                    dbc.Col(
                        dag.AgGrid(
                            id=f"{self.module_number}-kontrollutslag",
                            defaultColDef=default_col_def,
                            className="ag-theme-alpine ag-theme-ssb mb-2 header-style-on-filter",
                            columnSize="responsiveSizeToFit",
                            dashGridOptions={
                                "pagination": True,
                                "rowSelection": "single",
                                "rowHeight": 30,
                            },
                            style={"height": "500px"},
                        ),
                        width=12,
                    )
                ),
            ],
        )

    @abstractmethod
    def layout(self) -> html.Div:
        """Defines the layout for the NspekControlView module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    def module_callbacks(self) -> None:

        @callback(
            Output(f"{self.module_number}-kontroll-var", "children"),
            *self.variableselector.get_all_inputs(),
        )
        def show_vars(*args):
            return f"valgte variabler: {dict(zip(self.time_units, args, strict=False))}"

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def alert_user_of_controls(
            click: int | None, alert_store: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            return [
                create_alert(
                    "Kjører kontroller, dette kan ta litt tid, du får beskjed når den er ferdig. Ikke klikk på knappen igjen.",
                    "info",
                    ephemeral=True,
                ),
                *alert_store,
            ]

        @callback(
            Output(f"{self.module_number}-kontroller", "rowData"),
            Output(f"{self.module_number}-kontroller", "columnDefs"),
            Output("alert_store", "data", allow_duplicate=True),
            Input(f"{self.module_number}-kontroll-refresh", "n_clicks"),
            Input(f"{self.module_number}-kontroll-run-button", "n_clicks"),
            State("alert_store", "data"),
            *self.variableselector.get_all_inputs(),
            prevent_initial_call=True,
        )
        def get_kontroller_overview(refresh, run, store, *args):

            control_class = self.control_dict

            subset = dict(zip(self.time_units, args, strict=False))
            subset["aar"] = int(subset["aar"])

            instance = control_class(
                time_units=self.time_units,
                applies_to_subset=subset,
            )

            if ctx.triggered_id == f"{self.module_number}-kontroll-run-button":
                if hasattr(instance, "run_all_controls"):
                    instance.run_all_controls()

            df = instance.get_current_kontroller()

            if df is None or df.empty:
                return [], [], store

            columns = [{"headerName": c, "field": c} for c in df.columns]

            if len(columns) > 0:
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True

            return (
                df.to_dict("records"),
                columns,
                [create_alert("Oppdatert", "info", ephemeral=True), *store],
            )

        @callback(
            Output(f"{self.module_number}-kontrollutslag", "rowData"),
            Output(f"{self.module_number}-kontrollutslag", "columnDefs"),
            Input(f"{self.module_number}-kontroller", "selectedRows"),
            prevent_initial_call=True,
        )
        def get_kontrollutslag(selected):

            if not selected:
                raise PreventUpdate

            control_class = self.control_dict

            instance = control_class(
                time_units=self.time_units,
                applies_to_subset={},
            )

            df = instance.get_current_kontrollutslag(
                specific_control=selected[0]["kontrollid"]
            )

            if df is None or df.empty:
                return [], []
            
            df["foretak"] = df["ident"]

            columns = [{"headerName": c, "field": c} for c in df.columns]

            if len(columns) > 0:
                columns[0]["checkboxSelection"] = True
                columns[0]["headerCheckboxSelection"] = True
            
            for col in columns:
                if col["field"] == "foretak":
                    col["hide"] = True

            return df.to_dict("records"), columns

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
            if selected_row is None or not selected_row:
                logger.debug("Raising PreventUpdate due to selected_row being None")
                raise PreventUpdate
            if len(selected_row) > 1:
                raise ValueError(
                    "Too many rows selected, logic won't work with more than one row."
                )
            if len(self.outputs) == 1:
                return str(selected_row[0][self.outputs[0]])

            elif len(self.outputs) > 1:
                return tuple(str(selected_row[0][output]) for output in self.outputs)
            else:
                raise ValueError(
                    f"Something is wrong with 'self.outputs'. Should be a list with at least one string inside of it. Is currently: {self.outputs}"
                )


class NspekControlViewTab(TabImplementation, NspekControlView):
    def __init__(self, time_units: list[str], control_dict: dict[str, Any]):
        NspekControlView.__init__(
            self,
            time_units=time_units,
            control_dict=control_dict,
        )
        TabImplementation.__init__(self)


class NspekControlViewWindow(WindowImplementation, NspekControlView):
    def __init__(self, time_units: list[str], control_dict: dict[str, Any], **kwargs: Any):

        NspekControlView.__init__(
            self,
            time_units=time_units,
            control_dict=control_dict,
        )
        WindowImplementation.__init__(self, **kwargs)
