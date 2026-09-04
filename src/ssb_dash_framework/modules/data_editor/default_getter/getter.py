import logging
from typing import Any

import ibis.selectors as s
import pandas as pd
import tzlocal
from ibis import _
from pandas import Series

from ....utils.config_tools.connection import get_connection
from ..meta import FetcherMeta
from ..modules.inforow.info_row_model import InfoRowField
from ..modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)
from ..utils import EditorSettings
from ..modules.sidebar.meta import RefnrStatus
from .form_cache import FormGetterCached

logger = logging.getLogger(__name__)
local_tz = tzlocal.get_localzone()


class StandardDataHandler(FetcherMeta):

    def __init__(self) -> None:
        # self.settings = settings
        self.cache = FormGetterCached()
        super().__init__()

    def get_field(
        self, setting: EditorSettings, container: FieldCallbackContainer, inputs: list
    ):
        refnr = inputs[0]

        t = self.cache.get_form(refnr, setting)
        filters = [
            t[setting.refnr_col] == refnr,
            t[setting.field_name_col] == container.settings.variable,
        ]

        res: Series | Any = t.filter(filters).select(setting.field_value_col).execute()
        logger.debug(f"Returning:\n{res}")

        if res.empty:
            return None
        if len(res) > 1:  # catch potential duplicates
            logger.error(
                f"Multiple rows returned for {container.settings.variable}, refnr={refnr}. Using first row."
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

    def get_timeseries(
        self,
        settings: EditorSettings,
        variable: str | list[str],
        refnr: str,
        ident: str,
        periods: list[str],
    ):

        with get_connection(necessary_tables=[settings.form_data_table]) as conn:
            t = conn.table(settings.form_data_table)
            temp_filter = t.filter(
                t[settings.ident_col] == ident,
                t[settings.period_col].isin(periods),  # pyright: ignore
            ).select(
                settings.period_col, settings.field_value_col, settings.field_name_col
            )

            if isinstance(variable, list):
                temp_filter = temp_filter.filter(
                    t[settings.field_name_col].isin(variable)  # pyright: ignore
                )
            else:
                temp_filter = temp_filter.filter(t[settings.field_name_col] == variable)

            data = temp_filter.pivot_wider(
                id_cols=settings.period_col,
                names_from=settings.field_name_col,
                values_from=settings.field_value_col,
            ).execute()
        return data.to_dict(orient="records")

    def get_dynamic_list(
        self,
        settings: EditorSettings,
        wildcard: str,
        refnr: str,
    ) -> list[dict]:
        with get_connection(necessary_tables=[settings.form_data_table]) as conn:
            t = conn.table(settings.form_data_table)
            temp_filter = t.filter(
                t[settings.refnr_col] == refnr,
                # t["feltnavn"] == "NyEngAnnetGjodsID",
                t[settings.field_name_col].ilike(wildcard),
            )  # .pivot_wider(id_cols="indeks", names_from="feltnavn", values_from="verdi")

            data = temp_filter.execute()
            fieldname_parent = f"{settings.field_name_col}_parent"
            data[fieldname_parent] = data[settings.field_name_col].str.rsplit("/", n=1)
            data[fieldname_parent] = data[fieldname_parent].str[0]
            complete_data = data.pivot_table(
                settings.field_value_col,
                index=[fieldname_parent],
                columns="feltnavn",
                aggfunc=", ".join,
            ).reset_index()
        return complete_data.to_dict(orient="records")

    def update_form_active_status(self, refnr: str, value: bool) -> None:
        pass

    def update_form_reception_comment(self, refnr: str, comment: str) -> None:
        pass

    def update_form_status(self, refnr: str, status_code: Any) -> None:
        pass