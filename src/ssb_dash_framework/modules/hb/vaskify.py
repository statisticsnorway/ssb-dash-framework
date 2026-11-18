"""Vaskify execution boundary for the HB module."""

import pandas as pd
from vaskify import Detect

from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

from .data_handler import validate_hb_dataframe
from .period_validation import is_canonical_hb_period


def run_hb_vaskify(
    hb_input_dataframe: pd.DataFrame,
    *,
    hb_comparison_periods: tuple[str, str],
    configured_hb_strata_variable: str | None = None,
) -> pd.DataFrame:
    """Run Vaskify HB against the common HB input DataFrame.

    Args:
        hb_input_dataframe: Validated common HB input data.
        hb_comparison_periods: The ordered periods to compare.
        configured_hb_strata_variable: The configured source strata variable,
            if the input includes a normalized ``strata`` column.

    Returns:
        The DataFrame returned by Vaskify's HB method.
    """
    _validate_hb_vaskify_input(
        hb_input_dataframe,
        configured_hb_strata_variable=configured_hb_strata_variable,
    )
    _validate_hb_comparison_periods(hb_input_dataframe, hb_comparison_periods)
    detector = Detect(hb_input_dataframe, id_nr="unit_id")
    hb_result = detector.hb(
        y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="strata" if configured_hb_strata_variable is not None else "",
        pu=0.5,
        pa=0.05,
        pc=20,
        percentiles=(0.25, 0.75),
        flag="flag_hb",
        output_format="wide",
        output_scope="all",
    )
    _validate_hb_vaskify_result(
        hb_result,
        hb_input_dataframe=hb_input_dataframe,
        hb_comparison_periods=hb_comparison_periods,
        require_strata=configured_hb_strata_variable is not None,
    )
    if hb_result.empty:
        raise ValueError(
            "Vaskify returned an empty HB result; no result is available."
        )
    return hb_result


def normalize_hb_result(
    hb_input_dataframe: pd.DataFrame,
    hb_vaskify_result_dataframe: pd.DataFrame,
    *,
    hb_comparison_periods: tuple[str, str],
    configured_hb_strata_variable: str | None = None,
) -> pd.DataFrame:
    """Reconcile Vaskify diagnostics with every unit in the HB input.

    Extra input columns are retained as source context. Context that is stable
    for a unit is kept in one column; context that changes between periods is
    retained in period-specific columns.
    """
    _validate_hb_vaskify_input(
        hb_input_dataframe,
        configured_hb_strata_variable=configured_hb_strata_variable,
    )
    _validate_hb_comparison_periods(hb_input_dataframe, hb_comparison_periods)
    _validate_hb_vaskify_result(
        hb_vaskify_result_dataframe,
        hb_input_dataframe=hb_input_dataframe,
        hb_comparison_periods=hb_comparison_periods,
        require_strata=configured_hb_strata_variable is not None,
    )
    if hb_vaskify_result_dataframe.empty:
        raise ValueError(
            "Vaskify returned an empty HB result; no result is available."
        )

    hb_unit_ids = hb_input_dataframe["unit_id"].drop_duplicates().tolist()
    normalized_hb_result = pd.DataFrame(
        index=pd.Index(hb_unit_ids, name="unit_id")
    )
    hb_comparison_values = hb_input_dataframe.pivot(
        index="unit_id",
        columns="period",
        values="value",
    ).reindex(index=hb_unit_ids, columns=hb_comparison_periods)
    hb_comparison_values.columns = [
        f"value_{hb_period}" for hb_period in hb_comparison_periods
    ]

    normalized_context_columns: dict[object, pd.Series] = {}
    normalized_value_column_names = {
        f"value_{hb_period}" for hb_period in hb_comparison_periods
    }
    hb_input_context_columns = [
        column_name
        for column_name in hb_input_dataframe.columns
        if column_name not in {"unit_id", "period", "value"}
    ]
    for context_column_name in hb_input_context_columns:
        context_values_by_unit = hb_input_dataframe.groupby(
            "unit_id",
            sort=False,
        )[context_column_name].nunique(dropna=False)
        if context_values_by_unit.le(1).all():
            context_by_unit = (
                hb_input_dataframe.drop_duplicates("unit_id", keep="first")
                .set_index("unit_id")[context_column_name]
                .reindex(hb_unit_ids)
            )
            context_output_columns = {
                context_column_name: context_by_unit,
            }
        else:
            context_by_period = hb_input_dataframe.pivot(
                index="unit_id",
                columns="period",
                values=context_column_name,
            ).reindex(index=hb_unit_ids, columns=hb_comparison_periods)
            context_output_columns = {
                f"{context_column_name}_{hb_period}": context_by_period[hb_period]
                for hb_period in hb_comparison_periods
            }

        for output_column_name, context_values in context_output_columns.items():
            if (
                output_column_name in normalized_context_columns
                or output_column_name in normalized_value_column_names
            ):
                raise ValueError(
                    "HB source context collides with a normalized result column: "
                    f"{output_column_name!r}."
                )
            normalized_context_columns[output_column_name] = context_values

    if normalized_context_columns:
        normalized_hb_result = normalized_hb_result.join(
            pd.DataFrame(normalized_context_columns, index=hb_unit_ids)
        )
    normalized_hb_result = normalized_hb_result.join(hb_comparison_values)

    comparison_value_columns = {
        f"value_{hb_period}" for hb_period in hb_comparison_periods
    }
    source_context_columns = set(normalized_context_columns)
    required_diagnostic_columns = {
        "lower_limit",
        "upper_limit",
        "ratio",
        "median_ratio",
        "flag_hb",
    }
    context_diagnostic_collisions = (
        source_context_columns & required_diagnostic_columns
    )
    if context_diagnostic_collisions:
        conflicting_column_names = ", ".join(
            sorted(context_diagnostic_collisions)
        )
        raise ValueError(
            "HB source context collides with Vaskify diagnostic columns: "
            f"{conflicting_column_names}."
        )
    hb_diagnostic_columns = [
        column_name
        for column_name in hb_vaskify_result_dataframe.columns
        if column_name != "unit_id"
        and column_name not in comparison_value_columns
        and column_name not in source_context_columns
    ]
    conflicting_diagnostic_columns = (
        set(hb_diagnostic_columns) & set(normalized_hb_result.columns)
    )
    if conflicting_diagnostic_columns:
        conflicting_column_names = ", ".join(
            sorted(map(str, conflicting_diagnostic_columns))
        )
        raise ValueError(
            "Vaskify diagnostics conflict with normalized HB input columns: "
            f"{conflicting_column_names}."
        )

    normalized_hb_result = normalized_hb_result.reset_index()
    return normalized_hb_result.merge(
        hb_vaskify_result_dataframe[["unit_id", *hb_diagnostic_columns]],
        on="unit_id",
        how="left",
        validate="one_to_one",
        sort=False,
    )


def _validate_hb_vaskify_result(
    hb_result: object,
    *,
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
    require_strata: bool,
) -> None:
    if not isinstance(hb_result, pd.DataFrame):
        raise TypeError("Vaskify HB result must be a pandas DataFrame.")

    required_columns = {
        "unit_id",
        f"value_{hb_comparison_periods[0]}",
        f"value_{hb_comparison_periods[1]}",
        "lower_limit",
        "upper_limit",
        "ratio",
        "median_ratio",
        "flag_hb",
    }
    if require_strata:
        required_columns.add("strata")

    missing_columns = required_columns - set(hb_result.columns)
    if missing_columns:
        missing_column_names = ", ".join(sorted(missing_columns))
        raise ValueError(
            "Vaskify HB result is missing required columns: "
            f"{missing_column_names}."
        )

    result_unit_ids = hb_result["unit_id"]
    string_unit_ids = result_unit_ids.map(
        lambda unit_id: isinstance(unit_id, str)
    ).astype(bool)
    invalid_unit_ids = result_unit_ids.isna() | ~string_unit_ids
    if invalid_unit_ids.any():
        raise TypeError(
            "Vaskify result 'unit_id' values must be non-null strings."
        )
    if result_unit_ids.duplicated().any():
        raise ValueError("Vaskify result 'unit_id' values must be unique.")

    input_unit_ids = set(hb_input_dataframe["unit_id"])
    unknown_unit_ids = set(result_unit_ids) - input_unit_ids
    if unknown_unit_ids:
        raise ValueError(
            "Vaskify result contains unit_id values not present in HB input: "
            f"{', '.join(sorted(unknown_unit_ids))}."
        )


def _validate_hb_vaskify_input(
    hb_input_dataframe: pd.DataFrame,
    *,
    configured_hb_strata_variable: str | None,
) -> None:
    validate_hb_dataframe(hb_input_dataframe)
    if configured_hb_strata_variable is not None and (
        "strata" not in hb_input_dataframe.columns
    ):
        raise ValueError(
            "HB input must contain a 'strata' column when a strata variable is configured."
        )
    if configured_hb_strata_variable is not None:
        strata_values_per_unit = hb_input_dataframe.groupby(
            "unit_id",
            sort=False,
        )["strata"].nunique(dropna=False)
        if strata_values_per_unit.gt(1).any():
            raise ValueError(
                "HB input 'strata' values must be consistent across periods "
                "for each unit when a strata variable is configured."
            )


def _validate_hb_comparison_periods(
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
) -> None:
    if not isinstance(hb_comparison_periods, tuple):
        raise TypeError("hb_comparison_periods must be a tuple.")
    if len(hb_comparison_periods) != 2:
        raise ValueError("HB comparison requires exactly two periods.")
    comparison_period_frequencies = [
        frequency
        for period in hb_comparison_periods
        for frequency in TimeUnitType
        if is_canonical_hb_period(period, frequency)
    ]
    if len(comparison_period_frequencies) != 2:
        raise ValueError("HB comparison periods must be canonical TimeUnit periods.")
    if comparison_period_frequencies[0] is not comparison_period_frequencies[1]:
        raise ValueError(
            "HB comparison periods must use the same canonical TimeUnit frequency."
        )
    if hb_comparison_periods[0] == hb_comparison_periods[1]:
        raise ValueError("HB comparison periods must be distinct.")
    if any(
        is_canonical_hb_period(period, TimeUnitType.HALF_YEAR)
        for period in hb_comparison_periods
    ):
        raise ValueError(
            "HALF_YEAR comparisons are disabled until Vaskify supports "
            "canonical half-year periods."
        )

    input_periods = hb_input_dataframe["period"].drop_duplicates().tolist()
    if len(input_periods) != 2 or not all(
        isinstance(period, str) and period in hb_comparison_periods
        for period in input_periods
    ):
        raise ValueError(
            "HB input must contain exactly the requested comparison periods."
        )
