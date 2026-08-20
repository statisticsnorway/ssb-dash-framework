import os

import plotly.express as px
from plotly.graph_objs._figure import Figure

from ssb_dash_framework import AppConfig
from ssb_dash_framework import FigureDisplayWindow
from ssb_dash_framework import apply_edits
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import main_layout

# Here the base of the app is built from the supplied yaml config file
# No need to change this part of the .py file
# If you want to include more modules, you can update the app.yaml file

yaml_content = config_parser_yaml("demo/parqueteditor/app.yaml")
config = AppConfig(**yaml_content)
app, tab_list, window_list = build_app_from_config(config)

# Or If you prefer using python to add modules, you can do so below this
# point by appending instantiated modules to tab_list and window_list


def make_bars(aar: str, orgnr: str) -> Figure:
    """Function to make a barplot for updated data."""
    data = apply_edits(
        "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet",
    )

    return px.bar(data, x="orgnr", y=["inntekter", "utgifter"], barmode="group")


window_list.append(
    FigureDisplayWindow(
        label="Inntekter og utgifter",
        # Note that the list in 'inputs' is telling the module to 'listen' to the
        # fields listed as outputs from the ParquetEditor in the yaml file
        inputs=["aar", "orgnr"],
        figure_func=make_bars,
    )
)

# From here the app is built and started, no need to change anything below this point

app.layout = main_layout(window_list=window_list, tab_list=tab_list)

app.run(
    debug=True,
    port=config.app_settings.port,
    jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
    jupyter_mode="tab",
    threaded=False,
)
