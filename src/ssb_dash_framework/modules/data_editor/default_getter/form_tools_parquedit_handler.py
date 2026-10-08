import logging
from typing import Any, Literal

import pandas as pd
import tzlocal
from ibis import _

from ssb_parquedit import ParquEdit

from ..modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)
from .getter import StandardDataHandler
from ..utils import EditorSettings

logger = logging.getLogger(__name__)
local_tz = tzlocal.get_localzone()


class AltinnFormParqueditHandler(StandardDataHandler):

    def __init__(self, conn: ParquEdit) -> None:
        self.conn = conn
        super().__init__()

    def update_form_active_status(self, refnr: str, value: bool) -> None:
        formdata: pd.DataFrame = self.conn.view(
            "skjemamottak", f"refnr = '{refnr}'", limit=1
        )
        if formdata.shape[1] != 0:
            rowid = formdata.iloc[0, :]["rowid"]
            self.conn.edit(
                "skjemamottak",
                rowid,
                {"aktiv": value},
                change_event_reason="REVIEW",
                change_comment="Status på skjema endret manuelt",
            )

    def update_form_reception_comment(self, refnr: str, comment: str) -> None:
        formdata: pd.DataFrame = self.conn.view(
            "skjemamottak", f"refnr = '{refnr}'", limit=1
        )
        if formdata.shape[1] != 0:
            rowid = formdata.iloc[0, :]["rowid"]
            self.conn.edit(
                "skjemamottak",
                rowid,
                {"kommentar": comment},
                change_event_reason="REVIEW",
                change_comment="Status på skjema endret manuelt",
            )

    def update_form_status(
        self,
        refnr: str,
        status_code: Literal["Under behandling", "Ferdig", "Ubehandlet"],
    ) -> None:
        formdata: pd.DataFrame = self.conn.view(
            "skjemamottak", f"refnr = '{refnr}'", limit=1
        )

        if formdata.shape[1] != 0:
            rowid = formdata.iloc[0, :]["rowid"]
            self.conn.edit(
                "skjemamottak",
                rowid,
                {"status": status_code},
                change_event_reason="REVIEW",
                change_comment="Status på skjema endret manuelt",
            )

    def update_field_value(
        self,
        refnr: str,
        skjema: str | None,
        ident: str,
        period: str | None,
        value: Any,
        old_value: Any,
        settings: EditorSettings,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
        editing_code: str | None,
    ) -> Any:
        if container.settings.type == "checklist":
            value = ",".join(value)
        if editing_code is None:
            raise ValueError("editing_code cannot be None")
        settings.field_name_col
        formdata: pd.DataFrame = self.conn.view(
            "skjemadata",
            f"{settings.refnr_col} = '{refnr}' AND {settings.period_col} = '{period}' AND {settings.field_name_col} = '{container.settings.variable}'",
            limit=1,
        )

        if formdata.shape[1] != 0:
            rowid = formdata.iloc[0, :]["rowid"]
            self.conn.edit(
                "skjemadata",
                rowid,
                {settings.field_value_col: value},
                change_event_reason=editing_code,
                change_comment="Status på skjema endret manuelt",
            )
