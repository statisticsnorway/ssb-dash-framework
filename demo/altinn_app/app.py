import os
import tempfile
from pathlib import Path

from ssb_dash_framework import AppConfig
from ssb_dash_framework import EditingTable
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import get_connection
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_sqlite_connection
from ssb_dash_framework_testdata.altinn import build_db

# This demo runs on the bundled Altinn testdata instead of a real database.
# set_sqlite_connection() opens a new connection per query, so the testdata has
# to live in a file rather than in ":memory:". The file is rebuilt on every run
# because the .sql testdata files are plain INSERTs and would otherwise stack up.
db_path = Path(tempfile.gettempdir()) / "ssb_dash_framework_altinn_demo.sqlite"
db_path.unlink(missing_ok=True)
build_db.seed_sqlite(db_path)
set_sqlite_connection(str(db_path))

# Here the base of the app is built from the supplied yaml config file
# No need to change this part of the .py file
# If you want to include more modules, you can update the app.yaml file

yaml_content = config_parser_yaml("demo/altinn_app/config/base.yaml")
config = AppConfig(**yaml_content)
app, tab_list, window_list = build_app_from_config(config)

# Or If you prefer using python to add modules, you can do so below this
# point by appending instantiated modules to tab_list and window_list


def get_enheter_data(*args, **kwargs):
    with get_connection() as conn:
        t = conn.table("enheter")
        return t.select(["iso_period", "skjema", "ident"]).to_pandas()


window_list.append(
    EditingTable(
        label="Klikk meg og velg enhet + skjema",
        inputs=["periode"],
        states=[],
        get_data_func=get_enheter_data,
        output=["iso_period", "skjema", "ident"],
        output_varselector_name=["periode", "altinnskjema", "ident"],
    )
)

# From here the app is built and started, no need to change anything below this point

app.layout = main_layout(
    window_list=window_list,
    tab_list=tab_list,
    default_values={
        "periode": "2026",
        "ident": "ATF2134661",
        "altinnskjema": "RA-0745",
        "refnr": "b250f49e78cb"
    },
)

app.run(
    debug=True,
    port=config.app_settings.port,
    jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
    jupyter_mode="tab",
    threaded=False,
)
