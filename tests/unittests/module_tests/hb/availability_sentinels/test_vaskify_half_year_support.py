import pandas as pd
import pytest

import ssb_dash_framework.modules.hb.vaskify as hb_vaskify


def _run_direct_vaskify_hb(
    hb_input_dataframe: pd.DataFrame,
    hb_comparison_periods: tuple[str, str],
) -> pd.DataFrame:
    detector = hb_vaskify.Detect(hb_input_dataframe, id_nr="unit_id")
    return detector.hb(
        y_var="value",
        time_var="period",
        time_periods=list(hb_comparison_periods),
        strata_var="",
        pu=0.5,
        pa=0.05,
        pc=20,
        percentiles=(0.25, 0.75),
        flag="flag_hb",
        output_format="wide",
        output_scope="all",
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Native Vaskify half-year support is available; remove the HALF_YEAR "
        "execution guard and enable native half-year periods."
    ),
)
def test_installed_vaskify_supports_canonical_half_year_periods() -> None:
    hb_input_dataframe = pd.DataFrame(
        {
            "unit_id": ["unit-1", "unit-1", "unit-2", "unit-2"],
            "period": ["2023-2", "2024-1", "2023-2", "2024-1"],
            "value": [10.0, 12.0, 15.0, 16.0],
        }
    )

    result = _run_direct_vaskify_hb(
        hb_input_dataframe,
        ("2023-2", "2024-1"),
    )

    assert not result.empty
    assert "unit_id" in result.columns
