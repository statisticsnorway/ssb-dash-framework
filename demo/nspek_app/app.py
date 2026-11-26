import os
import tempfile
from pathlib import Path

#from ssb_dash_framework import Aarsregnskap
from ssb_dash_framework import Naeringsspesifikasjon
from ssb_dash_framework import NspekControls
from ssb_dash_framework import NspekControlView
from ssb_dash_framework import NspekDashboard
from ssb_dash_framework import VariableSelector
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_nspek_sqlite_connection
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType
from ssb_dash_framework_testdata.nspek import build_db

# This demo runs on local SQLite testdata instead of a real Postgres database.
# Build and seed SQLite database for the demo.
db_path = Path(tempfile.gettempdir()) / "ssb_dash_framework_nspek_demo.sqlite"
db_path.unlink(missing_ok=True)
build_db.seed_sqlite(db_path)

# Configure the app to use this local SQLite file.
set_nspek_sqlite_connection(str(db_path))

# Set environmental variable for foretak database lookup.
os.environ["SSB_FORETAK_DB_PATH"] = str(db_path)

perioder = ["aar"]

port = 8000
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="info", log_to_file=True)

VariableSelectorConfig(
    time_units=TimeUnit(name="aar", frequency=TimeUnitType.YEAR),
    ident="ident",
    secondary_idents=["foretak", "tema"],
)

year_default = "2024"
ident_default = "999000002"
tema_default = "Resultat"

default_values = {
    "aar": year_default,
    "ident": ident_default,
    "foretak": ident_default,
    "tema": tema_default,
}

tab_list = []

tab_list.extend(
    [
        NspekControlView(
            time_units=perioder,
            control_class=NspekControls,
        ),
        #Aarsregnskap(),
    ]
)

window_list = []

window_list.extend(
    [
        Naeringsspesifikasjon(
            time_units=perioder,
            db_user=None,  # Not needed since we are using sqlite connection
        ),
        NspekDashboard(time_units=perioder),
    ]
)

app.layout = main_layout(window_list, tab_list, default_values=default_values)

hacky_varselector = VariableSelector(
    selected_inputs=["aar"], selected_states=["foretak", "ident", "tema"]
)

server = app.server

if __name__ == "__main__":
    app.run(
        debug=True,
        port=port,
        jupyter_server_url=domain,
        jupyter_mode="tab",
        threaded=False,
    )
