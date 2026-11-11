"""The default MacroModule data handler for the Altinn data model."""

import logging
from typing import Any

import pandas as pd

from ...utils.config_tools.connection import get_connection
from .data_handler import MacroModuleDataHandler

logger = logging.getLogger(__name__)

CodelistSpec = list[str] | dict[str, Any]


class AltinnMacroModuleDataHandler(MacroModuleDataHandler):
    """Feeds a MacroModule from the Altinn data model (skjemamottak, skjemadata, enhetsinfo).

    Only active submissions of one form are used. If a unit has several active
    submissions in a period, the most recently received one is kept.

    Value variables are numeric `skjemadata` fields matched on `feltnavn`. By default an
    observation is a unit, and a field that occurs in several repeating group instances
    is summed. With `repeating_group`, each top-level instance of that group (e.g.
    `/NyEngSpredUtsGroup/9`) is an observation, and values in nested groups are summed
    into it. Instances are matched across periods on their path, so a form that
    renumbers instances shows them as new and gone.

    Grouping variables are read from `enhetsinfo.variabel`, and otherwise from
    `skjemadata.feltnavn`; in instance mode, from fields inside the instance. The unit
    name comes from `enhetsinfo` (`enhetsNavn`).
    """

    def __init__(
        self,
        skjema: str,
        value_variables: dict[str, str] | list[str],
        grouping_variables: list[str],
        codelists: dict[str, CodelistSpec] | None = None,
        repeating_group: str | None = None,
        exclude_instances: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the handler.

        Args:
            skjema: The form, e.g. "RA-0745".
            value_variables: `feltnavn` of the numeric fields to aggregate, as a list or
                as {feltnavn: label}.
            grouping_variables: Names of the grouping variables, in display order.
            codelists: Codelist per grouping variable, as a list of codes, a
                {code: label} dict, or {"klass": classification id, "level": level} to
                fetch it from Klass for the selected period's year.
            repeating_group: Path of a top-level repeating group, e.g.
                "/NyEngSpredUtsGroup". Makes each instance of it an observation.
            exclude_instances: Drops repeating group instances where a field has one
                of the listed values, e.g. {"NyEngSpredUtsID": ["TOTAL_ROW"]}.

        Raises:
            ValueError: If a codelist is given for an undeclared grouping variable or is
                not a list or dict.
        """
        self.skjema = skjema
        self.value_variables = (
            dict(value_variables)
            if isinstance(value_variables, dict)
            else {v: v for v in value_variables}
        )
        self.grouping_variables = list(grouping_variables)
        self.codelists = codelists or {}
        self.repeating_group = repeating_group.rstrip("/") if repeating_group else None
        self.exclude_instances = exclude_instances or {}
        for variable, spec in self.codelists.items():
            if variable not in self.grouping_variables:
                raise ValueError(
                    f"Codelist given for '{variable}', which is not a grouping variable."
                )
            if not isinstance(spec, list | dict):
                raise ValueError(
                    f"Codelist for '{variable}' must be a list or a dict, got {type(spec).__name__}."
                )

    def fetch_observations(self, period: str) -> pd.DataFrame:
        """Fetch one row per active submission (or instance) for the period.

        Args:
            period: The period, matched against `iso_periode`.

        Returns:
            Observations in the MacroModule's data model, plus `refnr` and `dato_mottatt`
            which `resolve_duplicates` uses.
        """
        fields = [
            *self.value_variables,
            *self.grouping_variables,
            *self.exclude_instances,
        ]
        with get_connection() as conn:
            mottak = conn.table("skjemamottak")
            mottak = mottak.filter(
                (mottak.skjema == self.skjema)
                & (mottak.iso_periode == period)
                & mottak.aktiv
            )
            data = conn.table("skjemadata")
            data = data.filter(
                (data.skjema == self.skjema)
                & (data.iso_periode == period)
                & data.feltnavn.isin(fields)
                & data.refnr.isin(mottak.refnr)
            )
            if self.repeating_group:
                data = data.filter(data.feltsti.like(f"{self.repeating_group}/%"))
            info = conn.table("enhetsinfo")
            info = info.filter(
                (info.iso_periode == period)
                & info.variabel.isin([*self.grouping_variables, "enhetsNavn"])
                & info.ident.isin(mottak.ident)
            )
            submissions = mottak.select("ident", "refnr", "dato_mottatt").to_pandas()
            answers = data.select("refnr", "feltsti", "feltnavn", "verdi").to_pandas()
            unit_info = info.select("ident", "variabel", "verdi").to_pandas()
        return self._to_observations(submissions, answers, unit_info, period)

    def resolve_duplicates(self, data: pd.DataFrame, period: str) -> pd.DataFrame:
        """Keep only the most recently received active submission per unit.

        This overrides the base class hook, which is the intended way to resolve
        duplicates in a data handler.

        Args:
            data: Observations from `fetch_observations`.
            period: The period the observations belong to.

        Returns:
            The observations belonging to each unit's latest active submission.
        """
        ordered = data.sort_values("dato_mottatt", na_position="first")
        latest = ordered.groupby(self.ident_column)["refnr"].last()
        kept = data[data["refnr"] == data[self.ident_column].map(latest)]
        if len(kept) < len(data):
            logger.debug(
                f"{self.skjema} {period}: ignored {len(data) - len(kept)} observation(s) from older active submissions."
            )
        return kept

    def get_codelists(self, period: str) -> dict[str, dict[str, str]]:
        """Return the configured codelists, fetching Klass codelists for the period's year.

        Args:
            period: The selected period. Klass codelists are valid on 31 December of its year.

        Returns:
            {grouping variable: {code: label}}.
        """
        return {
            variable: _codelist(spec, period)
            for variable, spec in self.codelists.items()
        }

    def last_updated(self, period: str) -> str | None:
        """Return when the latest active submission for the period was received.

        Args:
            period: The selected period.

        Returns:
            The receipt time, or None if there are no active submissions.
        """
        with get_connection() as conn:
            mottak = conn.table("skjemamottak")
            latest = (
                mottak.filter(
                    (mottak.skjema == self.skjema)
                    & (mottak.iso_periode == period)
                    & mottak.aktiv
                )
                .dato_mottatt.max()
                .to_pandas()
            )
        return None if pd.isna(latest) else str(latest)[:19]

    def _to_observations(
        self,
        submissions: pd.DataFrame,
        answers: pd.DataFrame,
        unit_info: pd.DataFrame,
        period: str,
    ) -> pd.DataFrame:
        """Pivot the long Altinn data to one row per submission (or instance)."""
        answers = self._drop_excluded(answers)
        key = ["refnr"]
        if self.repeating_group:
            start = len(self.repeating_group) + 1
            answers = answers.assign(
                **{
                    self.instance_column: self.repeating_group
                    + "/"
                    + answers["feltsti"].str.slice(start).str.split("/").str[0]
                }
            )
            key.append(self.instance_column)
            base = answers[key].drop_duplicates().merge(submissions, on="refnr")
        else:
            base = submissions

        values = answers[answers["feltnavn"].isin(self.value_variables)]
        text = (
            values["verdi"]
            .astype(object)
            .where(values["verdi"].astype(str).str.strip() != "")
        )
        numbers = pd.to_numeric(text, errors="coerce")
        invalid = numbers.isna() & text.notna()
        if invalid.any():
            example = values[invalid].iloc[0]
            raise ValueError(
                f"{self.skjema} {period}: {int(invalid.sum())} non-numeric value(s) in value "
                f"variables, e.g. {example['feltnavn']}='{example['verdi']}' ({example['feltsti']})."
            )
        sums = (
            values.assign(verdi=numbers)
            .groupby([*key, "feltnavn"])["verdi"]
            .sum()
            .unstack("feltnavn")
            .reindex(columns=list(self.value_variables))
        )
        codes = (
            answers[answers["feltnavn"].isin(self.grouping_variables)]
            .sort_values("feltsti")
            .groupby([*key, "feltnavn"])["verdi"]
            .first()
            .unstack("feltnavn")
            .reindex(columns=self.grouping_variables)
        )
        info = (
            unit_info.groupby(["ident", "variabel"])["verdi"]
            .first()
            .unstack("variabel")
            .reindex(columns=[*self.grouping_variables, "enhetsNavn"])
        )
        result = (
            base.merge(sums, on=key, how="left")
            .merge(codes, on=key, how="left")
            .merge(info, on="ident", how="left", suffixes=("_skjema", ""))
        )
        for variable in self.grouping_variables:
            result[variable] = result[variable].fillna(result.pop(f"{variable}_skjema"))
        result = result.rename(
            columns={"ident": self.ident_column, "enhetsNavn": self.name_column}
        )
        result[list(self.value_variables)] = (
            result[list(self.value_variables)].astype("float64").fillna(0)
        )
        text_columns = [*self.grouping_variables, self.name_column]
        result[text_columns] = result[text_columns].astype(object)
        result = result.where(result.notna(), None)
        return result.reset_index(drop=True)

    def _drop_excluded(self, answers: pd.DataFrame) -> pd.DataFrame:
        """Drop every answer inside a repeating group instance marked by `exclude_instances`."""
        if not self.exclude_instances or answers.empty:
            return answers
        marked = pd.Series(False, index=answers.index)
        for field, values in self.exclude_instances.items():
            marked |= (answers["feltnavn"] == field) & answers["verdi"].isin(values)
        parents = answers.loc[marked, "feltsti"].str.rsplit("/", n=1).str[0]
        refnrs = answers.loc[marked, "refnr"]
        dropped = pd.Series(False, index=answers.index)
        for depth in parents.str.count("/").unique():
            at_depth = parents.str.count("/") == depth
            excluded = set(zip(refnrs[at_depth], parents[at_depth], strict=True))
            prefix = answers["feltsti"].str.split("/").str[: depth + 1].str.join("/")
            dropped |= pd.Series(
                [
                    pair in excluded
                    for pair in zip(answers["refnr"], prefix, strict=True)
                ],
                index=answers.index,
            )
        return answers[~dropped]


def _codelist(spec: CodelistSpec, period: str) -> dict[str, str]:
    """Turn a codelist configuration into {code: label}."""
    if isinstance(spec, list):
        return {str(code): str(code) for code in spec}
    if "klass" in spec:
        from klass import KlassClassification

        codes = (
            KlassClassification(spec["klass"])
            .get_codes(f"{period[:4]}-12-31", select_level=spec.get("level"))
            .data
        )
        return dict(
            zip(codes["code"].astype(str), codes["name"].astype(str), strict=True)
        )
    return {str(code): str(label) for code, label in spec.items()}
