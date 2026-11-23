from typing import cast
from typing import get_type_hints

import pandas as pd
import pytest

from ssb_dash_framework.modules.hb import HBDataHandlerMeta
from ssb_dash_framework.modules.hb import HBDataResult
from ssb_dash_framework.modules.hb import HBDataWarning
from ssb_dash_framework.modules.hb import validate_hb_dataframe
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


def valid_hb_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1"],
            "period": ["2024", "2023"],
            "value": [12.5, 10.0],
        }
    )


def test_validate_hb_dataframe_returns_the_input_dataframe() -> None:
    hb_input_dataframe = valid_hb_dataframe()

    validated_dataframe = validate_hb_dataframe(hb_input_dataframe)

    assert validated_dataframe is hb_input_dataframe


def test_hb_data_result_contains_validated_dataframe_and_warnings() -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_warning = HBDataWarning(
        message="Multiple answers matched the configured field.",
        unit_id="unit-1",
        period="2024",
    )

    hb_data_result = HBDataResult(
        hb_dataframe=validate_hb_dataframe(hb_input_dataframe),
        hb_warnings=(hb_warning,),
    )

    assert hb_data_result.hb_dataframe is hb_input_dataframe
    assert hb_data_result.hb_warnings == (hb_warning,)


def test_hb_data_result_defaults_to_no_warnings() -> None:
    hb_data_result = HBDataResult(hb_dataframe=valid_hb_dataframe())

    assert hb_data_result.hb_warnings == ()


def test_hb_data_handler_meta_returns_hb_data_result() -> None:
    return_type = get_type_hints(HBDataHandlerMeta.get_hb_dataframe)["return"]

    assert return_type is HBDataResult


@pytest.mark.parametrize(
    ("column_name", "column_value"),
    [
        ("unit_id", [1, 2]),
        ("period", [2024, 2023]),
        ("value", ["12.5", "10.0"]),
    ],
)
def test_validate_hb_dataframe_rejects_invalid_required_column_types(
    column_name: str, column_value: list[object]
) -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe[column_name] = column_value

    with pytest.raises(TypeError, match="HB column"):
        validate_hb_dataframe(hb_input_dataframe)


@pytest.mark.parametrize("missing_column", ["unit_id", "period", "value"])
def test_validate_hb_dataframe_rejects_missing_required_columns(
    missing_column: str,
) -> None:
    hb_input_dataframe = valid_hb_dataframe().drop(columns=missing_column)

    with pytest.raises(ValueError, match=f"missing required columns: {missing_column}"):
        validate_hb_dataframe(hb_input_dataframe)


def test_validate_hb_dataframe_rejects_duplicate_unit_period_rows() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1"],
            "period": ["2024", "2024"],
            "value": [12.5, 10.0],
        }
    )

    with pytest.raises(ValueError, match="at most one row"):
        validate_hb_dataframe(hb_input_dataframe)


@pytest.mark.parametrize(
    ("frequency", "period"),
    [
        (None, "2024-Q5"),
        (None, "2024-00"),
        (None, "2024-13"),
        (None, "24"),
        (None, "2024-3"),
        (None, "2024-W1"),
        (None, "2024-W00"),
        (None, "2024-W54"),
        (None, "2024-02-30"),
        (None, "0000"),
        (TimeUnitType.YEAR, "2024-Q1"),
        (TimeUnitType.HALF_YEAR, "2024-Q1"),
        (TimeUnitType.QUARTER, "2024-1"),
        (TimeUnitType.MONTH, "2024-01-01"),
        (TimeUnitType.WEEK, "2024-01-01"),
        (TimeUnitType.DAY, "2024-W01"),
    ],
)
def test_validate_hb_dataframe_rejects_noncanonical_periods(
    frequency: TimeUnitType | None,
    period: str,
) -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "period"] = period

    with pytest.raises(ValueError, match="canonical"):
        validate_hb_dataframe(
            hb_input_dataframe,
            configured_hb_frequency=frequency,
        )


@pytest.mark.parametrize(
    ("frequency", "periods"),
    [
        (TimeUnitType.YEAR, ["2024", "2023"]),
        (TimeUnitType.HALF_YEAR, ["2024-1", "2024-2"]),
        (TimeUnitType.QUARTER, ["2024-Q1", "2024-Q2"]),
        (TimeUnitType.MONTH, ["2024-01", "2024-02"]),
        (TimeUnitType.WEEK, ["2024-W01", "2024-W02"]),
        (TimeUnitType.DAY, ["2024-01-01", "2024-01-02"]),
    ],
)
def test_validate_hb_dataframe_accepts_all_timeunit_frequencies(
    frequency: TimeUnitType,
    periods: list[str],
) -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe["period"] = periods

    validated_dataframe = validate_hb_dataframe(
        hb_input_dataframe,
        configured_hb_frequency=frequency,
    )

    assert validated_dataframe is hb_input_dataframe


@pytest.mark.parametrize(
    "period",
    [
        "2024",
        "2024-1",
        "2024-Q1",
        "2024-01",
        "2024-W01",
        "2024-01-01",
    ],
)
def test_validate_hb_dataframe_accepts_canonical_periods_without_frequency(
    period: str,
) -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "period"] = period

    validate_hb_dataframe(hb_input_dataframe)


def test_validate_hb_dataframe_accepts_week_53_only_when_valid_for_week_year() -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe["period"] = ["2020-W53", "2020-W52"]

    validated_dataframe = validate_hb_dataframe(
        hb_input_dataframe,
        configured_hb_frequency=TimeUnitType.WEEK,
    )

    assert validated_dataframe is hb_input_dataframe


def test_validate_hb_dataframe_rejects_week_53_for_52_week_year() -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "period"] = "2024-W53"

    with pytest.raises(ValueError, match="configured frequency WEEK"):
        validate_hb_dataframe(
            hb_input_dataframe,
            configured_hb_frequency=TimeUnitType.WEEK,
        )


def test_validate_hb_dataframe_rejects_invalid_configured_frequency_type() -> None:
    with pytest.raises(
        TypeError, match="configured_hb_frequency must be a TimeUnitType"
    ):
        validate_hb_dataframe(
            valid_hb_dataframe(),
            configured_hb_frequency=cast(TimeUnitType, "YEAR"),
        )


def test_validate_hb_dataframe_allows_missing_numeric_values() -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "value"] = None

    validated_dataframe = validate_hb_dataframe(hb_input_dataframe)

    assert pd.isna(validated_dataframe.loc[0, "value"])


def test_hb_data_handler_meta_requires_get_hb_dataframe_implementation() -> None:
    with pytest.raises(TypeError, match="abstract"):
        HBDataHandlerMeta()
