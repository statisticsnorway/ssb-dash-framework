"""Runnable HB demo with a deterministic in-memory data handler."""

import os

import pandas as pd

from ssb_dash_framework import HBMethod
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import VariableSelectorOption
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework.modules.hb import HBDataHandlerMeta
from ssb_dash_framework.modules.hb import HBDataResult
from ssb_dash_framework.setup.variableselector import TimeUnit
from ssb_dash_framework.setup.variableselector import TimeUnitType

PORT = 8072


class _DeterministicHBDataHandler(HBDataHandlerMeta):
    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        previous_period, selected_period = hb_comparison_periods
        hb_records = []
        for unit_number, previous_value in enumerate(
            (10.0, 20.0, 30.0, 40.0, 50.0, 60.0),
            start=1,
        ):
            unit_id = f"demo-{unit_number:03}"
            hb_records.extend(
                [
                    {
                        "unit_id": unit_id,
                        "period": previous_period,
                        "value": previous_value,
                    },
                    {
                        "unit_id": unit_id,
                        "period": selected_period,
                        "value": previous_value * 1.1,
                    },
                ]
            )
        hb_records.extend(
            [
                {
                    "unit_id": "demo-flagged",
                    "period": previous_period,
                    "value": 10.0,
                },
                {
                    "unit_id": "demo-flagged",
                    "period": selected_period,
                    "value": 100.0,
                },
            ]
        )
        return HBDataResult(pd.DataFrame.from_records(hb_records))


configured_hb_time_unit = TimeUnit(
    name="periode",
    frequency=TimeUnitType.YEAR,
)
VariableSelectorConfig(
    ident="unit_id",
    time_units=configured_hb_time_unit,
)
VariableSelectorOption("measure")

app = app_setup(
    port=PORT,
    service_prefix=(
        os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
        if os.getenv("DAPLA_ENVIRONMENT")
        else ""
    ),
    stylesheet="lumen",
    enable_logging=False,
)
hb_method = HBMethod(
    hb_data_handler=_DeterministicHBDataHandler(),
    hb_variable_selector="measure",
    configured_hb_time_unit=configured_hb_time_unit,
)
app.layout = main_layout(
    window_list=[],
    tab_list=[hb_method],
    default_values={
        "measure": "turnover",
        "periode": "2024",
        "unit_id": "demo-001",
    },
)

if __name__ == "__main__":
    app.run(
        debug=False,
        port=PORT,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
