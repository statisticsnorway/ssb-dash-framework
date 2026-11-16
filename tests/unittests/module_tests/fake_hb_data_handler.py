"""Deterministic HB data handler for module tests."""

import pandas as pd

from ssb_dash_framework.modules.hb.data_handler import HBDataHandlerMeta
from ssb_dash_framework.modules.hb.data_handler import HBDataResult
from ssb_dash_framework.modules.hb.data_handler import validate_hb_dataframe


class FakeHBDataHandler(HBDataHandlerMeta):
    """Provide a validated, preconfigured HB DataFrame without a backend."""

    def __init__(self, hb_dataframe: pd.DataFrame) -> None:
        """Initialize the handler with deterministic test data."""
        self._hb_dataframe = hb_dataframe.copy(deep=True)

    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        hb_dataframe = self._hb_dataframe.copy(deep=True)
        validate_hb_dataframe(hb_dataframe)
        return HBDataResult(hb_dataframe=hb_dataframe)
