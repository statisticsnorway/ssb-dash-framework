"""Retrieve configured Altinn candidate records for the HB module."""

from collections.abc import Mapping

import pandas as pd

from ssb_dash_framework.utils.core_query_functions import (
    active_no_duplicates_refnr_list,
)
from ssb_dash_framework.utils.config_tools.connection import get_connection


class AltinnHBCandidateRetriever:
    """Read candidate Altinn answers without selecting submissions or normalizing values."""

    def __init__(
        self,
        *,
        configured_hb_form: str,
        hb_variable_to_feltsti: Mapping[str, str],
    ) -> None:
        """Configure the source form and exact field path for each HB variable."""
        if not isinstance(configured_hb_form, str) or not configured_hb_form.strip():
            raise ValueError("configured_hb_form must be a non-empty string.")
        if not hb_variable_to_feltsti:
            raise ValueError("hb_variable_to_feltsti must not be empty.")

        validated_field_mapping: dict[str, str] = {}
        for hb_variable, feltsti in hb_variable_to_feltsti.items():
            if not isinstance(hb_variable, str) or not hb_variable.strip():
                raise ValueError("HB variable mapping keys must be non-empty strings.")
            if not isinstance(feltsti, str) or not feltsti.strip():
                raise ValueError(
                    f"The feltsti mapping for HB variable {hb_variable!r} "
                    "must be a non-empty string."
                )
            validated_field_mapping[hb_variable] = feltsti

        self._configured_hb_form = configured_hb_form
        self._hb_variable_to_feltsti = validated_field_mapping

    def retrieve_candidate_records(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
    ) -> pd.DataFrame:
        """Return source-keyed Altinn rows for the configured field and periods.

        Active-submission selection and conversion into the common HB DataFrame
        are intentionally left to later steps.
        """
        if (
            not isinstance(selected_hb_variable, str)
            or selected_hb_variable not in self._hb_variable_to_feltsti
        ):
            raise ValueError(
                f"No Altinn feltsti is configured for HB variable "
                f"{selected_hb_variable!r}."
            )
        if (
            not isinstance(hb_comparison_periods, tuple)
            or len(hb_comparison_periods) != 2
            or any(
                not isinstance(period, str) or not period.strip()
                for period in hb_comparison_periods
            )
            or hb_comparison_periods[0] == hb_comparison_periods[1]
        ):
            raise ValueError(
                "hb_comparison_periods must contain two distinct non-empty "
                "period strings."
            )

        selected_feltsti = self._hb_variable_to_feltsti[selected_hb_variable]

        with get_connection() as conn:
            enheter = conn.table("enheter")
            unit_period_records = enheter.filter(
                (enheter.skjema == self._configured_hb_form)
                & enheter.iso_periode.isin(hb_comparison_periods)
            ).select(
                iso_periode=enheter.iso_periode,
                skjema=enheter.skjema,
                ident=enheter.ident,
            )

            skjemamottak = conn.table("skjemamottak")
            submission_records = skjemamottak.select(
                submission_period=skjemamottak.iso_periode,
                submission_skjema=skjemamottak.skjema,
                submission_ident=skjemamottak.ident,
                refnr=skjemamottak.refnr,
            )

            unit_submission_records = unit_period_records.join(
                submission_records,
                (
                    unit_period_records.iso_periode
                    == submission_records.submission_period
                )
                & (unit_period_records.skjema == submission_records.submission_skjema)
                & (unit_period_records.ident == submission_records.submission_ident),
                how="left",
            )

            skjemadata = conn.table("skjemadata")
            selected_field_answers = skjemadata.select(
                answer_period=skjemadata.iso_periode,
                answer_skjema=skjemadata.skjema,
                answer_ident=skjemadata.ident,
                answer_refnr=skjemadata.refnr,
                feltsti=skjemadata.feltsti,
                feltnavn=skjemadata.feltnavn,
                verdi=skjemadata.verdi,
                dybde=skjemadata.dybde,
                indeks=skjemadata.indeks,
            )

            # Keep all matches; the downstream method owns missing-value treatment.
            candidate_records = unit_submission_records.join(
                selected_field_answers,
                (
                    unit_submission_records.iso_periode
                    == selected_field_answers.answer_period
                )
                & (
                    unit_submission_records.skjema
                    == selected_field_answers.answer_skjema
                )
                & (unit_submission_records.ident == selected_field_answers.answer_ident)
                & (unit_submission_records.refnr == selected_field_answers.answer_refnr)
                & (selected_field_answers.feltsti == selected_feltsti),
                how="left",
            ).select(
                unit_submission_records.iso_periode,
                unit_submission_records.skjema,
                unit_submission_records.ident,
                unit_submission_records.refnr,
                selected_field_answers.feltsti,
                selected_field_answers.feltnavn,
                selected_field_answers.verdi,
                selected_field_answers.dybde,
                selected_field_answers.indeks,
            )

            return candidate_records.to_pandas()

    def select_active_candidate_records(
        self,
        candidate_records: pd.DataFrame,
        *,
        hb_comparison_periods: tuple[str, str],
    ) -> pd.DataFrame:
        """Keep latest active candidate submissions, selecting independently by period.

        Unit-periods with no active submission are left for the separate
        missing-submission validation step.
        """
        if not isinstance(candidate_records, pd.DataFrame):
            raise TypeError("candidate_records must be a pandas DataFrame.")
        required_columns = {"iso_periode", "skjema", "ident", "refnr"}
        missing_columns = required_columns - set(candidate_records.columns)
        if missing_columns:
            missing_column_names = ", ".join(sorted(missing_columns))
            raise ValueError(
                "candidate_records is missing required columns: "
                f"{missing_column_names}."
            )
        if (
            not isinstance(hb_comparison_periods, tuple)
            or len(hb_comparison_periods) != 2
            or any(
                not isinstance(period, str) or not period.strip()
                for period in hb_comparison_periods
            )
            or hb_comparison_periods[0] == hb_comparison_periods[1]
        ):
            raise ValueError(
                "hb_comparison_periods must contain two distinct non-empty "
                "period strings."
            )

        active_refnrs_by_period: dict[str, list[str]] = {}
        with get_connection() as conn:
            for comparison_period in hb_comparison_periods:
                active_refnrs_by_period[comparison_period] = (
                    active_no_duplicates_refnr_list(
                        conn,
                        self._configured_hb_form,
                        filters={"iso_periode": comparison_period},
                    )
                )

        selected_period_records = [
            candidate_records.loc[
                (candidate_records["skjema"] == self._configured_hb_form)
                & (candidate_records["iso_periode"] == comparison_period)
                & candidate_records["refnr"].isin(active_refnrs_by_period[comparison_period])
            ]
            for comparison_period in hb_comparison_periods
        ]
        return pd.concat(selected_period_records, ignore_index=True)
