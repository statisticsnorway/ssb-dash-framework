import os

if os.getenv("DAPLA_ENVIRONMENT", None) == "PROD":
    from ssb_dash_framework import _get_connection_object
    from ssb_dash_framework import set_eimerdb_connection

    set_eimerdb_connection(
        bucket_name="ssb-dapla-felles-data-produkt-prod",
        eimer_name="produksjonstilskudd_altinn3",
    )
    try:
        _get_connection_object().query("SELECT * FROM enheter")
    except Exception as e:
        raise e
else:
    raise NotImplementedError(
        "Demo currently only works inside of SSB's Dapla Prod environment using the 'Dapla felles' buckets."
    )

test = _get_connection_object().query(
    "SELECT * FROM skjemamottak WHERE aar = 2024 and refnr = 20243"
)
print(test)
test = _get_connection_object().query(
    "SELECT * FROM skjemadata_hoved WHERE aar = 2024 and refnr = 20243"
)
print(test)

from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables
from ssb_dash_framework.experimental.modules.data_editor.core import DataEditor
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_table import (
    DataEditorTable,
)
from ssb_dash_framework.experimental.modules.data_editor.helper_buttons.supporting_table import (
    DataEditorSupportTable,
)
from ssb_dash_framework.experimental.modules.data_editor.helper_buttons.supporting_table import (
    DataEditorSupportTables,
)
from ssb_dash_framework.utils.config_tools.set_variables import TimeUnitType
from ssb_dash_framework.utils.config_tools.set_variables import VariableSelectorConfig

VariableSelectorConfig(
    refnr="refnr",
    ident="ident",
    time_units={"aar": TimeUnitType.YEAR},
    # grouping_variables=["komm_nr"]
)

set_variables(
    [
        "variabel",
        "altinnskjema",
        "valgt_tabell",
    ]
)

default_values = {"aar": "2024", "refnr": "20243", "altinnskjema": "RA-7357"}

port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug", log_to_file=True)


def support_table_get_data(aar, skjema):
    return _get_connection_object().query(
        f"SELECT * FROM skjemadata_hoved WHERE aar = {aar} and skjema ='{skjema}'"
    )


DataEditorSupportTable(
    label="Demo",
    get_data_func=support_table_get_data,
    inputs=["aar", "altinnskjema"],
)

DataEditorSupportTables()

DataEditorTable(applies_to_tables=["skjemadata_hoved"], applies_to_forms=["RA-7357"])

tab_list = [DataEditor()]
window_list = []

app.layout = main_layout(window_list, tab_list, default_values=default_values)

if __name__ == "__main__":
    print("Running app!")
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
