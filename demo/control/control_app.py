# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#   kernelspec:
#     display_name: demo-ssb-dash
#     language: python
#     name: demo-ssb-dash
# ---

# +
import os  # Nødvendig for oppsett

from control_code import DemoControls  # For å kunne bruke kontroll-modulen

# Moduler importert fra biblioteket
# from ssb_dash_framework import HBMethod
from ssb_dash_framework import AggDistPlotterWindow
from ssb_dash_framework import AltinnControlViewWindow
from ssb_dash_framework import AltinnSkjemadataEditor
from ssb_dash_framework import FreeSearchTab
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_eimerdb_connection
from ssb_dash_framework import set_variables

# from egentilpassing.hb_method import hb_get_data


# Kobling til EimerDB som ligger i fellesbøtta.
set_eimerdb_connection(
    "ssb-dapla-felles-data-produkt-prod",
    "produksjonstilskudd_altinn3",
)
selected_time_units = ["aar"]  # Tidsenheten(e) til dataene

# Basic app-oppsett
port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug", log_to_file=True)

# VARIABLER: Velg hvilke variabler appen skal bruke. Default values er valgfritt, men anbefalt.
set_variables(
    [
        "aar",
        "ident",
        "statistikkvariabel",
        "altinnskjema",
        "valgt_tabell",
        "refnr",
    ]
)
default_values = {
    "aar": "2023",
    "statistikkvariabel": "fulldyrket",
    "valgt_tabell": "skjemadata_hoved",
    "altinnskjema": "RA-7357",
}

# Uncomment this if you have access to the VoF shared bucket.
# bof_module = BofInformationTab(
#     variableselector_foretak_name="ident"
# )

# Legg in alle tabene i denne lista
tab_list = [
    AltinnSkjemadataEditor(time_units=selected_time_units, variable_connection={}),
    FreeSearchTab(),
    #    bof_module # Uncomment this if you have access to the VoF shared bucket.
]

# MODALENE: Lag en liste med alle modalene
# hb = HBMethod(
#     database=conn,
#     hb_get_data_func=hb_get_data,
#     selected_state_keys=["aar", "statistikkvariabel"],
#     selected_ident="ident",
#     variable="verdi",
# )

# visualiseringsbyggermodul = VisualizationBuilder(conn)
# datafangstmodalen = AltinnDataCaptureWindow(
#     time_units=selected_time_units
# )
aggdistplotter = AggDistPlotterWindow(selected_time_units)

controls = AltinnControlViewWindow(
    time_units=["aar"], control_dict={"RA-7357": DemoControls}
)

# MODALENE: Lag en liste med alle modalene
modal_list = [
    # datafangstmodalen,
    aggdistplotter,
    controls,
    # hb,
    # visualiseringsbyggermodul,
]

# Denne linja genererer layouten til hele appen. Her legges listene med valgt innhold for modalene, fanene og variablene.
app.layout = main_layout(modal_list, tab_list, default_values=default_values)

if __name__ == "__main__":
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
