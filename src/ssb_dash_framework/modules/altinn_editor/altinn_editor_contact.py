import logging
from typing import Any

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


class AltinnEditorContact:
    """Module for displaying contact information in the Altinn Editor."""

    def __init__(
        self,
        time_units: list[str],
        conn: object,
        variable_selector_instance: VariableSelector,
    ) -> None:
        """Initializes the Altinn Editor Contact module.

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
        self.variable_selector = variable_selector_instance
        self.time_units = time_units
        self.module_layout = self._create_layout()
        self.module_callbacks()

    def offcanvas_contact(self) -> html.Div:
        """Retuns an offcanvas component containing a table with contact information."""
        return html.Div(
            [
                dbc.Offcanvas(
                    html.Div(
                        style={
                            "display": "grid",
                            "grid-template-rows": "10% 10% 10% 35% 35%",
                            "height": "100%",
                        },
                        children=[
                            html.Div(
                                [
                                    html.Label("Navn:"),
                                    dbc.Input(
                                        type="text",
                                        id="skjemadata-kontaktinfo-navn",
                                        placeholder="Navn Navnesen",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("E-post:"),
                                    dbc.Input(
                                        type="email",
                                        id="skjemadata-kontaktinfo-epost",
                                        placeholder="navn@mail.com",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("Telefonnummer:"),
                                    dbc.Input(
                                        type="text",
                                        id="skjemadata-kontaktinfo-telefon",
                                        placeholder="12345678",
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("Kontaktinfokommentar:"),
                                    dbc.Textarea(
                                        placeholder="Ingen kommentar",
                                        id="skjemadata-kontaktinfo-kommentar1",
                                        style={"height": "80%"},
                                        disabled=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label("kommentar_krevende:"),
                                    dbc.Textarea(
                                        placeholder="Ingen kommentar",
                                        id="skjemadata-kontaktinfo-kommentar2",
                                        style={"height": "80%"},
                                        disabled=True,
                                    ),
                                ]
                            ),
                        ],
                    ),
                    id="skjemadata-kontaktinfocanvas",
                    title="Kontaktinfo og kommentarer",
                    is_open=False,
                    placement="end",
                    backdrop=False,
                    style={"width": "25%", "height": "100%"},
                ),
            ]
        )

    def _create_layout(self) -> html.Div:
        """Creates the layout for the Altinn Editor Contact module."""
        return html.Div(
            [
                dbc.Form(
                    [
                        dbc.Label("Kontaktinfo", className="mb-1"),
                        dbc.Button(
                            "Se kontaktinfo",
                            id="altinnedit-contact-button",
                            className="w-100",
                        ),
                    ]
                ),
                self.offcanvas_contact(),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout for the Altinn Editor Contact module."""
        return self.module_layout

    def module_callbacks(self) -> None:
        """Defines the callbacks for the Altinn Editor Contact module."""

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfocanvas", "is_open"),
            Input("altinnedit-contact-button", "n_clicks"),
            State("skjemadata-kontaktinfocanvas", "is_open"),
        )
        def toggle_offcanvas_kontaktinfo(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfo-navn", "value"),
            Output("skjemadata-kontaktinfo-epost", "value"),
            Output("skjemadata-kontaktinfo-telefon", "value"),
            Output("skjemadata-kontaktinfo-kommentar1", "value"),
            Output("skjemadata-kontaktinfo-kommentar2", "value"),
            Input("altinnedit-contact-button", "n_clicks"),
            State("altinnedit-skjemaversjon", "value"),
            State("altinnedit-skjemaer", "value"),
            self.variable_selector.get_states(),
            prevent_initial_call=True,
        )
        def kontaktinfocanvas(
            n_clicks: None | int, skjemaversjon: str, skjema: str, *args: Any
        ) -> tuple[str, str, str, str, str]:
            logger.debug(
                f"Args:\n"
                f"n_clicks: {n_clicks}\n"
                f"skjemaversjon: {skjemaversjon}\n"
                f"skjema: {skjema}\n"
                f"args: {args}"
            )
            partition_args = dict(zip(self.time_units, args, strict=False))
            df_skjemainfo = self.conn.query(
                f"""SELECT
                kontaktperson, epost, telefon, kommentar_kontaktinfo, kommentar_krevende
                FROM kontaktinfo
                WHERE skjemaversjon = '{skjemaversjon}'
                """,
                partition_select=create_partition_select(
                    desired_partitions=self.time_units, skjema=skjema, **partition_args
                ),
            )
            if df_skjemainfo.empty:
                logger.info("Kontaktinfo table for ")
            kontaktperson = df_skjemainfo["kontaktperson"][0]
            epost = df_skjemainfo["epost"][0]
            telefon = df_skjemainfo["telefon"][0]
            kommentar1 = df_skjemainfo["kommentar_kontaktinfo"][0]
            kommentar2 = df_skjemainfo["kommentar_krevende"][0]
            return kontaktperson, epost, telefon, kommentar1, kommentar2
