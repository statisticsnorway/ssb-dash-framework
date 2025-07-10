import logging

import dash_bootstrap_components as dbc
from dash import callback
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

logger = logging.getLogger(__name__)


class AltinnEditorContact:

    def __init__(self):
        self.layout = self._create_layout()
        self.module_callbacks()

    def open_button(self):
        return dbc.Button(
            "Kontakt",
            id="altinn-contact-button",
            className="altinn-editor-module-button",
        )

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

    def _create_layout(self):
        return html.Div(
            [
                self.open_button(),
                self.offcanvas_contact(),
            ]
        )

    def module_callbacks(self):

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfocanvas", "is_open"),
            Input("altinnedit-option2", "n_clicks"),
            State("skjemadata-kontaktinfocanvas", "is_open"),
        )
        def toggle_offcanvas_kontaktinfo(n_clicks, is_open):
            if n_clicks is None:
                return no_update
            if is_open == False:
                return True
            else:
                return False

        @callback(  # type: ignore[misc]
            Output("skjemadata-kontaktinfo-navn", "value"),
            Output("skjemadata-kontaktinfo-epost", "value"),
            Output("skjemadata-kontaktinfo-telefon", "value"),
            Output("skjemadata-kontaktinfo-kommentar1", "value"),
            Output("skjemadata-kontaktinfo-kommentar2", "value"),
            Input("altinnedit-option2", "n_clicks"),
            State("altinnedit-skjemaversjon", "value"),
            State("altinnedit-skjemaer", "value"),
            *self.create_callback_components("State"),
            prevent_initial_call=True,
        )
        def kontaktinfocanvas(n_clicks, skjemaversjon, skjema, *args):
            partition_args = dict(zip(self.time_units, args, strict=False))
            df_skjemainfo = self.conn.query(
                f"""SELECT
                kontaktperson, epost, telefon, kommentar_kontaktinfo, kommentar_krevende
                FROM kontaktinfo
                WHERE skjemaversjon = '{skjemaversjon}'
                """,
                partition_select=self.create_partition_select(
                    skjema=skjema, **partition_args
                ),
            )
            if df_skjemainfo.empty:
                logger.info("Kontaktinfo table for ")
            kontaktperson = df_skjemainfo["kontaktperson"][0]
            epost = df_skjemainfo["epost"][0]
            telefon = df_skjemainfo["telefon"][0]
            kommentar1 = df_skjemainfo["kommentar_kontaktinfo"][0]
            kommentar2 = df_skjemainfo["kommentar_krevende"][0]
            button_text = "kontaktinfo"
            return kontaktperson, epost, telefon, kommentar1, kommentar2
