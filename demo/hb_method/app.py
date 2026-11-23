"""Runnable HB demo with the Altinn adapter and the framework DataEditor."""

import os
import sqlite3
import tempfile
from collections.abc import Generator
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dash_bootstrap_components as dbc
import ibis
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash import no_update
from dash import set_props
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from ibis.backends import BaseBackend

from ssb_dash_framework import DataEditor
from ssb_dash_framework import DataViewCustom
from ssb_dash_framework import EditorSettings
from ssb_dash_framework import HBMethod
from ssb_dash_framework import StandardDataHandler
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import VariableSelectorOption
from ssb_dash_framework import app_setup
from ssb_dash_framework import get_connection
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_connection
from ssb_dash_framework.modules.data_editor.modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)
from ssb_dash_framework.modules.data_editor.modules.sidebar.editing_sidebar_helper import (
    DataEditorHelperSidebar,
)
from ssb_dash_framework.modules.hb import AltinnHBDataHandler
from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType
from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework_testdata.altinn import build_db

PORT = 8072
HB_DEMO_FORM = "RA-0745"
HB_DEMO_VARIABLE = "new_grass_area"
HB_DEMO_FIELD_PATH = "/NyEngArbAreal"
HB_DEMO_PERIODS = ("2024", "2025")
HB_DEMO_UNIT_IDS = tuple(f"90000000{unit_number + 1}" for unit_number in range(7))
HB_DEMO_PREVIOUS_VALUES = (10, 20, 30, 40, 50, 60, 70)
HB_DEMO_SELECTED_VALUES = (11, 22, 33, 44, 55, 66, 200)
HB_DEMO_EDITING_CODES = [
    {"label": "Statistisk gjennomgang", "value": "REVIEW"},
    {"label": "Kontakt med dataleverandør", "value": "OWNER"},
    {"label": "Kontroll mot annen kilde", "value": "OTHER_SOURCE"},
    {"label": "Marginal enhet", "value": "MARGINAL_UNIT"},
    {"label": "Dublett", "value": "DUPLICATE"},
    {"label": "Annen grunn", "value": "OTHER"},
]

HB_DEMO_SAVE_BUTTON_ID = "hb-demo-save-edit-button"
HB_DEMO_REASON_MODAL_ID = "hb-demo-reason-modal"
HB_DEMO_REASON_ID = "hb-demo-edit-reason"
HB_DEMO_COMMENT_ID = "hb-demo-edit-comment"
HB_DEMO_EDIT_DETAILS_ID = "hb-demo-edit-details"
HB_DEMO_EDIT_ERROR_ID = "hb-demo-edit-error"
HB_DEMO_CANCEL_ID = "hb-demo-cancel-edit"
HB_DEMO_CONFIRM_ID = "hb-demo-confirm-edit"


def _walk_components(component: Component) -> Iterator[Component]:
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, Component):
        yield from _walk_components(children)
    elif isinstance(children, (list, tuple)):
        for child in children:
            if isinstance(child, Component):
                yield from _walk_components(child)


@dataclass
class PendingHBDemoEdit:
    """Values staged by the demo editor until the user confirms the save."""

    refnr: str
    skjema: str | None
    ident: str
    period: str
    value: Any
    old_value: Any
    settings: EditorSettings
    container: FieldCallbackContainer


class HBDemoDataHandler(StandardDataHandler):
    """Stage DataEditor edits until the demo reason dialog confirms them."""

    def __init__(self) -> None:
        """Create a handler with no pending demo edit."""
        super().__init__()
        self.pending_edit: PendingHBDemoEdit | None = None

    def update_field_value(
        self,
        refnr: str,
        skjema: str | None,
        ident: str,
        period: str,
        value: Any,
        old_value: Any,
        settings: EditorSettings,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
        editing_code: str | None,
    ) -> None:
        """Stage a field edit instead of writing it before confirmation."""
        del inputs, editing_code
        self.pending_edit = PendingHBDemoEdit(
            refnr=refnr,
            skjema=skjema,
            ident=ident,
            period=period,
            value=value,
            old_value=old_value,
            settings=settings,
            container=container,
        )
        set_props(HB_DEMO_SAVE_BUTTON_ID, {"disabled": False})

    def describe_pending_edit(self) -> str:
        """Return the unit, period, and value change shown in the confirmation dialog."""
        if self.pending_edit is None:
            raise RuntimeError("Ingen ventende demoendring å vise.")
        edit = self.pending_edit
        return (
            f"Enhet {edit.ident}, periode {edit.period}: "
            f"{edit.old_value} → {edit.value}"
        )

    def save_pending_edit(self, reason: str, justification: str) -> None:
        """Atomically save the demo value and its reason/justification record."""
        edit = self.pending_edit
        if edit is None:
            raise RuntimeError("Ingen ventende demoendring å lagre.")
        if not any(option["value"] == reason for option in HB_DEMO_EDITING_CODES):
            raise ValueError("Velg en gyldig årsak.")
        if not justification.strip():
            raise ValueError("Skriv en begrunnelse.")

        variable = edit.container.settings.variable
        value = str(edit.value)
        with get_connection() as connection:
            current_value = connection.con.execute(
                """
                SELECT verdi
                FROM skjemadata
                WHERE refnr = ? AND ident = ? AND iso_periode = ? AND variabel = ?
                """,
                (edit.refnr, edit.ident, edit.period, variable),
            ).fetchone()
            if current_value is None:
                raise RuntimeError("Demoverdien finnes ikke lenger.")
            if str(current_value[0]) != str(edit.old_value):
                raise RuntimeError("Demoverdien ble endret før lagringen.")

            update_cursor = connection.con.execute(
                """
                UPDATE skjemadata
                SET verdi = ?
                WHERE refnr = ? AND ident = ? AND iso_periode = ?
                    AND variabel = ? AND verdi = ?
                """,
                (
                    value,
                    edit.refnr,
                    edit.ident,
                    edit.period,
                    variable,
                    str(edit.old_value),
                ),
            )
            if update_cursor.rowcount != 1:
                raise RuntimeError("Kunne ikke lagre den valgte demoverdien.")

            connection.con.execute(
                """
                INSERT INTO hb_demo_edit_history (
                    refnr, ident, iso_periode, variabel, old_value,
                    new_value, reason, justification
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edit.refnr,
                    edit.ident,
                    edit.period,
                    variable,
                    str(edit.old_value),
                    value,
                    reason,
                    justification.strip(),
                ),
            )

        self.pending_edit = None
        self.cache.evict(edit.refnr, edit.settings.form_data_table)
        set_props(HB_DEMO_SAVE_BUTTON_ID, {"disabled": True})


class HBDemoSaveEditSidebar(DataEditorHelperSidebar):
    """Offer the demo's explicit reason-and-justification save flow."""

    def __init__(self, data_handler: HBDemoDataHandler) -> None:
        """Connect the save dialog to the demo's temporary data handler."""
        self.data_handler = data_handler
        self.module_callbacks()
        super().__init__()

    def _create_layout(self) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Lagre redigering",
                    id=HB_DEMO_SAVE_BUTTON_ID,
                    className="ssb-btn primary-btn w-100",
                    disabled=True,
                ),
                html.Div(
                    "Endringer gjelder bare demo-data i denne kjøringen.",
                    className="small mt-2",
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader("Årsak og begrunnelse for endring"),
                        dbc.ModalBody(
                            [
                                html.Div(id=HB_DEMO_EDIT_DETAILS_ID, className="mb-3"),
                                dbc.Label("Velg årsak"),
                                dcc.RadioItems(
                                    id=HB_DEMO_REASON_ID,
                                    options=HB_DEMO_EDITING_CODES,
                                    value=None,
                                    className="mb-3",
                                ),
                                dbc.Label("Begrunnelse"),
                                dbc.Textarea(
                                    id=HB_DEMO_COMMENT_ID,
                                    placeholder="Skriv begrunnelse for endringen",
                                    autoFocus=True,
                                ),
                                html.Div(
                                    id=HB_DEMO_EDIT_ERROR_ID,
                                    role="alert",
                                    className="text-danger mt-2",
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Avbryt",
                                    id=HB_DEMO_CANCEL_ID,
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Bekreft lagring",
                                    id=HB_DEMO_CONFIRM_ID,
                                    color="primary",
                                ),
                            ]
                        ),
                    ],
                    id=HB_DEMO_REASON_MODAL_ID,
                    is_open=False,
                    backdrop="static",
                    centered=True,
                ),
            ]
        )

    def module_callbacks(self) -> None:
        """Open, validate, and submit the demo edit confirmation dialog."""
        @callback(
            Output(HB_DEMO_REASON_MODAL_ID, "is_open"),
            Output(HB_DEMO_EDIT_ERROR_ID, "children"),
            Output(HB_DEMO_EDIT_DETAILS_ID, "children"),
            Output(HB_DEMO_REASON_ID, "value"),
            Output(HB_DEMO_COMMENT_ID, "value"),
            Input(HB_DEMO_SAVE_BUTTON_ID, "n_clicks"),
            Input(HB_DEMO_CANCEL_ID, "n_clicks"),
            Input(HB_DEMO_CONFIRM_ID, "n_clicks"),
            State(HB_DEMO_REASON_ID, "value"),
            State(HB_DEMO_COMMENT_ID, "value"),
            prevent_initial_call=True,
        )
        def save_edit(
            _save_clicks: int | None,
            _cancel_clicks: int | None,
            _confirm_clicks: int | None,
            reason: str | None,
            justification: str | None,
        ) -> tuple[Any, Any, Any, Any, Any]:
            del _save_clicks, _cancel_clicks, _confirm_clicks
            if ctx.triggered_id == HB_DEMO_SAVE_BUTTON_ID:
                try:
                    details = self.data_handler.describe_pending_edit()
                except RuntimeError as error:
                    return False, str(error), "", no_update, no_update
                return True, "", details, None, ""
            if ctx.triggered_id == HB_DEMO_CANCEL_ID:
                return False, "", "", no_update, no_update
            if ctx.triggered_id == HB_DEMO_CONFIRM_ID:
                if reason is None:
                    return True, "Velg en årsak.", no_update, reason, justification or ""
                if not justification or not justification.strip():
                    return (
                        True,
                        "Skriv en begrunnelse.",
                        no_update,
                        reason,
                        justification or "",
                    )
                try:
                    self.data_handler.save_pending_edit(reason, justification)
                except (RuntimeError, ValueError) as error:
                    return True, str(error), no_update, reason, justification
                return False, "", "", None, ""
            raise PreventUpdate


@contextmanager
def _hb_demo_connection(
    *args: Any, **kwargs: Any
) -> Generator[BaseBackend]:
    del args, kwargs
    try:
        yield _demo_database_backend
        _demo_database_backend.con.commit()
    except Exception:
        _demo_database_backend.con.rollback()
        raise


def _seed_hb_demo_records(database_path: Path) -> None:
    """Extend the bundled Altinn fixture with a deterministic HB candidate."""
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS datatyper (
                iso_periode VARCHAR,
                variabel VARCHAR,
                datatype VARCHAR
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO datatyper (iso_periode, variabel, datatype)
            VALUES (?, ?, ?)
            """,
            [
                (period, HB_DEMO_FIELD_PATH, "integer")
                for period in HB_DEMO_PERIODS
            ],
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hb_demo_edit_history (
                refnr VARCHAR NOT NULL,
                ident VARCHAR NOT NULL,
                iso_periode VARCHAR NOT NULL,
                variabel VARCHAR NOT NULL,
                old_value VARCHAR NOT NULL,
                new_value VARCHAR NOT NULL,
                reason VARCHAR NOT NULL,
                justification VARCHAR NOT NULL
            )
            """
        )
        enhetsinfo_columns = {
            column_info[1]
            for column_info in connection.execute(
                "PRAGMA table_info(enhetsinfo)"
            ).fetchall()
        }
        if "aar" not in enhetsinfo_columns:
            connection.execute("ALTER TABLE enhetsinfo ADD COLUMN aar VARCHAR")

        skjemadata_columns = {
            column_info[1]
            for column_info in connection.execute(
                "PRAGMA table_info(skjemadata)"
            ).fetchall()
        }
        if "variabel" not in skjemadata_columns:
            connection.execute(
                "ALTER TABLE skjemadata ADD COLUMN variabel VARCHAR"
            )

        for unit_number, unit_id in enumerate(HB_DEMO_UNIT_IDS):
            for period, value in zip(
                HB_DEMO_PERIODS,
                (
                    HB_DEMO_PREVIOUS_VALUES[unit_number],
                    HB_DEMO_SELECTED_VALUES[unit_number],
                ),
                strict=True,
            ):
                existing_submissions = connection.execute(
                    """
                    SELECT refnr
                    FROM skjemamottak
                    WHERE skjema = ? AND ident = ? AND iso_periode = ? AND aktiv = 1
                    """,
                    (HB_DEMO_FORM, unit_id, period),
                ).fetchall()
                if existing_submissions:
                    raise RuntimeError(
                        f"Unexpected bundled submission for {unit_id} in {period}."
                    )

                reference_number = f"hb-demo-{unit_id}-{period}"
                connection.execute(
                    """
                    INSERT INTO enheter (iso_periode, ident, skjema)
                    VALUES (?, ?, ?)
                    """,
                    (period, unit_id, HB_DEMO_FORM),
                )
                connection.execute(
                    """
                    INSERT INTO skjemamottak (
                        iso_periode, start_dato, slutt_dato, skjema,
                        skjema_versjon, ident, refnr, kommentar,
                        dato_mottatt, status, aktiv
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        period,
                        f"{period}-01-01 00:00:00.000000",
                        f"{period}-12-31 23:59:59.999999",
                        HB_DEMO_FORM,
                        "1.8.15",
                        unit_id,
                        reference_number,
                        "",
                        f"{period}-12-15 09:00:00.000000",
                        "Ferdig",
                        True,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO skjemadata (
                        iso_periode, skjema, ident, refnr, feltsti,
                        feltnavn, verdi, alias, dybde, indeks, variabel
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        period,
                        HB_DEMO_FORM,
                        unit_id,
                        reference_number,
                        HB_DEMO_FIELD_PATH,
                        "NyEngArbAreal",
                        str(value),
                        None,
                        None,
                        None,
                        HB_DEMO_FIELD_PATH,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO enhetsinfo (
                        iso_periode, ident, variabel, verdi, aar
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (period, unit_id, "enhetsOrgNr", unit_id, period),
                )


def _create_hb_demo_database() -> BaseBackend:
    """Load the bundled fixture and synthetic records into process-local SQLite."""
    with tempfile.TemporaryDirectory(prefix="ssb_dash_framework_hb_seed_") as folder:
        seed_path = Path(folder) / "hb_demo_seed.sqlite"
        build_db.seed_sqlite(seed_path)
        _seed_hb_demo_records(seed_path)

        database = ibis.sqlite.connect(":memory:")
        seed_connection = sqlite3.connect(seed_path)
        try:
            seed_connection.backup(database.con)
        finally:
            seed_connection.close()
        return database


_demo_database_backend = _create_hb_demo_database()
set_connection(_hb_demo_connection)

configured_hb_time_unit = TimeUnit(
    name="periode",
    frequency=TimeUnitType.YEAR,
)
VariableSelectorConfig(
    refnr="refnr",
    ident="ident",
    time_units=configured_hb_time_unit,
    grouping_variables=["altinnskjema"],
)
VariableSelectorOption("measure")

app = app_setup(
    port=PORT,
    service_prefix=(
        os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
        if os.getenv("DAPLA_ENVIRONMENT")
        else ""
    ),
    stylesheet="lumen",
    enable_logging=False,
)

hb_method = HBMethod(
    hb_data_handler=AltinnHBDataHandler(
        configured_hb_form=HB_DEMO_FORM,
        hb_variable_to_feltsti={HB_DEMO_VARIABLE: HB_DEMO_FIELD_PATH},
    ),
    hb_variable_selector="measure",
    configured_hb_time_unit=configured_hb_time_unit,
)

hb_demo_data_handler = HBDemoDataHandler()
data_editor = DataEditor(
    settings=EditorSettings(
        starting_table="skjemadata",
        form_data_table="skjemadata",
        form_list=[HB_DEMO_FORM],
        period_col="iso_periode",
        ident_col="ident",
        refnr_col="refnr",
        form_name_col="skjema",
        field_name_col="variabel",
        field_value_col="verdi",
    ),
    data_handler=hb_demo_data_handler,
    inforow={
        "orgnr": {"source": "variableselector", "variable_name": "ident"},
        "skjema": {
            "source": "variableselector",
            "variable_name": "altinnskjema",
        },
    },
    sidebar=[HBDemoSaveEditSidebar(hb_demo_data_handler)],
    dataview=[
        DataViewCustom(
            applies_to_forms=[HB_DEMO_FORM],
            applies_to_tables=["skjemadata"],
            layout=[
                {
                    "type": "row",
                    "children": [
                        {
                            "type": "col",
                            "children": [
                                {
                                    "type": "microlayout",
                                    "label": "Demo-data: Areal ny eng",
                                    "field_name_col": "variabel",
                                    "field_value_col": "verdi",
                                    "inputs": ["refnr", "periode"],
                                    "layout": [
                                        {
                                            "type": "header",
                                            "label": "HB demo-verdi",
                                            "size": "md",
                                        },
                                        {
                                            "type": "input",
                                            "label": "Areal ny eng (dekar) - demo-data",
                                            "id": "hb_demo_value",
                                            "variable": HB_DEMO_FIELD_PATH,
                                        },
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        )
    ],
)
data_editor.icon = DashIconify(icon="feather:edit-2", width=24)

app.layout = main_layout(
    window_list=[],
    tab_list=[hb_method, data_editor],
    default_values={
        "measure": HB_DEMO_VARIABLE,
        "periode": HB_DEMO_PERIODS[1],
        "ident": HB_DEMO_UNIT_IDS[-1],
        "altinnskjema": HB_DEMO_FORM,
        "refnr": f"hb-demo-{HB_DEMO_UNIT_IDS[-1]}-{HB_DEMO_PERIODS[1]}",
    },
)


@callback(
    VariableSelector.get_refnr(Output),
    VariableSelector.get_ident(Input),
    VariableSelector.get_timevar(Input),
    VariableSelector.get_input("altinnskjema")[0],
    prevent_initial_call=True,
)
def update_hb_demo_reference_number(
    ident: str | None, period: str | None, form: str | None
) -> str | None:
    """Keep the editor's submission reference in sync with its selected context."""
    hb_demo_data_handler.pending_edit = None
    set_props(HB_DEMO_SAVE_BUTTON_ID, {"disabled": True})
    if not ident or not period or not form:
        return None

    with get_connection() as connection:
        submission = connection.con.execute(
            """
            SELECT refnr
            FROM skjemamottak
            WHERE ident = ? AND iso_periode = ? AND skjema = ? AND aktiv = 1
            ORDER BY dato_mottatt DESC, refnr
            LIMIT 1
            """,
            (ident, period, form),
        ).fetchone()
    return str(submission[0]) if submission is not None else None


def _configure_hb_demo_graph() -> None:
    graph = next(
        (
            component
            for component in _walk_components(app.layout)
            if isinstance(component, dcc.Graph)
            and str(component.id).endswith("-hb_result_graph")
        ),
        None,
    )
    if graph is None:
        raise RuntimeError("The HB result graph was not found in the demo layout.")
    graph.responsive = True

    style = """
<style>
.tab-implementation > * { width: 100%; min-width: 0; }
[id$="-hb_result_graph"] { width: 100% !important; height: 700px !important; }
</style>
"""
    if "</head>" not in app.index_string:
        raise RuntimeError("The Dash index template does not contain a head element.")
    app.index_string = app.index_string.replace("</head>", f"{style}</head>", 1)


_configure_hb_demo_graph()

if __name__ == "__main__":
    try:
        app.run(
            debug=False,
            port=PORT,
            jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
            jupyter_mode="tab",
            threaded=False,
        )
    finally:
        _demo_database_backend.disconnect()
