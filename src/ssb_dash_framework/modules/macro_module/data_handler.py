"""The data handler contract for the MacroModule.

A data handler translates a storage backend's data model into the MacroModule's data
model: one row per observation, with a fixed ident column, an optional instance and
name column, one string column per grouping variable and one numeric column per value
variable.
"""

import logging
from abc import abstractmethod
from typing import ClassVar

import pandas as pd
from pandas.api.types import is_bool_dtype
from pandas.api.types import is_numeric_dtype
from pandas.api.types import is_string_dtype

from ...config.models import YamlLoadable
from ...utils.alert_handler import AlertHandler

logger = logging.getLogger(__name__)


class MacroModuleDataHandler(YamlLoadable):
    """Base class for data handlers that feed a MacroModule.

    Subclasses set `value_variables` and `grouping_variables` and implement
    `fetch_observations`. The MacroModule only calls `get_observations`, which fetches,
    resolves duplicates and validates, so a handler can never skip validation.

    Attributes:
        ident_column: Name of the column identifying the unit.
        instance_column: Name of the optional column identifying a repeating group
            instance. Together with `ident_column` it forms the observation key.
        name_column: Name of the optional column shown as the unit name.
        value_variables: Numeric variables to aggregate, as {name: label} in display order.
        grouping_variables: Categorical variables observations can be grouped by, in display order.
    """

    ident_column: ClassVar[str] = "ident"
    instance_column: ClassVar[str] = "instance"
    name_column: ClassVar[str] = "name"

    value_variables: dict[str, str]
    grouping_variables: list[str]

    @abstractmethod
    def fetch_observations(self, period: str) -> pd.DataFrame:
        """Fetch the observations for one period in the MacroModule's data model.

        Build the query in ibis and call `.to_pandas()` inside the handler's own
        `with get_connection()` block, so heavy filtering and pivoting runs in the database.

        Args:
            period: The period, formatted like the variable selector's time unit.

        Returns:
            One row per observation: the ident column, optionally the instance and name
            columns, one string column per grouping variable and one numeric column per
            value variable.
        """
        ...

    def get_codelists(self, period: str) -> dict[str, dict[str, str]]:
        """Return the codelists for the grouping variables, if the handler has any.

        The MacroModule asks for the selected period's codelists and uses them for both
        the selected and the comparison period. Grouping variables without a codelist
        fall back to the codes found in the data, sorted.

        Args:
            period: The selected period.

        Returns:
            {grouping variable: {code: label}}, with codes in display order.
        """
        return {}

    def last_updated(self, period: str) -> str | None:
        """Return a human readable time for when the data was last updated, if known.

        Args:
            period: The selected period.

        Returns:
            The time as text, or None if unknown.
        """
        return None

    def key_columns(self, data: pd.DataFrame) -> list[str]:
        """Return the columns that identify an observation in `data`.

        Args:
            data: Observations in the MacroModule's data model.

        Returns:
            The ident column, plus the instance column if `data` has one.
        """
        if self.instance_column in data.columns:
            return [self.ident_column, self.instance_column]
        return [self.ident_column]

    def resolve_duplicates(self, data: pd.DataFrame, period: str) -> pd.DataFrame:
        """Resolve observations that share a key, before the data is validated.

        Override this method to resolve duplicates; it is the intended extension point.
        For example, `AltinnMacroModuleDataHandler` keeps the most recently received
        active submission per unit. The default only warns the user through the
        AlertHandler and returns the data unchanged, so `validate` then raises.

        Args:
            data: Observations as returned by `fetch_observations`.
            period: The period the observations belong to.

        Returns:
            The observations, with at most one row per key.
        """
        key = self.key_columns(data)
        if set(key) <= set(data.columns):
            duplicates = int(data.duplicated(key).sum())
            if duplicates:
                AlertHandler.warning(
                    f"{type(self).__name__}: {duplicates} duplicate observation(s) for {key} "
                    f"in period {period}. The data handler must resolve duplicates."
                )
        return data

    def validate(self, data: pd.DataFrame, period: str) -> None:
        """Check that `data` follows the MacroModule's data model.

        Content problems, such as codes missing from a codelist, are not errors here;
        the MacroModule shows them as an "Ukjent" group.

        Args:
            data: Observations after duplicates have been resolved.
            period: The period the observations belong to.

        Raises:
            TypeError: If `data` is not a pandas DataFrame.
            ValueError: If a column is missing or has the wrong type, or if two
                observations share a key.
        """
        where = f"{type(self).__name__} (period {period})"
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                f"{where}: fetch_observations must return a pandas DataFrame, got {type(data).__name__}."
            )
        optional = [self.instance_column, self.name_column]
        text_columns = [
            self.ident_column,
            *self.grouping_variables,
            *(c for c in optional if c in data.columns),
        ]
        missing = [
            c for c in [*text_columns, *self.value_variables] if c not in data.columns
        ]
        if missing:
            raise ValueError(f"{where}: missing column(s) {missing}.")
        for column in text_columns:
            if not _is_text(data[column]):
                raise ValueError(
                    f"{where}: column '{column}' must contain strings, got {data[column].dtype}."
                )
        for column in self.value_variables:
            if not is_numeric_dtype(data[column]) or is_bool_dtype(data[column]):
                raise ValueError(
                    f"{where}: value column '{column}' must be numeric, got {data[column].dtype}."
                )
        key = self.key_columns(data)
        duplicated = data[data.duplicated(key, keep=False)]
        if not duplicated.empty:
            examples = duplicated[key].drop_duplicates().head(5).to_dict("records")
            raise ValueError(
                f"{where}: {len(duplicated)} rows share a key {key}, e.g. {examples}. "
                "Resolve duplicates by overriding resolve_duplicates."
            )

    def get_observations(self, period: str) -> pd.DataFrame:
        """Fetch, resolve duplicates and validate the observations for one period.

        This is the only method the MacroModule calls to get data. Do not override it.

        Args:
            period: The period to fetch.

        Returns:
            Validated observations in the MacroModule's data model.
        """
        data = self.fetch_observations(period)
        if isinstance(data, pd.DataFrame):
            data = self.resolve_duplicates(data, period)
        self.validate(data, period)
        logger.debug(f"{type(self).__name__}: {len(data)} observations for {period}.")
        return data


def _is_text(series: pd.Series) -> bool:
    """Return True if every non-null value in `series` is a string."""
    if is_string_dtype(series.dtype) and series.dtype != object:
        return True
    return bool(series.dropna().map(lambda value: isinstance(value, str)).all())
