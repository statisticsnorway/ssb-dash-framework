"""The finished app from the getting started guide: docs/guides/getting_started.md."""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ssb_dash_framework import AppConfig
from ssb_dash_framework import FigureDisplay
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import main_layout

# 1. Read the app config. It sets up the app and the variable selector.
config_path = Path(__file__).parent / "app.yaml"
config = AppConfig(**config_parser_yaml(str(config_path)))
app, tab_list, window_list = build_app_from_config(config)

# 2. Some example data. In your own app you would read your own data, preferably using get_connection() as explained...
data = pd.DataFrame(
    {
        "aar": ["2024", "2024", "2024", "2025", "2025", "2025"],
        "orgnr": ["111111111", "222222222", "333333333"] * 2,
        "omsetning": [120, 80, 150, 130, 95, 140],
    }
)


# 3. Functions that make the figures.
def turnover_per_unit(aar: str) -> go.Figure:
    """Bar chart with the turnover of every unit in the selected year."""
    selected = data[data["aar"] == aar]
    return px.bar(selected, x="orgnr", y="omsetning", title=f"Turnover in {aar}")


def turnover_over_time(orgnr: str) -> go.Figure:
    """Line chart with the turnover of the selected unit for every year."""
    selected = data[data["orgnr"] == orgnr]
    return px.line(selected, x="aar", y="omsetning", title=f"Turnover for {orgnr}")


# 4. Add modules in Python.
tab_list.append(
    FigureDisplay(
        label="Turnover per unit",
        figure_func=turnover_per_unit,
        inputs=["aar"],
        output="orgnr",
        clickdata_func=lambda clickdata: clickdata["points"][0]["x"],
    )
)

window_list.append(
    FigureDisplay(
        label="Turnover over time",
        figure_func=turnover_over_time,
        inputs=["orgnr"],
    )
)

# 5. Build the layout and start the app.
app.layout = main_layout(
    window_list=window_list,
    tab_list=tab_list,
    default_values={"aar": "2025", "orgnr": "111111111"},
)

if __name__ == "__main__":
    app.run(
        debug=False,
        port=config.app_settings.port,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
