import os
import tempfile
from pathlib import Path

from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_sqlite_connection
from ssb_dash_framework.experimental import AltinnMacroModuleDataHandler
from ssb_dash_framework.experimental import MacroModule
from ssb_dash_framework_testdata.altinn import build_db

# This demo runs on the bundled Altinn testdata (form RA-0745, yearly 2024-2026).
# set_sqlite_connection() opens a new connection per query, so the testdata has to
# live in a file. It is rebuilt on every run because the .sql files are plain INSERTs.
db_path = Path(tempfile.gettempdir()) / "ssb_dash_framework_macro_demo.sqlite"
db_path.unlink(missing_ok=True)
build_db.seed_sqlite(db_path)
set_sqlite_connection(str(db_path))

# 'naring' is also a grouping variable in the variable selector, so typing a code
# there filters both macro modules.
VariableSelectorConfig(
    ident="ident",
    time_units={"name": "periode", "frequency": "year"},
    grouping_variables=["naring"],
)

port = 8071
service_prefix = (
    os.getenv("DAPLA_ENVIRONMENT") and os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
) or ""
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="info", log_to_file=False)

naring = {"01.11": "Dyrking av korn", "01.41": "Melkeproduksjon"}
skip_totals = {"NyEngSpredUtsID": ["TOTAL_ROW"]}

# One observation per unit.
per_unit = AltinnMacroModuleDataHandler(
    skjema="RA-0745",
    value_variables={
        "NyEngArbAreal": "Areal ny eng",
        "NyEngSpredUtsGjodsMengde": "Gjødselmengde",
    },
    grouping_variables=["naring", "kommune"],
    codelists={"naring": naring},
    exclude_instances=skip_totals,
)

# One observation per spreader in the repeating group.
per_spreader = AltinnMacroModuleDataHandler(
    skjema="RA-0745",
    value_variables={"NyEngSpredUtsGjodsMengde": "Gjødselmengde"},
    grouping_variables=["NyEngSpredUtsID", "naring"],
    codelists={"naring": naring},
    repeating_group="/NyEngSpredUtsGroup",
    exclude_instances=skip_totals,
)

tab_list = [
    MacroModule(per_unit, label="Makro per enhet"),
    MacroModule(per_spreader, label="Makro per spredemetode"),
]

app.layout = main_layout([], tab_list, default_values={"periode": "2026"})

if __name__ == "__main__":
    app.run(debug=False, port=port, jupyter_server_url=domain, jupyter_mode="tab")
