import logging
from typing import Any
from typing import Literal

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from ..utils.alert_handler import create_alert
from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


default_col_def = {
    "filter": True,
    "resizable": True,
    "sortable": True,
    "floatingFilter": True,
    "editable": False,
}


class AltinnControlView:
    """Provides a layout and functionality for a modal that offers a tabular view of the controls.

    Attributes:
        time_units (list): A list of the time units used.
        control_dict (dict): A dictionary with one control class per skjema.
        conn (object): The eimerdb connection.
    """

    def __init__(
        self, time_units: list[str], control_dict: dict[str, Any], conn: object
    ) -> None:  # TODO add proper annotation for control_dict value
        """Initializes the AltinnControlView with time units, control dictionary, and database connection.

        Args:
            time_units (list): A list of the time units used.
            control_dict (dict): A dictionary with one control class per skjema.
            conn (object): The eimerdb connection.
        """
        logger.warning(
            f"{self.__class__.__name__} is under development and may change in future releases."
        )
        assert hasattr(
            conn, "query"
        ), "The database connection object must have a 'query' method."
        self.time_units = time_units
        self.control_dict = control_dict
        self.conn = conn
        self.callbacks()

    def layout(self) -> html.Div:
        """Generates the layout for the AltinnControlView module.

        Returns:
            layout: A Div element containing two tables, kontroller and kontrollutslag.
        """
        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.ModalTitle("⚠️ Kontroller"),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "🖵",
                                            id="kontroller-modal-fullscreen",
                                        ),
                                        width="auto",
                                        className="ms-auto",
                                    ),
                                ],
                                className="w-100",
                                align="center",
                            )
                        ),
                        dbc.ModalBody(
                            html.Div(
                                style={
                                    "height": "80vh",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "10px",
                                },
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    "🔄 Refresh",
                                                    id="kontrollermodal-refresh",
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Kjør alle kontrollene",
                                                    id="kontrollermodal-kontrollbutton",
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Insert nye kontrollutslag",
                                                    id="kontrollermodal-insertbutton",
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(html.P(id="kontrollermodal-vars")),
                                        ],
                                        className="g-2",
                                    ),
                                    html.Div(
                                        dag.AgGrid(
                                            id="kontroller-table1",
                                            defaultColDef=default_col_def,
                                            className="ag-theme-alpine-dark header-style-on-filter",
                                            style={"height": "35vh", "width": "100%"},
                                            columnSize="responsiveSizeToFit",
                                            dashGridOptions={
                                                "pagination": True,
                                                "rowSelection": "single",
                                                "rowHeight": 28,
                                            },
                                        ),
                                        style={"flexShrink": 0},
                                    ),
                                    html.Div(
                                        dag.AgGrid(
                                            id="kontroller-table2",
                                            defaultColDef=default_col_def,
                                            className="ag-theme-alpine-dark header-style-on-filter",
                                            style={"height": "35vh", "width": "100%"},
                                            columnSize="responsiveSizeToFit",
                                            dashGridOptions={
                                                "pagination": True,
                                                "rowSelection": "single",
                                                "rowHeight": 28,
                                            },
                                        ),
                                        style={"flexShrink": 0},
                                    ),
                                ],
                            )
                        ),
                    ],
                    id="kontroller-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("⚠️", "Kontroller", "sidebar-kontroller-button"),
            ]
        )
        return layout

    def create_partition_select(
        self, skjema: str | None = None, **kwargs: Any
    ) -> dict[str, list[Any]]:  # TODO fix return annotation
        """Creates the partition select argument based on the chosen time units."""
        partition_select = {
            unit: [kwargs[unit]] for unit in self.time_units if unit in kwargs
        }
        if skjema is not None:
            partition_select["skjema"] = [skjema]
        return partition_select

    def create_callback_components(
        self, input_type: Literal["Input", "State"] = "Input"
    ) -> list[str]:
        """Generates a list of dynamic Dash Input or State components."""
        component = Input if input_type == "Input" else State
        return [component(f"var-{unit}", "value") for unit in self.time_units]

    def callbacks(self) -> None:
        """Registers Dash callbacks for the AltinnControlView module."""

        @callback(  # type: ignore[misc]
            Output("kontroller-modal", "fullscreen"),
            Input("kontroller-modal-fullscreen", "n_clicks"),
            State("kontroller-modal", "fullscreen"),
        )
        def toggle_fullscreen_modal(
            n_clicks: int, fullscreen_state: str | bool
        ) -> str | bool:
            fullscreen: str | bool
            if n_clicks > 0:
                if fullscreen_state is True:
                    fullscreen = "xxl-down"
                else:
                    fullscreen = True
                return fullscreen
            raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("kontroller-modal", "is_open"),
            Input("sidebar-kontroller-button", "n_clicks"),
            State("kontroller-modal", "is_open"),
        )
        def kontrollermodal_toggle(n: int, is_open: bool) -> bool:
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            Output("kontroller-table1", "rowData"),
            Output("kontroller-table1", "columnDefs"),
            Input("var-altinnskjema", "value"),
            Input("kontrollermodal-refresh", "n_clicks"),
            *self.create_callback_components("Input"),
        )
        def kontrollutslag_antall(
            skjema: str, n_clicks: int, *args: Any
        ) -> tuple[
            list[dict[str, Any]], list[dict[str, str | bool]]
        ]:  # TODO can *args be more specific?
            partition_args = dict(zip(self.time_units, args, strict=False))
            df1 = self.conn.query(
                """SELECT
                    kontroller.skjema,
                    kontroller.kontrollid,
                    kontroller.type,
                    kontroller.skildring,
                    kontroller.kontrollvar,
                    kontroller.varsort,
                    utslag.ant_utslag
                FROM kontroller AS kontroller
                JOIN (
                    SELECT kontrollid, COUNT(row_id) AS ant_utslag
                    FROM kontrollutslag
                    WHERE utslag = True
                    GROUP BY kontrollid
                    ) AS utslag ON kontroller.kontrollid = utslag.kontrollid
                """,
                self.create_partition_select(skjema=skjema, **partition_args),
            )
            df2 = self.conn.query(
                """SELECT k.kontrollid, COUNT(row_id) AS uediterte FROM kontrollutslag AS k
                JOIN (
                    SELECT ident, skjemaversjon FROM skjemamottak
                    WHERE editert = False
                ) AS subq ON subq.ident = k.ident AND subq.skjemaversjon = k.skjemaversjon
                WHERE utslag = True
                GROUP BY k.kontrollid""",
                self.create_partition_select(skjema=skjema, **partition_args),
            )
            df = df1.merge(df2, on="kontrollid", how="left")
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": col == "varsort",
                    "flex": 2 if col == "skildring" else 1,
                    "tooltipField": col if col == "skildring" else None,
                }
                for col in df.columns
            ]
            columns[0]["checkboxSelection"] = True
            columns[0]["headerCheckboxSelection"] = True
            return df.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output("kontroller-table2", "rowData"),
            Output("kontroller-table2", "columnDefs"),
            Input("kontroller-table1", "selectedRows"),
            *self.create_callback_components("State"),
        )
        def kontrollutslag_mikro(
            current_row: list[dict[str, Any]], *args: Any
        ) -> tuple[
            list[dict[str, Any]], list[dict[str, str | bool]]
        ]:  # TODO can *args be more specific?
            partition_args = dict(zip(self.time_units, args, strict=False))
            kontrollid = current_row[0]["kontrollid"]
            kontrollvar = current_row[0]["kontrollvar"]
            skjema = current_row[0]["skjema"]
            varsort = current_row[0]["varsort"]
            df = self.conn.query(
                f"""
                    SELECT utslag.ident, utslag.skjemaversjon, utslag.kontrollid, utslag.utslag, s.editert, utslag.verdi
                    FROM kontrollutslag AS utslag
                    JOIN (
                        SELECT skjemaversjon AS s_skjemaversjon, editert, ident
                        FROM skjemamottak
                        WHERE aktiv = True
                    ) AS s ON utslag.skjemaversjon = s.s_skjemaversjon AND utslag.ident = s.ident
                    WHERE utslag.kontrollid = '{kontrollid}' AND utslag.utslag = True
                    ORDER BY editert, utslag.verdi {varsort}
                """,
                partition_select={
                    "kontrollutslag": self.create_partition_select(
                        skjema=skjema, **partition_args
                    ),
                    "enhetsinfo": self.create_partition_select(
                        skjema=None, **partition_args
                    ),
                    "skjemamottak": self.create_partition_select(
                        skjema=skjema, **partition_args
                    ),
                },
            ).rename(columns={"verdi": kontrollvar})
            columns = [{"headerName": col, "field": col} for col in df.columns]
            columns[0]["checkboxSelection"] = True
            columns[0]["headerCheckboxSelection"] = True
            return df.to_dict("records"), columns

        @callback(  # type: ignore[misc]
            Output("var-ident", "value", allow_duplicate=True),
            Input("kontroller-table2", "selectedRows"),
            prevent_initial_call=True,
        )
        def kontroll_detail_click(input1: list[dict[str, Any]]) -> str:
            selected = str(
                input1[0]["ident"]
            )  # TODO: check if this is correct, can it be more than one?
            return selected

        @callback(  # type: ignore[misc]
            Output("kontrollermodal-vars", "children"),
            Input("var-altinnskjema", "value"),
            *self.create_callback_components("Input"),
        )
        def altinnskjema(
            skjema: str, *args: Any
        ) -> str:  # TODO can *args be more specific?
            partition_args = dict(zip(self.time_units, args, strict=False))
            if partition_args is not None and skjema is not None:
                valgte_vars = (
                    f"valgt partisjon: {partition_args}\nvalgt skjema: {skjema}"
                )
                return valgte_vars

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("kontrollermodal-kontrollbutton", "n_clicks"),
            State("var-altinnskjema", "value"),
            State("alert_store", "data"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def kontrollkjøring(
            n_clicks: int, skjema: str, alert_store: list[dict[str, Any]], *args: Any
        ) -> list[dict[str, Any]]:  # TODO can *args be more specific?
            partition_args = dict(zip(self.time_units, args, strict=False))
            partitions = self.create_partition_select(skjema=None, **partition_args)
            partitions_skjema = self.create_partition_select(
                skjema=skjema, **partition_args
            )
            if n_clicks > 0:
                try:
                    control_class = self.control_dict[skjema](
                        partitions, partitions_skjema, self.conn
                    )
                    n_updates = control_class.execute_controls()
                    alert_store = [
                        create_alert(
                            f"Kontrollkjøringa er ferdig. {n_updates} rader oppdatert.",
                            "info",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception as e:
                    alert_store = [
                        create_alert(
                            f"Kontrollkjøringa feilet. {str(e)[:60]}",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                return alert_store
            raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("kontrollermodal-insertbutton", "n_clicks"),
            State("var-altinnskjema", "value"),
            State("alert_store", "data"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def kontrollkjøring_insert(
            n_clicks: int, skjema: str, alert_store: list[dict[str, Any]], *args: Any
        ) -> list[dict[str, Any]]:  # TODO can *args be more specific?
            partition_args = dict(zip(self.time_units, args, strict=False))
            partitions = self.create_partition_select(skjema=None, **partition_args)
            partitions_skjema = self.create_partition_select(
                skjema=skjema, **partition_args
            )
            if n_clicks > 0:
                try:
                    control_class = self.control_dict[skjema](
                        partitions, partitions_skjema, self.conn
                    )
                    n_inserts = control_class.insert_new_rows()
                    alert_store = [
                        create_alert(
                            f"Kontrollkjøringa er ferdig. {n_inserts} nye rader er lastet inn.",
                            "info",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                except Exception as e:
                    alert_store = [
                        create_alert(
                            f"Kontrollkjøringa feilet. {str(e)[:60]}",
                            "danger",
                            ephemeral=True,
                        ),
                        *alert_store,
                    ]
                return alert_store
            raise PreventUpdate
