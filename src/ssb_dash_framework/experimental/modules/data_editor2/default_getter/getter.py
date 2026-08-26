from typing import Any
import pandas as pd
from pandas import Series

import logging


import tzlocal


import ibis.selectors as s
from ibis import _

from ssb_dash_framework import get_connection

from ..meta import FetcherMeta
from ..utils import (
    EditorSettings,
    RefnrStatus,
)
from ..modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)
from ..modules.info_row_model import (
    InfoRowField,
)

from .form_cache import FormGetterCached, CallbackSettings

logger = logging.getLogger(__name__)
local_tz = tzlocal.get_localzone()


class StandardDataHandler(FetcherMeta):

    def __init__(self) -> None:
        # self.settings = settings
        self.cache = FormGetterCached()
        super().__init__()

    def get_field(
        self, setting: CallbackSettings, container: FieldCallbackContainer, inputs: list
    ):
        refnr = inputs[0]
        # print(refnr, setting, container)
        t = self.cache.get_form(refnr, setting)
        filters = [
            t[setting.form_reference_number_column] == refnr,
            t[setting.formdata_fieldname_column] == container.settings.field_path,
        ]

        res: Series | Any = (
            t.filter(filters).select(setting.formdata_field_value_column_name).execute()
        )
        logger.debug(f"Returning:\n{res}")

        if res.empty:
            return None
        if len(res) > 1:  # catch potential duplicates
            logger.error(
                f"Multiple rows returned for {container.settings.field_path}, refnr={refnr}. Using first row."
            )
        return res.iloc[0, 0]

    def get_comment(self, refnr: str) -> str | None:
        with get_connection() as conn:
            s = conn.table("skjemamottak")
            comment = (
                s.filter(_.refnr == refnr)
                .select("kommentar")
                .limit(1)
                .to_pandas()["kommentar"]
            )[0]
        return comment  # pyright: ignore

    def get_history(self, refnr: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_form_status(self, refnr: str) -> RefnrStatus | None:
        # print("hei", refnr)
        with get_connection() as conn:
            t = conn.table("skjemamottak")
            data = t.filter(_.refnr == refnr).to_pandas()

        if data.empty:
            return None

        row = data.iloc[0]
        # print(row)
        status = "Ubehandlet"
        if row["editert"] == "ferdig":
            status = "Ferdig"
        if row["editert"] == "under editering":
            status = "Under arbeid"
        return RefnrStatus(active=row["aktiv"], status=status)

    def get_refnrs_by_period_ident(
        self, settings: EditorSettings, ident: str, period: str
    ) -> pd.DataFrame:

        with get_connection() as conn:
            t = conn.table("skjemamottak")
            data = (
                t.filter(
                    t[settings.ident_col] == ident,
                    t[settings.period_col] == period,
                )
                .order_by(_.dato_mottatt.desc())
                .select(
                    "skjema",
                    "dato_mottatt",
                    "refnr",
                    s.matches(r"^(editert|status)$"),
                    "kommentar",
                    "aktiv",
                )
                .to_pandas()
            )
            # data["dato_mottatt"] = (
            # data["dato_mottatt"]
            # .dt.tz_convert(local_tz)
            # .dt.tz_localize(None)
            # .dt.strftime("%Y-%m-%d %H:%M:%S")
            # )
        # print(data)
        return data

    def get_info_row_fields(
        self,
        settings: EditorSettings,
        ident: str,
        period: str,
        fields: list[InfoRowField],
    ) -> dict[str, str | int | bool | float | None]:
        info_values = {}
        with get_connection(necessary_tables=["enhetsinfo"]) as conn:
            for info_var in fields:
                logger.debug(f"Getting data for:\n{info_var}")
                t = conn.table(info_var.source)
                t = t.filter(
                    t[settings.ident_col] == ident, t[settings.period_col] == period
                )
                data = (
                    t.filter(_.variabel == info_var.source_variable_name)
                    .limit(1)
                    .execute()
                )
                logger.debug(f"Info values from database:\n{data}")
                value = data["verdi"].item()
                info_values[info_var.name] = value
        return info_values

    def get_timeseries(self, variable: str, refnr: str, ident: str, periods: list[str]):
        print("fired", variable)
        with get_connection(necessary_tables=["skjemadata"]) as conn:
            t = conn.table("skjemadata")
            data = (
                t.filter(
                    t["ident"] == ident,
                    t["iso_period"].isin(periods),
                    t["feltsti"] == variable
                ).select("iso_period", "verdi").execute()
            )
        return data.to_dict(orient="records")
