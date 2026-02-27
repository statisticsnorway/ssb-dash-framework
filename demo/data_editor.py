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

from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables
from ssb_dash_framework.modules.data_editor.core import DataEditor

set_variables(
    [
        "aar",
        "ident",
        "variabel",
        "altinnskjema",
        "valgt_tabell",
        "refnr",
    ]
)


port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug", log_to_file=True)

tab_list = [DataEditor()]
window_list = []

app.layout = main_layout(window_list, tab_list)

if __name__ == "__main__":
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
