import logging
import os
import re
import time
from pathlib import Path
from typing import Any
from typing import ClassVar
import plotly.express as px
import plotly.graph_objects as go

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
from dash_ag_grid import AgGrid
from dash_iconify import DashIconify
from ibis import _
from pandas.core.frame import DataFrame

from ...setup.variableselector import VariableSelector
from ...utils import TabImplementation
from ...utils import WindowImplementation
from ...utils.alert_handler import create_alert
from ...utils.module_validation import module_validator
from .nspek_utils import get_nspek_connection
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
    "constructed": {
        "title": "Konstruert",
        "card_id": "nspek-dashboard-constructed-card",
        "modal_id": "nspek-dashboard-constructed-modal",
        "grid_id": "nspek-dashboard-constructed-grid",
        "kilde": "K",
        "description": (
            "Viser registreringene som er konstruert av SSB, "
            "inkludert organisasjonsnummer og tidspunkt for registrering."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
            },
            {
                "field": "sekvensnummer",
                "headerName": "Sekvensnummer",
            },
        ],
    },
    "ske": {
        "title": "Mottatt fra SKE",
        "card_id": "nspek-dashboard-ske-card",
        "modal_id": "nspek-dashboard-ske-modal",
        "grid_id": "nspek-dashboard-ske-grid",
        "kilde": "N",
        "description": (
            "Viser registreringene som er mottatt fra Skatteetaten (SKE), "
            "inkludert organisasjonsnummer og tidspunkt for mottak."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": False,
                "sortable": False,
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
                "filter": False,
                "sortable": False,
            },
            {
                "field": "sekvensnummer",
                "headerName": "Sekvensnummer",
                "filter": False,
                "sortable": False,
            },
        ],
    },
    "total": {
        "title": "Totalt i populasjonen",
        "card_id": "nspek-dashboard-total-card",
        "modal_id": "nspek-dashboard-total-modal",
        "grid_id": "nspek-dashboard-total-grid",
        "kilde": None,
        "description": (
            "Viser alle registreringene i populasjonen, "
            "uavhengig av hvordan registreringen er opprettet."
        ),
        "columns": [
            {
                "field": "orgnr",
                "headerName": "Organisasjonsnummer",
                "filter": False,
                "sortable": False,
            },
            {
                "field": "tidspunkt",
                "headerName": "Tidspunkt",
                "filter": False,
                "sortable": False,
            },
            {
                "field": "kilde",
                "headerName": "Kilde",
                "filter": False,
                "sortable": False,
            },
            {
                "field": "sekvensnummer",
                "headerName": "Sekvensnummer",
                "filter": False,
                "sortable": False,
            },
        ],
    },
}


def get_nspek_kpi_modal_data(
    aar: int,
    kilde: str | None = None,
    start_row: int = 0,
    end_row: int = 100,
) -> tuple[pd.DataFrame, int]:
    """Return one page of KPI modal rows and the total row count."""

    aar = int(aar)
    start_row = max(int(start_row), 0)
    end_row = max(int(end_row), start_row)
    limit = max(end_row - start_row, 1)

    kilde_filter = "" if kilde is None else f"AND kilde = '{kilde}'"

    with get_nspek_connection() as conn:
        query = f"""
            SELECT
                orgnr,
                dato_mottatt AS tidspunkt,
                kilde,
                sekvensnummer
            FROM nspek_core.registrering
            WHERE aar = {aar}
              {kilde_filter}
            ORDER BY dato_mottatt DESC, sekvensnummer DESC
            LIMIT {limit}
            OFFSET {start_row}
        """

        cursor = conn.raw_sql(query)
        try:
            rows = cursor.fetchall()
        finally:
            cursor.close()

        count_query = f"""
            SELECT COUNT(*)
            FROM nspek_core.registrering
            WHERE aar = {aar}
              {kilde_filter}
        """

        cursor = conn.raw_sql(count_query)
        try:
            count_row = cursor.fetchone()
        finally:
            cursor.close()

    df = pd.DataFrame(
        rows,
        columns=["orgnr", "tidspunkt", "kilde", "sekvensnummer"],
    )

    if not df.empty:
        df["tidspunkt"] = pd.to_datetime(
            df["tidspunkt"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

    return df, int(count_row[0] or 0)

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


def construct_sequence(
    orgnr: str,
    aar: int,
) -> dict[str, str | int]:
    """Check for existing NSPEK registration and construct if needed."""

    orgnr = str(orgnr).strip()
    aar = int(aar)

    try:
        with get_nspek_connection() as conn:
            # ------------------------------------------------------------
            # Sjekk om det allerede finnes en registrering
            # ------------------------------------------------------------
            query = f"""
                SELECT sekvensnummer
                FROM nspek_core.registrering
                WHERE orgnr = '{orgnr}'
                  AND aar = {aar}
                LIMIT 1
            """

            cursor = conn.raw_sql(query)

            try:
                row = cursor.fetchone()
            finally:
                cursor.close()

            if row is not None:
                sekvensnummer = row[0]

                return {
                    "status": "info",
                    "orgnr": orgnr,
                    "sekvensnummer": sekvensnummer,
                    "message": (
                        "Det finnes allerede en "
                        f"næringsspesifikasjon ({sekvensnummer}) "
                        f"for {aar}."
                    ),
                }

            # ------------------------------------------------------------
            # Opprett ny tom næringsspesifikasjon
            # ------------------------------------------------------------
            query = f"""
                INSERT INTO nspek_core.registrering (
                    aar,
                    sekvensnummer,
                    orgnr,
                    dato_mottatt,
                    kilde
                )
                VALUES (
                    {aar},
                    nextval('nspek_core.construct_seq'),
                    '{orgnr}',
                    now(),
                    'K'
                )
                RETURNING sekvensnummer
            """

            cursor = conn.raw_sql(query)

            try:
                row = cursor.fetchone()
            finally:
                cursor.close()

            sekvensnummer = row[0]

            return {
                "status": "success",
                "orgnr": orgnr,
                "sekvensnummer": sekvensnummer,
                "message": (
                    "Ny næringsspesifikasjon ble konstruert "
                    f"med sekvensnummer ({sekvensnummer})."
                ),
            }

    except Exception:
        logger.exception(
            "Feil ved konstruksjon av NSPEK for %s",
            orgnr,
        )

        return {
            "status": "warning",
            "orgnr": orgnr,
            "message": (
                "Det oppstod en feil ved konstruksjon "
                "av næringsspesifikasjonen."
            ),
        }


def get_nspek_kpis(aar: int) -> dict[str, int]:
    """Return KPI values for NSPEK registrations."""

    aar = int(aar)

    with get_nspek_connection() as conn:
        query = f"""
            SELECT
                COUNT(*) FILTER (WHERE kilde = 'K') AS antall_konstruerte,
                COUNT(*) FILTER (WHERE kilde = 'N') AS antall_ske,
                COUNT(*) AS antall_totalt
            FROM nspek_core.registrering
            WHERE aar = {aar}
        """

        cursor = conn.raw_sql(query)

        try:
            row = cursor.fetchone()
        finally:
            cursor.close()

    return {
        "antall_konstruerte": int(row[0] or 0),
        "antall_ske": int(row[1] or 0),
        "antall_totalt": int(row[2] or 0),
    }


def get_nspek_development_data(aar: int) -> pd.DataFrame:
    """Return monthly NSPEK registration counts for the selected year."""

    aar = int(aar)

    with get_nspek_connection() as conn:
        query = f"""
            SELECT
                DATE_TRUNC('month', dato_mottatt) AS maaned,
                COUNT(*) FILTER (WHERE kilde = 'K') AS konstruert,
                COUNT(*) FILTER (WHERE kilde = 'N') AS ske
            FROM nspek_core.registrering
            WHERE aar = {aar}
            GROUP BY DATE_TRUNC('month', dato_mottatt)
            ORDER BY maaned
        """

        cursor = conn.raw_sql(query)

        try:
            rows = cursor.fetchall()
        finally:
            cursor.close()

    return pd.DataFrame(
        rows,
        columns=["maaned", "konstruert", "ske"],
    )


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

    def create_dropdown_card(
        self,
        title: str,
        component_id: str,
        options=None,
        value=None,
    ):
        dropdown_card = html.Div(
            children=[
                html.Span(title, className="dropdown-label"),
                dcc.Dropdown(
                    id=component_id,
                    className="ssb-dropdown",
                    options=options,
                    value=value,
                    placeholder="-- Velg --",
                    clearable=False,
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
                                        icon="/proxy/8000/assets/test.svg",
                                        subtitle="foretak",
                                        time_text="Valgt årgang",
                                    ),
                                    md=8,
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
                                    md=4,
                                    className="d-flex flex-column",
                                ),
                            ],
                            className="mb-4 align-items-stretch",
                        ),

                        AgGrid(
                            id=grid_id,
                            columnDefs=column_defs,
                            defaultColDef={
                                "sortable": False,
                                "filter": False,
                                "resizable": True,
                            },
                            columnSize="sizeToFit",
                            rowModelType="infinite",
                            dashGridOptions={
                                "animateRows": False,
                                "pagination": True,
                                "paginationPageSize": 100,
                                "cacheBlockSize": 100,
                                "maxBlocksInCache": 5,
                                "infiniteInitialRowCount": 1,
                                "rowBuffer": 0,
                                "maxConcurrentDatasourceRequests": 1,
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
            id_vars="maaned",
            value_vars=["konstruert", "ske"],
            var_name="kilde",
            value_name="antall",
        )

        labels = {
            "konstruert": "Konstruert",
            "ske": "Mottatt fra SKE",
        }
        long_df["kilde"] = long_df["kilde"].map(labels)

        long_df["maaned_label"] = (
            pd.to_datetime(long_df["maaned"])
            .dt.month.map(
                {
                    1: "Januar",
                    2: "Februar",
                    3: "Mars",
                    4: "April",
                    5: "Mai",
                    6: "Juni",
                    7: "Juli",
                    8: "August",
                    9: "September",
                    10: "Oktober",
                    11: "November",
                    12: "Desember",
                }
            )
            + " "
            + pd.to_datetime(long_df["maaned"]).dt.year.astype(str)
        )

        fig = px.line(
            long_df,
            x="maaned",
            y="antall",
            color="kilde",
            markers=True,
            color_discrete_map={
                "Konstruert": "#075745",
                "Mottatt fra SKE": "#1A9D49",
            },
            custom_data=["maaned_label"],
        )

        fig.update_traces(
            marker=dict(size=8),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{fullData.name}: %{y}<extra></extra>"
            ),
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
        fig = px.bar(
            df,
            x="kategori",
            y="antall",
            text="antall",
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            margin={"l": 10, "r": 20, "t": 20, "b": 50},
            showlegend=False,
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
                "title": "Antall registreringer",
                "showgrid": True,
                "gridcolor": "#E6E6E6",
                "gridwidth": 1,
                "showline": True,
                "linecolor": "#21383A",
                "linewidth": 1,
            },
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        return fig

    def create_development_table(self, df: pd.DataFrame) -> html.Div:
        table_df = df.copy()

        if not table_df.empty:
            maaneder = {
                1: "Januar",
                2: "Februar",
                3: "Mars",
                4: "April",
                5: "Mai",
                6: "Juni",
                7: "Juli",
                8: "August",
                9: "September",
                10: "Oktober",
                11: "November",
                12: "Desember",
            }

            dato = pd.to_datetime(table_df["maaned"])

            table_df["maaned"] = (
                dato.dt.month.map(maaneder)
                + " "
                + dato.dt.year.astype(str)
            )

        table_df = table_df.rename(
            columns={
                "maaned": "Måned",
                "konstruert": "Konstruert",
                "ske": "Mottatt fra SKE",
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

        return html.Div(table, className="ssb-table-wrapper")

    def create_distribution_table(self, df: pd.DataFrame) -> html.Div:
        table_df = df.copy()
        table_df = table_df.rename(
            columns={
                "kategori": "Kategori",
                "antall": "Antall",
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

        return html.Div(table, className="ssb-table-wrapper")


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
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            self.create_dropdown_card(
                                                title="Årgang",
                                                component_id="nspek-dashboard-construct-aar",
                                                options=[
                                                    {"label": "2025", "value": 2025},
                                                    {"label": "2024", "value": 2024},
                                                ],
                                                value=2024,
                                            ),
                                            width=4,
                                        ),
                                    ],
                                    className="mb-3",
                                ),

                                html.Div(
                                    "Skriv inn ett eller flere organisasjonsnummer, ett per linje.",
                                    className="nspek-construct-result-label",
                                ),

                                html.Div(
                                    className="ssb-text-area",
                                    children=[
                                        dcc.Loading(
                                            id="nspek-dashboard-construct-loading",
                                            #type="circle",
                                            color="#00824D",
                                            overlay_style={
                                                "visibility": "visible",
                                                "filter": "blur(2px)",
                                            },
                                            children=[
                                                dbc.Textarea(
                                                    id="nspek-dashboard-construct-orgnr",
                                                    placeholder=(
                                                        "Eksempel:\n"
                                                        "979443137\n"
                                                        "932598957\n"
                                                        "987654321\n"
                                                        "999888777"
                                                    ),
                                                    className="comment-textarea",
                                                    readOnly=False,
                                                    style={
                                                        "width": "100%",
                                                        "height": "600px",
                                                        "padding": "10px 12px",
                                                    },
                                                ),
                                                html.Div(
                                                    id="nspek-dashboard-construct-loading-trigger",
                                                    style={"display": "none"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),

                                html.Small(
                                    (
                                        "Du kan også lime inn en liste med organisasjonsnummer. "
                                        "Duplikater vil bli fjernet i behandlingen."
                                    ),
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
                                    "Lukk",
                                    id="nspek-dashboard-construct-close",
                                    className="ssb-btn secondary-btn",
                                ),
                                dbc.Button(
                                    "Konstruer",
                                    id="nspek-dashboard-construct-submit",
                                    className="ssb-btn primary-btn",
                                    disabled=True,
                                ),
                            ]
                        ),
                    ],
                    id="nspek-dashboard-construct-modal",
                    className="ssb-modal",
                    is_open=False,
                    scrollable=True,
                    size="xl",
                    backdrop="static",
                    keyboard=False,
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
                                "nspek-dashboard-total-value",
                                "feather:users",
                                "Totalt antall registreringer",
                                card_id="nspek-dashboard-total-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            self.create_kpi_card(
                                "Mottatt fra SKE",
                                "nspek-dashboard-ske-value",
                                "feather:database",
                                "Data mottatt fra SKE",
                                card_id="nspek-dashboard-ske-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            self.create_kpi_card(
                                "Konstruert",
                                "nspek-dashboard-constructed-value",
                                "feather:user-check",
                                "Registreringer opprettet av SSB",
                                card_id="nspek-dashboard-constructed-card",
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    self.create_dropdown_card(
                                        title="Årgang",
                                        component_id="nspek-dashboard-aar",
                                        options=[
                                            {"label": "2025", "value": 2025},
                                            {"label": "2024", "value": 2024},
                                        ],
                                        value=2025,
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Oppdater data",
                                                id="nspek-dashboard-refresh",
                                                className="ssb-btn primary-btn",
                                            ),
                                            dbc.Button(
                                                "Konstruer",
                                                id="nspek-dashboard-construct",
                                                className="ssb-btn primary-btn",
                                            ),
                                        ],
                                        className="nspek-dashboard-action-buttons",
                                    ),
                                ],
                                className="d-flex flex-column gap-2",
                            ),
                            md=3,
                        ),
                    ],
                    className="g-3 mb-5",
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
                                            "Utvikling i innsamling",
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
                                                            html.Div(
                                                                id="nspek-dashboard-development-table"
                                                            )
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
                                            value="table",
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
                                                        html.Div(
                                                            id="nspek-dashboard-distribution-table"
                                                        )
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

            ],
            style={
                "width": "100%",
                "minWidth": "0",
                "maxWidth": "1180px",
            },
            className="nspek-dashboard-container",
        )


    def module_callbacks(self) -> None:
        """Defines the callbacks for the Naeringsspesifikasjon module."""

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
                "nspek-dashboard-construct-close",
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
            self.variableselector.get_output_object("ident"),
            self.variableselector.get_output_object("aar"),
            self.variableselector.get_output_object("foretak"),
            Output(
                "nspek-dashboard-construct-result",
                "children",
            ),
            Output(
                "nspek-dashboard-construct-loading-trigger",
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
            State(
                "nspek-dashboard-construct-aar",
                "value",
            ),
            prevent_initial_call=True,
            running=[
                (
                    Output(
                        "nspek-dashboard-construct-orgnr",
                        "readOnly",
                    ),
                    True,
                    False,
                ),
                (
                    Output(
                        "nspek-dashboard-construct-submit",
                        "disabled",
                        allow_duplicate=True,
                    ),
                    True,
                    False,
                ),
                (
                    Output(
                        "nspek-dashboard-construct-submit",
                        "children",
                    ),
                    "Konstruerer …",
                    "Konstruer",
                ),
                (
                    Output(
                        "nspek-dashboard-construct-close",
                        "disabled",
                    ),
                    True,
                    False,
                ),
            ],
        )
        def construct_sequences(
            n_clicks,
            orgnr_text,
            aar,
        ):
            # ================================================================
            # Valider input
            # ================================================================

            if aar is None:
                return (
                    no_update,
                    no_update,
                    no_update,
                    self.create_dialog(
                        variant="warning",
                        message=(
                            "Velg en årgang før du konstruerer "
                            "næringsspesifikasjoner."
                        ),
                        title="Advarsel",
                    ),
                    "",
                )

            if not orgnr_text or not orgnr_text.strip():
                return (
                    no_update,
                    no_update,
                    no_update,
                    self.create_dialog(
                        variant="warning",
                        message="Skriv inn minst ett organisasjonsnummer.",
                        title="Advarsel",
                    ),
                    "",
                )

            orgnr_list = list(
                dict.fromkeys(
                    orgnr.strip()
                    for orgnr in orgnr_text.splitlines()
                    if orgnr.strip()
                )
            )

            results = []

            # ================================================================
            # Behandle organisasjonsnummer
            # ================================================================

            for orgnr in orgnr_list:

                time.sleep(1)

                # ------------------------------------------------------------
                # Valider format
                # ------------------------------------------------------------

                if len(orgnr) > 9:
                    results.append(
                        {
                            "status": "warning",
                            "orgnr": f"{orgnr[:12]}...",
                            "message": (
                                "Ugyldig organisasjonsnummer. "
                                "Organisasjonsnummeret kan ikke være "
                                "lengre enn 9 tegn."
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

                # ------------------------------------------------------------
                # Sjekk BoF
                # ------------------------------------------------------------

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

                # ------------------------------------------------------------
                # DB-sjekk + konstruksjon
                # ------------------------------------------------------------

                result = construct_sequence(
                    orgnr=orgnr,
                    aar=aar,
                )

                results.append(result)
                print(result)

            # ================================================================
            # Status for jobben
            # ================================================================

            has_success = any(
                result["status"] in {"success", "info"}
                for result in results
            )

            if not has_success:
                job_dialog = self.create_dialog(
                    variant="warning",
                    message="Ingen organisasjonsnummer ble behandlet.",
                    title="Advarsel",
                )

            else:
                # ------------------------------------------------------------
                # Ett orgnr og vellykket behandling
                # ------------------------------------------------------------

                if len(orgnr_list) == 1:
                    orgnr = orgnr_list[0]

                    job_dialog = self.create_dialog(
                        variant="success",
                        message=(
                            f"Organisasjonsnummer {orgnr} er behandlet. "
                            f"Variabelvelgeren er nå oppdatert til "
                            f"{orgnr} og årgang {aar}."
                        ),
                        title="Suksess",
                    )

                # ------------------------------------------------------------
                # Flere orgnr og alle vellykket
                # ------------------------------------------------------------

                else:
                    job_dialog = self.create_dialog(
                        variant="success",
                        message="Alle organisasjonsnummer ble behandlet.",
                        title="Suksess",
                    )

            # ================================================================
            # Oppdater VariableSelector
            # ================================================================

            update_variableselector = (
                len(orgnr_list) == 1
                and len(results) == 1
                and results[0]["status"] in {"success", "info"}
            )

            if update_variableselector:
                variableselector_ident = orgnr_list[0]
                variableselector_aar = aar
                variableselector_foretak = orgnr_list[0]
            else:
                variableselector_ident = no_update
                variableselector_aar = no_update
                variableselector_foretak = no_update

            # ================================================================
            # Bygg resultatvisning
            # ================================================================

            result_content = html.Div(
                [
                    html.Div(
                        "Status for jobben",
                        className="nspek-construct-result-label",
                    ),

                    job_dialog,

                    # --------------------------------------------------------
                    # Status per organisasjonsnummer
                    # --------------------------------------------------------

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

            return (
                variableselector_ident,
                variableselector_aar,
                variableselector_foretak,
                result_content,
                "",
            )

        @callback(
            Output(
                "nspek-dashboard-construct-submit",
                "disabled",
            ),
            Input(
                "nspek-dashboard-construct-aar",
                "value",
            ),
            Input(
                "nspek-dashboard-construct-orgnr",
                "value",
            ),
        )
        def update_construct_button_disabled(aar, orgnr_text):
            return (
                aar is None
                or not orgnr_text
                or not orgnr_text.strip()
            )

        @callback(
            Output("nspek-dashboard-total-modal", "is_open"),
            Output("nspek-dashboard-ske-modal", "is_open"),
            Output("nspek-dashboard-constructed-modal", "is_open"),
            Input("nspek-dashboard-total-card", "n_clicks"),
            Input("nspek-dashboard-total-modal-close", "n_clicks"),
            Input("nspek-dashboard-ske-card", "n_clicks"),
            Input("nspek-dashboard-ske-modal-close", "n_clicks"),
            Input("nspek-dashboard-constructed-card", "n_clicks"),
            Input("nspek-dashboard-constructed-modal-close", "n_clicks"),
            State("nspek-dashboard-total-modal", "is_open"),
            State("nspek-dashboard-ske-modal", "is_open"),
            State("nspek-dashboard-constructed-modal", "is_open"),
            prevent_initial_call=True,
        )
        def toggle_kpi_modals(
            total_card_clicks,
            total_close_clicks,
            ske_card_clicks,
            ske_close_clicks,
            constructed_card_clicks,
            constructed_close_clicks,
            total_is_open,
            ske_is_open,
            constructed_is_open,
        ):
            triggered_id = ctx.triggered_id

            states = [total_is_open, ske_is_open, constructed_is_open]

            if triggered_id == "nspek-dashboard-total-card":
                return True, False, False
            if triggered_id == "nspek-dashboard-total-modal-close":
                return False, ske_is_open, constructed_is_open
            if triggered_id == "nspek-dashboard-ske-card":
                return False, True, False
            if triggered_id == "nspek-dashboard-ske-modal-close":
                return total_is_open, False, constructed_is_open
            if triggered_id == "nspek-dashboard-constructed-card":
                return False, False, True
            if triggered_id == "nspek-dashboard-constructed-modal-close":
                return total_is_open, ske_is_open, False

            return states

        @callback(
            Output("nspek-dashboard-total-grid-count", "children"),
            Output("nspek-dashboard-ske-grid-count", "children"),
            Output("nspek-dashboard-constructed-grid-count", "children"),
            Input("nspek-dashboard-aar", "value"),
            Input("nspek-dashboard-refresh", "n_clicks"),
            Input("nspek-dashboard-total-grid-refresh", "n_clicks"),
            Input("nspek-dashboard-ske-grid-refresh", "n_clicks"),
            Input("nspek-dashboard-constructed-grid-refresh", "n_clicks"),
        )
        def update_kpi_modal_counts(
            aar,
            _dashboard_refresh,
            _total_refresh,
            _ske_refresh,
            _constructed_refresh,
        ):
            if aar is None:
                return "0", "0", "0"

            kpis = get_nspek_kpis(aar)

            return (
                f"{kpis['antall_totalt']:,}".replace(",", " "),
                f"{kpis['antall_ske']:,}".replace(",", " "),
                f"{kpis['antall_konstruerte']:,}".replace(",", " "),
            )

        @callback(
            Output("nspek-dashboard-total-grid", "getRowsResponse"),
            Input("nspek-dashboard-total-grid", "getRowsRequest"),
            State("nspek-dashboard-aar", "value"),
        )
        def load_total_kpi_rows(request, aar):
            if not request or aar is None:
                return {"rowData": [], "rowCount": 0}

            df, total_count = get_nspek_kpi_modal_data(
                aar,
                start_row=request.get("startRow", 0),
                end_row=request.get("endRow", 100),
            )

            return {"rowData": df.to_dict("records"), "rowCount": total_count}

        @callback(
            Output("nspek-dashboard-ske-grid", "getRowsResponse"),
            Input("nspek-dashboard-ske-grid", "getRowsRequest"),
            State("nspek-dashboard-aar", "value"),
        )
        def load_ske_kpi_rows(request, aar):
            if not request or aar is None:
                return {"rowData": [], "rowCount": 0}

            df, total_count = get_nspek_kpi_modal_data(
                aar,
                kilde="N",
                start_row=request.get("startRow", 0),
                end_row=request.get("endRow", 100),
            )

            return {"rowData": df.to_dict("records"), "rowCount": total_count}

        @callback(
            Output("nspek-dashboard-constructed-grid", "getRowsResponse"),
            Input("nspek-dashboard-constructed-grid", "getRowsRequest"),
            State("nspek-dashboard-aar", "value"),
        )
        def load_constructed_kpi_rows(request, aar):
            if not request or aar is None:
                return {"rowData": [], "rowCount": 0}

            df, total_count = get_nspek_kpi_modal_data(
                aar,
                kilde="K",
                start_row=request.get("startRow", 0),
                end_row=request.get("endRow", 100),
            )

            return {"rowData": df.to_dict("records"), "rowCount": total_count}

        @callback(
            Output("nspek-dashboard-total-value", "children"),
            Output("nspek-dashboard-ske-value", "children"),
            Output("nspek-dashboard-constructed-value", "children"),
            Output("nspek-dashboard-development-graph", "figure"),
            Output("nspek-dashboard-development-table", "children"),
            Output("nspek-dashboard-distribution-graph", "figure"),
            Output("nspek-dashboard-distribution-table", "children"),
            Input("nspek-dashboard-aar", "value"),
            Input("nspek-dashboard-refresh", "n_clicks"),
        )
        def update_nspek_dashboard(aar, _n_clicks):
            if aar is None:
                empty_figure = go.Figure()
                message = html.Div("Velg en årgang.")
                return (
                    "–",
                    "–",
                    "–",
                    empty_figure,
                    message,
                    empty_figure,
                    message,
                )

            kpis = get_nspek_kpis(aar)
            development_df = get_nspek_development_data(aar)

            total = kpis["antall_totalt"]
            ske = kpis["antall_ske"]
            konstruert = kpis["antall_konstruerte"]

            distribution_df = pd.DataFrame(
                [
                    {
                        "kategori": "Mottatt fra SKE",
                        "antall": ske,
                    },
                    {
                        "kategori": "Konstruert",
                        "antall": konstruert,
                    },
                ]
            )

            development_figure = self.create_development_figure(
                development_df
            )
            development_table = self.create_development_table(
                development_df
            )
            distribution_figure = self.create_distribution_figure(
                distribution_df
            )
            distribution_table = self.create_distribution_table(
                distribution_df
            )

            return (
                f"{total:,}".replace(",", " "),
                f"{ske:,}".replace(",", " "),
                f"{konstruert:,}".replace(",", " "),
                development_figure,
                development_table,
                distribution_figure,
                distribution_table,
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
