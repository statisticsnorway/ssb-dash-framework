import logging
import os
import re
import time
from pathlib import Path
from typing import Any
from typing import ClassVar
import plotly.express as px
import random
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import ibis
import pandas as pd
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from dash_ag_grid import AgGrid
from dash_iconify import DashIconify
from ibis import _
from pandas.core.frame import DataFrame

from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator
#from .nspek_utils import get_nspek_connection
#from .nspek_utils import set_nspek_connection

ibis.options.interactive = True
logger = logging.getLogger(__name__)

TYPE_REGNSKAP_TABLE = {
    "registrering": {
        "database": "nspek_core",
        "table": "registrering",
    },
    "v_registrering_versjon": {
        "database": "nspek_core",
        "table": "v_registrering_versjon",
    },
    "virksomhet": {
        "database": "virksomhet",
        "table": "tema_virksomhet",
    },
    "balanseregnskap": {
        "database": "balanseregnskap",
        "table": "tema_balanse",
    },
    "resultatregnskap": {
        "database": "resultatregnskap",
        "table": "tema_resultat",
    },
    "enhet_opplysninger": {
        "database": "nspek_core",
        "table": "enhet_opplysninger",
    },
}


KPI_CONFIG = {
    "bruker": {
        "title": "Konstruert",
        "card_id": "nspek-dashboard-bruker-card",
        "modal_id": "nspek-dashboard-bruker-modal",
        "grid_id": "nspek-dashboard-bruker-grid",
        "description": (
            "Viser registreringene som er konstruert av SSB, "
            "inkludert organisasjonsnummer, bruker og tidspunkt."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": "agTextColumnFilter",
            },
            {
                "field": "bruker",
                "headerName": "Bruker",
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
            },
        ],
    },
    "ske": {
        "title": "Mottatt fra SKE",
        "card_id": "nspek-dashboard-ske-card",
        "modal_id": "nspek-dashboard-ske-modal",
        "grid_id": "nspek-dashboard-ske-grid",
        "description": (
            "Viser registreringene som er mottatt fra Skatteetaten (SKE), "
            "inkludert organisasjonsnummer og tidspunkt for mottak."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": "agTextColumnFilter",
            },
            {
                "field": "bruker",
                "headerName": "Bruker",
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
            },
        ],
    },
    "total": {
        "title": "Totalt i populasjonen",
        "card_id": "nspek-dashboard-total-card",
        "modal_id": "nspek-dashboard-total-modal",
        "grid_id": "nspek-dashboard-total-grid",
        "description": (
            "Viser alle registreringene i populasjonen, "
            "uavhengig av hvordan registreringen er opprettet."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": "agTextColumnFilter",
            },
            {
                "field": "bruker",
                "headerName": "Bruker",
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
            },
        ],
    },
    "skjoenn": {
        "title": "Skjønnslignet",
        "card_id": "nspek-dashboard-skjoenn-card",
        "modal_id": "nspek-dashboard-skjoenn-modal",
        "grid_id": "nspek-dashboard-skjoenn-grid",
        "description": (
            "Viser registreringene som er skjønnslignet av SKE."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": "agTextColumnFilter",
            },
            {
                "field": "bruker",
                "headerName": "Bruker",
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
            },
        ],
    },
}


def get_versions(conn, ident: str, aar: str) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing all sekvensnummer sorted by versjon_nr from nspek_core view v_registrering_versjon.

    Example use: get_versions(conn, "979443137", "2024")
    """
    config = TYPE_REGNSKAP_TABLE["v_registrering_versjon"]

    t = conn.table(config["table"], database=config["database"])

    df = (
        t.filter((_.orgnr == ident) & (_.aar == int(aar)))
        .order_by(_.versjon_nr)
        .select(_.sekvensnummer, _.versjon_nr, _.antall_versjoner, _.dato_mottatt)
        .execute()
    )

    df["label"] = (
        "v"
        + df["versjon_nr"].astype(str)
        + " – "
        + pd.to_datetime(df["dato_mottatt"]).dt.strftime("%Y-%m-%d %H:%M")
    )

    return df


def get_virksomhetsinfo(
    conn, variables_to_fetch: list, ident: str, aar: str, sekvensnummer: int
) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing virksomhetsinfo from nspek files for specified variables for a unit.

    Example use: get_virksomhetsinfo(conn, virksomhetsinfo_variabler, "979443137", "2024", 2291859)
    """
    config = TYPE_REGNSKAP_TABLE["virksomhet"]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.filter(t["felt"].isin(variables_to_fetch)).select(
        ["felt", "char_verdi"]
    )
    df = filtered.execute()

    return df


def get_skjoennslignet(conn, sekvensnummer: int) -> pd.DataFrame:
    """Fetch and return pandas dataframe containing virksomhetsinfo from nspek files for specified variables for a unit.

    Example use: get_skjoennslignet(self.conn, 2291859)
    """
    config = TYPE_REGNSKAP_TABLE["enhet_opplysninger"]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.filter(_.opplysning == "skjoennslignet").select(["opplysning"])
    df = filtered.execute()

    return df


def get_bof_database_path() -> Path:
    """Find the available BOF database."""
    database_paths = [
        Path("/buckets/shared/vof/oracle-hns/ssb_foretak.db"),
        Path("/buckets/delt-oracle-hns/ssb_foretak.db"),
    ]

    for database_path in database_paths:
        if database_path.exists():
            return database_path

    raise FileNotFoundError(
        "Fant ikke ssb_foretak.db. Sjekket følgende filbaner: "
        f"{', '.join(str(path) for path in database_paths)}"
    )


def orgnr_exists_in_bof(orgnr: str) -> bool:
    """Checks if organisation exists in BOF registry.

    Example use: orgnr_exists_in_bof("979443137")
    """
    try:
        db_path = get_bof_database_path()

        conn = ibis.sqlite.connect(str(db_path))
        t = conn.table("ssb_foretak")

        df = t.filter(_.orgnr == orgnr).limit(1).execute()

        return not df.empty

    except Exception as e:
        logger.error(f"BOF lookup feilet: {e}")
        return True


def get_value(series) -> str:
    """Return first value or empty string if no match."""
    return "" if series.empty else str(series.iloc[0])


def fetch_data_by_orgnr(
    conn, regnskapstype: str, ident: str, aar: str, sekvensnummer: int
) -> pd.DataFrame:
    """Returns a pandas dataframe with all nspek values found in the specified regnskapstype for a unit/orgnr.

    Example use: fetch_data_by_orgnr(conn, "resultatregnskap", "932598957", "2024", 2291859)
    """
    config = TYPE_REGNSKAP_TABLE[regnskapstype]

    t = conn.table(config["table"], database=config["database"])
    t = t.filter(_.sekvensnummer == sekvensnummer)
    filtered = t.select(["felt", "belop"])
    df = filtered.to_pandas()

    return df


def get_demo_population_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dato": pd.date_range(
                "2026-01-01",
                periods=8,
                freq="W",
            ),
            "bruker": [
                11,
                19,
                24,
                31,
                42,
                55,
                61,
                67,
            ],
            "skjoenn": [
                5,
                9,
                12,
                15,
                21,
                27,
                30,
                34,
            ],
            "ske": [
                80,
                150,
                260,
                340,
                420,
                510,
                560,
                610,
            ],
        }
    )


def construct_sequence(
    orgnr: str,
) -> dict[str, str]:
    """Mock konstruksjon av sekvens for et organisasjonsnummer."""

    orgnr = str(orgnr).strip()

    # ------------------------------------------------------------
    # Mock: Sjekk om det allerede finnes en sekvens
    # ------------------------------------------------------------

    mock_existing_sequences = {
        "979443137": 2291859,
        "932598957": 2291860,
    }

    if orgnr in mock_existing_sequences:
        sekvensnummer = mock_existing_sequences[orgnr]

        return {
            "status": "info",
            "orgnr": orgnr,
            "message": (
                f"Det finnes allerede en sekvens "
                f"({sekvensnummer})."
            ),
        }

    # ------------------------------------------------------------
    # Mock: Opprett nytt sekvensnummer
    # ------------------------------------------------------------

    mock_new_sequence = 3000000 + int(orgnr[-4:])

    return {
        "status": "success",
        "orgnr": orgnr,
        "message": (
            f"Ny sekvens {mock_new_sequence} "
            "ble konstruert."
        ),
    }


def get_kpi_metadata(
    kpi_type: str,
) -> list[dict]:
    """Return randomly generated mock metadata for a KPI."""

    counts = {
        "bruker": 67,
        "ske": 610,
        "skjoenn": 34,
    }

    brukere = [
        "sik",
        "mif",
        "hmt",
        "jca",
        "ret",
        "aeh",
        "klh",
        "jem",
        "tve",
        "gnh",
        "rga",
        "cgy",
    ]

    def generate_orgnr() -> str:
        """Generate a random 9-digit organisation number."""
        return str(random.randint(100_000_000, 999_999_999))

    def generate_timestamp() -> str:
        """Generate a random timestamp within the last 30 days."""
        end = datetime.now()
        start = end - timedelta(days=30)

        seconds = random.randint(
            0,
            int((end - start).total_seconds()),
        )

        timestamp = start + timedelta(seconds=seconds)

        return timestamp.strftime("%Y-%m-%d %H:%M")

    def generate_rows(
        count: int,
        bruker: str | None = None,
    ) -> list[dict]:
        """Generate random KPI metadata rows."""

        return [
            {
                "orgnr": generate_orgnr(),
                "bruker": bruker or random.choice(brukere),
                "tidspunkt": generate_timestamp(),
            }
            for _ in range(count)
        ]

    if kpi_type == "bruker":
        return generate_rows(67)

    if kpi_type == "ske":
        return generate_rows(610, bruker="SKE")

    if kpi_type == "skjoenn":
        return generate_rows(34)

    if kpi_type == "total":
        return (
            generate_rows(67)
            + generate_rows(610, bruker="SKE")
            + generate_rows(34)
        )

    return []


class NspekDashboard:
    """The Naeringsspesifikasjon module lets you view the nspek/naeringsspesifikasjon for a specified foretak (var-ident)."""

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = (
        [  # Used for validating that the variable selector has the required variables set. These are hard-coded in the module_callbacks.
            "foretak",
        ]
    )

    def __init__(self, time_units: list[str], db_user: str | None) -> None:
        """Explanation of module."""
        #set_nspek_connection(
        #    db_user if db_user else "strukt-naering-developers@dapla-group-sa-p-ye.iam"
        #)
        self.module_number = NspekDashboard._id_number
        self.module_name = self.__class__.__name__
        self.icon = DashIconify(icon="feather:activity", width=24)
        self.label = "NSPEK Status"

        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        self.time_units = [
            self.variableselector.get_option(x).id.removeprefix("var-")
            for x in time_units
        ]
        logger.debug("TIME UNITS %s", self.time_units)

        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _is_valid(self) -> None:
        for var in NspekDashboard._required_variables:
            try:
                self.variableselector.get_option(f"var-{var}", search_target="id")
            except ValueError as e:
                raise ValueError(
                    f"Naeringsspesifikasjon requires the variable selector option '{var}' to be set."
                ) from e

    def create_info_card(self, title: str, component_id: str, var_type: str):
        card_info = html.Div(
            className="ssb-input",
            children=[
                html.Label(title),
                html.Div(
                    className="input-wrapper",
                    children=[
                        dbc.Input(
                            id=component_id,
                            type=var_type,
                        )
                    ],
                ),
            ],
        )
        return card_info

    def create_dropdown_card(self, title: str, component_id: str):
        dropdown_card = html.Div(
            children=[
                html.Span(title, className="dropdown-label"),
                dcc.Dropdown(
                    id=component_id,
                    className="ssb-dropdown",
                    placeholder="-- Velg --",
                    clearable=True,
                    searchable=False,
                ),
            ],
            className="ssb-dropdown-card",
        )
        return dropdown_card

    def create_checkbox(
        self, component_id: str, label: str, value: str, checked: bool = False
    ):
        checkbox = html.Div(
            className="ssb-checkbox d-flex align-items-center",
            children=[
                dcc.Checklist(
                    id=component_id,
                    options=[{"label": "", "value": value}],
                    value=[value] if checked else [],
                ),
                html.Label(
                    label,
                    className="mb-1 ms-2",
                ),
            ],
        )
        return checkbox

    def create_dialog(self, variant: str, title: str, message: str):
        dialog = html.Div(
            className=f"ssb-dialog {variant} mt-2 mb-1",
            children=[
                html.Div(
                    DashIconify(icon=self._map_icon(variant), width=40),
                    className="icon-panel",
                ),
                html.Div(
                    [
                        html.Div(title, className="dialog-title"),
                        html.Div(message, className="content"),
                    ],
                    className="dialog-content",
                ),
                html.Button(
                    "✕",
                    id="close-version-warning",
                    n_clicks=0,
                    className="dialog-close",
                ),
            ],
        )
        return dialog

    def create_mini_dialog(
        self,
        variant: str,
        title: str,
        orgnr: str,
        message: str,
    ):
        return html.Div(
            className=f"ssb-dialog ssb-dialog-mini {variant}",
            children=[
                html.Div(
                    DashIconify(
                        icon=self._map_icon(variant),
                        width=20,
                    ),
                    className="icon-panel",
                ),
                html.Div(
                    [
                        html.Span(
                            title,
                            className="dialog-title",
                        ),
                        html.Span(
                            orgnr,
                            className="dialog-orgnr",
                        ),
                        html.Span(
                            message,
                            className="dialog-content",
                        ),
                    ],
                    className="dialog-content",
                ),
            ],
        )

    def _map_icon(self, variant):
        variant: str = {
            "warning": "feather:alert-triangle",
            "info": "feather:info",
            "success": "feather:check-circle",
        }.get(variant, "feather:info")
        return variant

    def create_kpi_card(
        self,
        title: str,
        component_id: str,
        icon: str,
        description: str | None = None,
        card_id: str | None = None,
    ) -> html.Div:
        """Create a dashboard KPI card using the SSB card component."""

        content = [
            html.Div(
                DashIconify(
                    icon=icon,
                    width=28,
                ),
                className="card-icon",
            ),
            html.Div(
                title,
                className="card-title",
            ),
            html.Div(
                id=component_id,
                className="nspek-dashboard-kpi-value",
            ),
        ]

        if description:
            content.append(
                html.Span(
                    description,
                    className=(
                        "ssb-text-wrapper "
                        "nspek-dashboard-kpi-description"
                    ),
                )
            )

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            content,
                            className="card-content",
                        )
                    ],
                    className="clickable top-orientation",
                )
            ],
            id=card_id,
            n_clicks=0 if card_id else None,
            className="ssb-card nspek-dashboard-kpi-card",
        )


    def create_kpi_modal(
        self,
        modal_id: str,
        title: str,
        grid_id: str,
        column_defs: list[dict],
        description: str,
    ) -> dbc.Modal:
        """Create a modal containing KPI information and an AG Grid."""

        refresh_button_id = f"{grid_id}-refresh"
        count_id = f"{grid_id}-count"
        close_button_id = f"{modal_id}-close"

        return dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(title),
                ),

                dbc.ModalBody(
                    [
                        dbc.Row(
                            [
                                # Key figure
                                dbc.Col(
                                    self.create_key_figure(
                                        title="Antall registreringer",
                                        component_id=count_id,
                                        size="large",
                                        icon="/proxy/8000/assets/test2.svg",
                                        subtitle="foretak",
                                        time_text="2026",
                                    ),
                                    md=6,
                                ),

                                # Description + refresh button
                                dbc.Col(
                                    [
                                        html.P(
                                            description,
                                            className="mb-0",
                                        ),
                                        html.Div(
                                            dbc.Button(
                                                "Oppdater data",
                                                id=refresh_button_id,
                                                className="ssb-btn primary-btn",
                                            ),
                                            className="d-flex justify-content-end mt-auto",
                                        ),
                                    ],
                                    md=6,
                                    className="d-flex flex-column",
                                ),
                            ],
                            className="mb-4 align-items-stretch",
                        ),

                        AgGrid(
                            id=grid_id,
                            columnDefs=column_defs,
                            rowData=[],
                            defaultColDef={
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                            },
                            columnSize="sizeToFit",
                            dashGridOptions={
                                "animateRows": False,
                            },
                            className="ag-theme-alpine ag-theme-ssb",
                            style={
                                "height": "700px",
                                "width": "100%",
                            },
                        ),
                    ],
                ),

                dbc.ModalFooter(
                    dbc.Button(
                        "Lukk",
                        id=close_button_id,
                        className="mb-3 ssb-btn primary-btn",
                    ),
                ),
            ],
            id=modal_id,
            className="ssb-modal",
            size="xl",
            is_open=False,
            scrollable=True,
        )


    def create_key_figure(
        self,
        title: str,
        component_id: str,
        size: str = "medium",
        icon: str | None = None,
        subtitle: str | None = None,
        time_text: str | None = None,
        green_box: bool = False,
    ) -> html.Div:
        """Create an SSB key figure component."""

        classes = f"ssb-key-figures {size}"

        if green_box:
            classes += " green-box"

        content = [
            html.Span(
                title,
                className="kf-title",
            ),
        ]

        if time_text:
            content.append(
                html.Div(
                    time_text,
                    className="kf-time",
                )
            )

        number_section = [
            html.Div(
                id=component_id,
                className=f"ssb-number {size}",
            )
        ]

        if subtitle:
            number_section.append(
                html.Span(
                    subtitle,
                    className="kf-title subtitle",
                )
            )

        content.append(
            html.Div(
                number_section,
                className="number-section",
            )
        )

        children = []

        if icon:
            if icon.startswith("feather:"):
                icon_component = DashIconify(
                    icon=icon,
                    width={
                        "small": 48,
                        "medium": 72,
                        "large": 100,
                    }[size],
                )
            else:
                icon_component = html.Img(
                    src=icon,
                    alt="",
                    **{"aria-hidden": "true"},
                )

            children.append(
                html.Div(
                    icon_component,
                    className=f"kf-icon {size}",
                )
            )

        children.append(
            html.Div(content)
        )

        return html.Div(
            children,
            className=classes,
        )

    def create_development_figure(self, df: pd.DataFrame):
        long_df = df.melt(
            id_vars="dato",
            value_vars=["bruker", "ske", "skjoenn"],
            var_name="kilde",
            value_name="antall",
        )

        labels = {
            "bruker": "Konstruert av bruker",
            "ske": "Mottatt fra SKE",
            "skjoenn": "Skjønnslignet",
        }

        long_df["kilde"] = long_df["kilde"].map(labels)

        fig = px.line(
            long_df,
            x="dato",
            y="antall",
            color="kilde",
            markers=True,
            color_discrete_map={
                "Konstruert av bruker": "#075745",
                "Mottatt fra SKE": "#1A9D49",
                "Skjønnslignet": "#1D9DE2",
            },
        )

        fig.update_traces(
            marker=dict(size=8),
        )

        fig.update_traces(
            selector={"name": "Konstruert av bruker"},
            marker_symbol="circle",
        )

        fig.update_traces(
            selector={"name": "Mottatt fra SKE"},
            marker_symbol="triangle-up",
        )

        fig.update_traces(
            selector={"name": "Skjønnslignet"},
            marker_symbol="square",
        )

        fig.update_layout(
            margin={"l": 10, "r": 10, "t": 30, "b": 75},
            hovermode="closest",
            spikedistance=-1,
            legend={
                "orientation": "h",
                "y": -0.20,
                "yanchor": "top",
                "x": 0,
                "xanchor": "left",
                "title": None,
            },
            font={
                "family": "Open Sans, Arial, sans-serif",
                "size": 12,
                "color": "#21383A",
            },
            xaxis={
                "title": None,
                "showgrid": False,
                "showline": True,
                "linecolor": "#21383A",
                "linewidth": 1,
                "showspikes": True,
                "spikemode": "across",
                "spikesnap": "data",
                "spikecolor": "#9272FC",
                "spikethickness": 1,
                "spikedash": "solid",
            },
            yaxis={
                "title": None,
                "showgrid": True,
                "gridcolor": "#E6E6E6",
                "gridwidth": 1,
                "showline": True,
                "linecolor": "#21383A",
                "linewidth": 1,
            },
            annotations=[
                {
                    "text": "Antall",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 1,
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "xshift": -35,
                    "showarrow": False,
                    "font": {
                        "family": "Open Sans, Arial, sans-serif",
                        "size": 12,
                        "color": "#21383A",
                    },
                },
                {
                    "text": "Dato",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 1,
                    "y": 0,
                    "xanchor": "right",
                    "yanchor": "top",
                    "yshift": -20,
                    "showarrow": False,
                    "font": {
                        "family": "Open Sans, Arial, sans-serif",
                        "size": 12,
                        "color": "#21383A",
                    },
                },
            ],
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        return fig


    def create_distribution_figure(self, df: pd.DataFrame):
        long_df = df.melt(
            id_vars="dato",
            value_vars=["bruker", "ske", "skjoenn"],
            var_name="kilde",
            value_name="antall",
        )

        labels = {
            "bruker": "Konstruert av bruker",
            "ske": "Mottatt fra SKE",
            "skjoenn": "Skjønnslignet",
        }

        long_df["kilde"] = long_df["kilde"].map(labels)

        fig = px.bar(
            long_df,
            x="dato",
            y="antall",
            color="kilde",
            barmode="group",
            color_discrete_map={
                "Konstruert av bruker": "#075745",
                "Mottatt fra SKE": "#1A9D49",
                "Skjønnslignet": "#1D9DE2",
            },
        )

        fig.update_layout(
            margin={"l": 10, "r": 10, "t": 30, "b": 75},
            legend={
                "orientation": "h",
                "y": -0.20,
                "yanchor": "top",
                "x": 0,
                "xanchor": "left",
                "title": None,
            },
            font={
                "family": "Open Sans, Arial, sans-serif",
                "size": 12,
                "color": "#21383A",
            },
            xaxis={
                "title": None,
                "showgrid": False,
                "showline": True,
                "linecolor": "#21383A",
                "linewidth": 1,
            },
            yaxis={
                "title": None,
                "showgrid": True,
                "gridcolor": "#E6E6E6",
                "gridwidth": 1,
                "showline": True,
                "linecolor": "#21383A",
                "linewidth": 1,
            },
            annotations=[
                {
                    "text": "Antall",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 1,
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "xshift": -35,
                    "showarrow": False,
                    "font": {
                        "family": "Open Sans, Arial, sans-serif",
                        "size": 12,
                        "color": "#21383A",
                    },
                },
                {
                    "text": "Dato",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 1,
                    "y": 0,
                    "xanchor": "right",
                    "yanchor": "top",
                    "yshift": -20,
                    "showarrow": False,
                    "font": {
                        "family": "Open Sans, Arial, sans-serif",
                        "size": 12,
                        "color": "#21383A",
                    },
                },
            ],
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        return fig


    def create_development_table(self, df: pd.DataFrame) -> html.Div:
        table_df = df.copy()

        table_df["dato"] = pd.to_datetime(table_df["dato"]).dt.strftime(
            "%d.%m.%Y"
        )

        table_df = table_df.rename(
            columns={
                "dato": "Dato",
                "bruker": "Konstruert av bruker",
                "ske": "Mottatt fra SKE",
                "skjoenn": "Skjønnslignet",
            }
        )

        table = dbc.Table.from_dataframe(
            table_df,
            striped=False,
            bordered=False,
            hover=False,
            responsive=False,
            class_name="ssb-table",
        )

        return html.Div(
            table,
            className="ssb-table-wrapper",
        )

    def create_distribution_table(self, df: pd.DataFrame) -> html.Div:
        table_df = df.copy()

        table_df["dato"] = pd.to_datetime(table_df["dato"]).dt.strftime(
            "%d.%m.%Y"
        )

        table_df = table_df.rename(
            columns={
                "dato": "Dato",
                "bruker": "Konstruert av bruker",
                "ske": "Mottatt fra SKE",
                "skjoenn": "Skjønnslignet",
            }
        )

        table = dbc.Table.from_dataframe(
            table_df,
            striped=False,
            bordered=False,
            hover=False,
            responsive=False,
            class_name="ssb-table",
        )

        return html.Div(
            table,
            className="ssb-table-wrapper",
        )


    def _create_layout(self):
        return html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle("Konstruer sekvens")
                        ),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    className="ssb-text-area",
                                    children=[
                                        dbc.Textarea(
                                            id="nspek-dashboard-construct-orgnr",
                                            placeholder=(
                                                "Skriv inn ett eller flere organisasjonsnummer, "
                                                "ett per linje.\n\n"
                                                "Eksempel:\n"
                                                "979443137\n"
                                                "932598957\n"
                                                "987654321\n"
                                                "999888777"
                                            ),
                                            className="comment-textarea",
                                            style={
                                                "width": "100%",
                                                "height": "600px",
                                                "padding": "10px 12px",
                                            },
                                        ),
                                    ],
                                ),
                                html.Small(
                                    "Du kan også lime inn en liste med organisasjonsnummer. Duplikater vil bli fjernet i behandlingen.",
                                    className="text-muted",
                                ),
                                html.Div(
                                    id="nspek-dashboard-construct-result",
                                    className="mt-3 nspek-construct-result-container",
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Avbryt",
                                    id="nspek-dashboard-construct-cancel",
                                    className="ssb-btn secondary-btn",
                                ),
                                dbc.Button(
                                    "Konstruer",
                                    id="nspek-dashboard-construct-submit",
                                    className="ssb-btn primary-btn",
                                ),
                            ]
                        ),
                    ],
                    id="nspek-dashboard-construct-modal",
                    className="ssb-modal",
                    is_open=False,
                    scrollable=True,
                    size="xl",
                    style={
                        "maxWidth": "100vw",
                        "width": "100vw",
                    },
                ),
                html.Div(
                    [
                        self.create_kpi_modal(
                            modal_id=config["modal_id"],
                            title=config["title"],
                            grid_id=config["grid_id"],
                            column_defs=config["columns"],
                            description=config["description"],
                        )
                        for config in KPI_CONFIG.values()
                    ]
                ),

                # ============================================================
                # SSB CARDS
                # ============================================================

                dbc.Row(
                    [
                        dbc.Col(
                            self.create_kpi_card(
                                "Totalt i populasjonen",
                                "nspek-demo-card-total",
                                "feather:users",
                                "Totalt antall registreringer",
                                card_id="nspek-dashboard-total-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            self.create_kpi_card(
                                "Mottatt fra SKE",
                                "nspek-demo-card-ske",
                                "feather:database",
                                "Data mottatt fra SKE",
                                card_id="nspek-dashboard-ske-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            self.create_kpi_card(
                                "Konstruert",
                                "nspek-demo-card-bruker",
                                "feather:user-check",
                                "Registreringer opprettet av SSB",
                                card_id="nspek-dashboard-bruker-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            self.create_kpi_card(
                                "Skjønnslignet",
                                "nspek-demo-card-skjoenn",
                                "feather:alert-triangle",
                                "Registreringer skjønnslignet av SKE",
                                card_id="nspek-dashboard-skjoenn-card",
                            ),
                            md=3,
                        ),
                    ],
                    className="g-3 mb-5",
                ),
                
                # ============================================================
                # GREEN-BOX og LARGE og KNAPPER
                # ============================================================

                dbc.Row(
                    [
                        dbc.Col(
                            self.create_key_figure(
                                title="Fullføringsgrad",
                                component_id="nspek-dashboard-kf-completion",
                                size="medium",
                                subtitle="prosent",
                                time_text="Status for innsamlingen",
                                green_box=True,
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            self.create_key_figure(
                                title="Totalt i NSPEK-populasjonen",
                                component_id="nspek-dashboard-kf-total",
                                size="large",
                                icon="/proxy/8000/assets/test2.svg",
                                subtitle="foretak",
                                time_text="2026",
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        [
                                            html.Span("Oppdater data", className="ms-2"),
                                        ],
                                        id="nspek-dashboard-refresh",
                                        className="ssb-btn primary-btn",
                                    ),
                                    dbc.Button(
                                        [
                                            html.Span("Konstruer", className="ms-2"),
                                        ],
                                        id="nspek-dashboard-construct",
                                        className="ssb-btn primary-btn",
                                    ),
                                    #dbc.Button(
                                    #    [
                                    #        html.Span("Innstillinger", className="ms-2"),
                                    #    ],
                                    #    id="nspek-dashboard-settings",
                                    #    className="ssb-btn primary-btn",
                                    #),
                                    #dbc.Button(
                                    #    [
                                    #        html.Span("Hjelp", className="ms-2"),
                                    #    ],
                                    #    id="nspek-dashboard-help",
                                    #    className="ssb-btn primary-btn",
                                    #),
                                ],
                                className="nspek-dashboard-action-buttons",
                            ),
                            md=2,
                            className="d-flex justify-content-end align-items-start",
                        ),
                    ],
                    className="mb-5",
                ),

                # ============================================================
                # GRAFER
                # ============================================================

                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Fordeling i innsamling",
                                            className="ssb-chart-title",
                                        ),

                                        html.Div(
                                            dcc.Tabs(
                                                id="nspek-dashboard-development-tabs",
                                                value="figure",
                                                children=[
                                                    dcc.Tab(
                                                        label="Vis som figur",
                                                        value="figure",
                                                        children=[
                                                            dcc.Graph(
                                                                id="nspek-dashboard-development-graph",
                                                                config={"displayModeBar": False},
                                                            )
                                                        ],
                                                    ),
                                                    dcc.Tab(
                                                        label="Vis som tabell",
                                                        value="table",
                                                        children=[
                                                            self.create_development_table(
                                                                get_demo_population_data()
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                className="ssb-chart-tabs",
                                            )
                                        ),
                                    ]
                                ),
                                className="h-100 ssb-chart-card",
                            ),
                            md=12,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Fordeling i innsamling",
                                            className="ssb-chart-title",
                                        ),
                                        dcc.Tabs(
                                            id="nspek-dashboard-distribution-tabs",
                                            value="figure",
                                            children=[
                                                dcc.Tab(
                                                    label="Vis som figur",
                                                    value="figure",
                                                    children=[
                                                        dcc.Graph(
                                                            id="nspek-dashboard-distribution-graph",
                                                            config={"displayModeBar": False},
                                                        )
                                                    ],
                                                ),
                                                dcc.Tab(
                                                    label="Vis som tabell",
                                                    value="table",
                                                    children=[
                                                        self.create_distribution_table(
                                                            get_demo_population_data()
                                                        ),
                                                    ],
                                                ),
                                            ],
                                            className="ssb-chart-tabs",
                                        )
                                    ]
                                ),
                                className="h-100 ssb-chart-card",
                            ),
                            md=12,
                        ),
                    ],
                    className="g-3 mb-5",
                ),

                # ============================================================
                # MEDIUM KEY FIGURES
                # ============================================================
                
                html.H4(
                    "Medium – gruppe på to",
                    className="mb-3",
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            self.create_key_figure(
                                title="Mottatt fra SKE",
                                component_id="nspek-dashboard-kf-ske",
                                size="medium",
                                icon="/proxy/8000/assets/test.svg",
                                subtitle="foretak",
                                time_text="2026",
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            self.create_key_figure(
                                title="Konstruert av bruker",
                                component_id="nspek-dashboard-kf-bruker",
                                size="medium",
                                icon="/proxy/8000/assets/test2.svg",
                                subtitle="foretak",
                                time_text="2026",
                            ),
                            md=6,
                        ),
                    ],
                    className="g-4 mb-5",
                ),

                # ============================================================
                # SMALL
                # ============================================================

                html.H4(
                    "Small – gruppe på fire",
                    className="mb-3",
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            self.create_key_figure(
                                title="Innkommet siste uke",
                                component_id="nspek-dashboard-kf-weekly",
                                size="small",
                                icon="/proxy/8000/assets/test.svg",
                                subtitle="registreringer",
                                time_text="Uke 35",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            self.create_key_figure(
                                title="Ferdigstilt",
                                component_id="nspek-dashboard-kf-finished",
                                size="small",
                                icon="/proxy/8000/assets/test2.svg",
                                subtitle="registreringer",
                                time_text="2026",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            self.create_key_figure(
                                title="Gjenstår",
                                component_id="nspek-dashboard-kf-remaining",
                                size="small",
                                icon="/proxy/8000/assets/test.svg",
                                subtitle="registreringer",
                                time_text="2026",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            self.create_key_figure(
                                title="Feilregistreringer",
                                component_id="nspek-dashboard-kf-errors",
                                size="small",
                                icon="/proxy/8000/assets/test2.svg",
                                subtitle="registreringer",
                                time_text="2026",
                            ),
                            md=4,
                        ),
                    ],
                    className="g-4 mb-5",
                ),
            ],
            className="nspek-dashboard-container",
        )


    def module_callbacks(self) -> None:
        """Defines the callbacks for the Naeringsspesifikasjon module."""

        @callback(
            # Cards
            Output("nspek-demo-card-total", "children"),
            Output("nspek-demo-card-bruker", "children"),
            Output("nspek-demo-card-ske", "children"),
            Output("nspek-demo-card-skjoenn", "children"),

            # Medium
            Output("nspek-dashboard-kf-ske", "children"),
            Output("nspek-dashboard-kf-bruker", "children"),

            # Small
            Output("nspek-dashboard-kf-weekly", "children"),
            Output("nspek-dashboard-kf-finished", "children"),
            Output("nspek-dashboard-kf-remaining", "children"),
            Output("nspek-dashboard-kf-errors", "children"),

            # Large
            Output("nspek-dashboard-kf-total", "children"),

            # Green box
            Output("nspek-dashboard-kf-completion", "children"),

            # Graphs
            Output("nspek-dashboard-development-graph", "figure"),
            Output("nspek-dashboard-distribution-graph", "figure"),

            Input("nspek-dashboard-refresh", "n_clicks"),
        )
        def update_dashboard(n_clicks):

            df = get_demo_population_data()

            bruker = df["bruker"].iloc[-1]
            ske = df["ske"].iloc[-1]
            skjoenn = df["skjoenn"].iloc[-1]

            total = bruker + ske + skjoenn

            # Demo-tall
            weekly = 124
            finished = 598
            remaining = total - finished
            errors = 42

            completion_rate = (
                finished / total * 100
                if total
                else 0
            )

            # Grafer
            development_figure = self.create_development_figure(df)
            distribution_figure = self.create_distribution_figure(df)

            return (
                # Cards
                f"{total:,}".replace(",", " "),
                f"{bruker:,}".replace(",", " "),
                f"{ske:,}".replace(",", " "),
                f"{skjoenn:,}".replace(",", " "),

                # Medium
                f"{ske:,}".replace(",", " "),
                f"{bruker:,}".replace(",", " "),

                # Small
                f"{weekly:,}".replace(",", " "),
                f"{finished:,}".replace(",", " "),
                f"{remaining:,}".replace(",", " "),
                f"{errors:,}".replace(",", " "),

                # Large
                f"{total:,}".replace(",", " "),

                # Green box
                f"{completion_rate:.1f}".replace(".", ","),

                # Graphs
                development_figure,
                distribution_figure,
            )

        @callback(
            Output(
                "nspek-dashboard-construct-modal",
                "is_open",
            ),
            Input(
                "nspek-dashboard-construct",
                "n_clicks",
            ),
            Input(
                "nspek-dashboard-construct-cancel",
                "n_clicks",
            ),
            State(
                "nspek-dashboard-construct-modal",
                "is_open",
            ),
            prevent_initial_call=True,
        )
        def toggle_construct_modal(
            open_clicks,
            cancel_clicks,
            is_open,
        ):
            return not is_open

        @callback(
            Output(
                "nspek-dashboard-construct-result",
                "children",
            ),
            Input(
                "nspek-dashboard-construct-submit",
                "n_clicks",
            ),
            State(
                "nspek-dashboard-construct-orgnr",
                "value",
            ),
            prevent_initial_call=True,
        )
        def construct_sequences(
            n_clicks,
            orgnr_text,
        ):
            if not orgnr_text or not orgnr_text.strip():
                return self.create_dialog(
                    variant="warning",
                    message="Skriv inn minst ett organisasjonsnummer.",
                    title="Advarsel",
                )

            orgnr_list = list(
                dict.fromkeys(
                    orgnr.strip()
                    for orgnr in orgnr_text.splitlines()
                    if orgnr.strip()
                )
            )

            results = []

            for orgnr in orgnr_list:

                # --------------------------------------------------------
                # Valider format
                # --------------------------------------------------------

                if len(orgnr) > 9:
                    results.append(
                        {
                            "status": "warning",
                            "orgnr": f"{orgnr[:12]}...",
                            "message": (
                                "Ugyldig organisasjonsnummer. "
                                "Organisasjonsnummeret kan ikke være lengre enn 9 tegn."
                            ),
                        }
                    )
                    continue

                if not re.fullmatch(r"\d{9}", orgnr):
                    results.append(
                        {
                            "status": "warning",
                            "orgnr": orgnr,
                            "message": (
                                "Ugyldig organisasjonsnummer. "
                                "Organisasjonsnummer må bestå av 9 siffer."
                            ),
                        }
                    )
                    continue

                # --------------------------------------------------------
                # Sjekk BoF
                # --------------------------------------------------------

                if not orgnr_exists_in_bof(orgnr):
                    results.append(
                        {
                            "status": "warning",
                            "orgnr": orgnr,
                            "message": (
                                "Ugyldig organisasjonsnummer. "
                                "Organisasjonsnummeret finnes ikke i BoF."
                            ),
                        }
                    )
                    continue

                # --------------------------------------------------------
                # Mock DB-sjekk + konstruksjon
                # --------------------------------------------------------

                result = construct_sequence(orgnr)
                results.append(result)

            all_processed = bool(results)

            return html.Div(
                [
                    # ------------------------------------------------------------
                    # Status for jobben
                    # ------------------------------------------------------------

                    html.Div(
                        "Status for jobben",
                        className="nspek-construct-result-label",
                    ),

                    self.create_dialog(
                        variant="success",
                        message="Alle organisasjonsnummer behandlet.",
                        title="Suksess",
                    ),

                    # ------------------------------------------------------------
                    # Status per organisasjonsnummer
                    # ------------------------------------------------------------

                    html.Div(
                        "Status per organisasjonsnummer",
                        className="nspek-construct-result-label mt-2",
                    ),

                    *[
                        self.create_mini_dialog(
                            variant=result["status"],
                            title={
                                "success": "Suksess",
                                "info": "Informasjon",
                                "warning": "Advarsel",
                            }[result["status"]],
                            orgnr=result["orgnr"],
                            message=result["message"],
                        )
                        for result in results
                    ],
                ]
            )

        @callback(
            Output("nspek-dashboard-bruker-modal", "is_open"),
            Output("nspek-dashboard-ske-modal", "is_open"),
            Output("nspek-dashboard-total-modal", "is_open"),
            Output("nspek-dashboard-skjoenn-modal", "is_open"),

            # Åpne
            Input("nspek-dashboard-bruker-card", "n_clicks"),
            Input("nspek-dashboard-ske-card", "n_clicks"),
            Input("nspek-dashboard-total-card", "n_clicks"),
            Input("nspek-dashboard-skjoenn-card", "n_clicks"),

            # Lukke
            Input("nspek-dashboard-bruker-modal-close", "n_clicks"),
            Input("nspek-dashboard-ske-modal-close", "n_clicks"),
            Input("nspek-dashboard-total-modal-close", "n_clicks"),
            Input("nspek-dashboard-skjoenn-modal-close", "n_clicks"),

            # Nåværende state
            State("nspek-dashboard-bruker-modal", "is_open"),
            State("nspek-dashboard-ske-modal", "is_open"),
            State("nspek-dashboard-total-modal", "is_open"),
            State("nspek-dashboard-skjoenn-modal", "is_open"),

            prevent_initial_call=True,
        )
        def toggle_kpi_modals(
            bruker_clicks,
            ske_clicks,
            total_clicks,
            skjoenn_clicks,
            bruker_close,
            ske_close,
            total_close,
            skjoenn_close,
            bruker_open,
            ske_open,
            total_open,
            skjoenn_open,
        ):
            triggered_id = ctx.triggered_id

            card_to_index = {
                "nspek-dashboard-bruker-card": 0,
                "nspek-dashboard-ske-card": 1,
                "nspek-dashboard-total-card": 2,
                "nspek-dashboard-skjoenn-card": 3,
            }

            close_to_index = {
                "nspek-dashboard-bruker-modal-close": 0,
                "nspek-dashboard-ske-modal-close": 1,
                "nspek-dashboard-total-modal-close": 2,
                "nspek-dashboard-skjoenn-modal-close": 3,
            }

            if triggered_id in card_to_index:
                states = [False, False, False, False]
                states[card_to_index[triggered_id]] = True
                return tuple(states)

            if triggered_id in close_to_index:
                states = [
                    bruker_open,
                    ske_open,
                    total_open,
                    skjoenn_open,
                ]
                states[close_to_index[triggered_id]] = False
                return tuple(states)

            return (
                bruker_open,
                ske_open,
                total_open,
                skjoenn_open,
            )

        @callback(
            Output("nspek-dashboard-bruker-grid", "rowData"),
            Output("nspek-dashboard-bruker-grid-count", "children"),

            Output("nspek-dashboard-ske-grid", "rowData"),
            Output("nspek-dashboard-ske-grid-count", "children"),

            Output("nspek-dashboard-total-grid", "rowData"),
            Output("nspek-dashboard-total-grid-count", "children"),

            Output("nspek-dashboard-skjoenn-grid", "rowData"),
            Output("nspek-dashboard-skjoenn-grid-count", "children"),

            # Kort
            Input("nspek-dashboard-bruker-card", "n_clicks"),
            Input("nspek-dashboard-ske-card", "n_clicks"),
            Input("nspek-dashboard-total-card", "n_clicks"),
            Input("nspek-dashboard-skjoenn-card", "n_clicks"),

            # Oppdater-knapper
            Input("nspek-dashboard-bruker-grid-refresh", "n_clicks"),
            Input("nspek-dashboard-ske-grid-refresh", "n_clicks"),
            Input("nspek-dashboard-total-grid-refresh", "n_clicks"),
            Input("nspek-dashboard-skjoenn-grid-refresh", "n_clicks"),

            prevent_initial_call=True,
        )
        def update_kpi_metadata(
            bruker_clicks,
            ske_clicks,
            total_clicks,
            skjoenn_clicks,
            bruker_refresh,
            ske_refresh,
            total_refresh,
            skjoenn_refresh,
        ):
            kpi_by_trigger = {
                "nspek-dashboard-bruker-card": "bruker",
                "nspek-dashboard-ske-card": "ske",
                "nspek-dashboard-total-card": "total",
                "nspek-dashboard-skjoenn-card": "skjoenn",

                "nspek-dashboard-bruker-grid-refresh": "bruker",
                "nspek-dashboard-ske-grid-refresh": "ske",
                "nspek-dashboard-total-grid-refresh": "total",
                "nspek-dashboard-skjoenn-grid-refresh": "skjoenn",
            }

            kpi_type = kpi_by_trigger.get(ctx.triggered_id)

            if kpi_type is None:
                raise PreventUpdate

            data = get_kpi_metadata(kpi_type)
            count = f"{len(data):,}".replace(",", " ")

            return (
                data if kpi_type == "bruker" else no_update,
                count if kpi_type == "bruker" else no_update,

                data if kpi_type == "ske" else no_update,
                count if kpi_type == "ske" else no_update,

                data if kpi_type == "total" else no_update,
                count if kpi_type == "total" else no_update,

                data if kpi_type == "skjoenn" else no_update,
                count if kpi_type == "skjoenn" else no_update,
            )


class NspekDashboardTab(TabImplementation, NspekDashboard):
    """NaeringsspesifikasjonTab is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""

    def __init__(self, time_units: list[str], db_user: str | None = None) -> None:
        """Initializes the NaeringsspesifikasjonTab class."""
        NspekDashboard.__init__(self, time_units=time_units, db_user=db_user)
        TabImplementation.__init__(self)


class NspekDashboardWindow(WindowImplementation, NspekDashboard):
    """NaeringsspesifikasjonWindow is an implementation of the Naeringsspesifikasjon module as a tab in a Dash application."""

    def __init__(
        self, time_units: list[str], db_user: str | None = None, **kwargs: Any
    ) -> None:
        """Initializes the NaeringsspesifikasjonWindow class."""
        NspekDashboard.__init__(self, time_units=time_units, db_user=db_user)
        WindowImplementation.__init__(self, **kwargs)
