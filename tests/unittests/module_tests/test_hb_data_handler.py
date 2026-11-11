import pandas as pd
import pytest

from ssb_dash_framework.modules.hb import HBDataHandlerMeta
from ssb_dash_framework.modules.hb import validate_hb_dataframe


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


@pytest.mark.parametrize("period", ["2024-Q5", "2024-00", "2024-13", "24", "2024-W1"])
def test_validate_hb_dataframe_rejects_noncanonical_periods(period: str) -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "period"] = period

    with pytest.raises(ValueError, match="canonical"):
        validate_hb_dataframe(hb_input_dataframe)


def test_validate_hb_dataframe_allows_missing_numeric_values() -> None:
    hb_input_dataframe = valid_hb_dataframe()
    hb_input_dataframe.loc[0, "value"] = None

    validated_dataframe = validate_hb_dataframe(hb_input_dataframe)

    assert pd.isna(validated_dataframe.loc[0, "value"])


def test_hb_data_handler_meta_requires_get_hb_dataframe_implementation() -> None:
    with pytest.raises(TypeError, match="abstract"):
        HBDataHandlerMeta()
