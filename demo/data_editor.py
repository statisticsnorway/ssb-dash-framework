import os

import plotly.express as px
from ibis import _

from ssb_dash_framework.experimental.modules.data_editor.helper_buttons.supporting_table import (
    DataEditorSupportTable,
)
from ssb_dash_framework.experimental.modules.data_editor.helper_buttons.supporting_table import (
    DataEditorSupportTables,
)
from ssb_dash_framework.experimental.modules.data_editor.sidebar_components.comment import (
    DataEditorSidebarComment,
)
from ssb_dash_framework.experimental.modules.data_editor.sidebar_components.editing_status import (
    DataEditorSidebarEditingStatus,
)

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
from ssb_dash_framework import get_connection
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables
from ssb_dash_framework.experimental.modules.data_editor.core import DataEditor, DataEditorInfoRow
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import (
    DataViewCustom,
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

default_values = {
    "aar": "2024",
    "refnr": "20243",
    "ident": "969744066",
    "altinnskjema": "RA-7357",
}

port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug", log_to_file=True)


# Doodle for custom layout
def make_fig_bar():
    with get_connection() as conn:
        t = conn.table("skjemadata_hoved")
        df = t.filter(_.aar == 2024).to_pandas()
    df["verdi"] = df["verdi"].astype(float).astype(int)
    df = df.groupby("variabel", as_index=False).agg({"verdi": "sum"})
    fig = px.bar(df, x="variabel", y="verdi")
    return fig


def make_fig_scatter():
    refnr = "20243"
    skjema = "RA-7357"

    with get_connection() as conn:
        from ssb_dash_framework import active_no_duplicates_refnr_list

        relevant_refnr = active_no_duplicates_refnr_list(conn, skjema)
        t = conn.table("skjemadata_hoved")
        df = (
            t.filter(_.refnr.isin(relevant_refnr))
            .filter(_.variabel.isin(["fulldyrket", "totalareal"]))
            .to_pandas()
        )
        df["verdi"] = df["verdi"].astype(float).astype(int)
        df = df.pivot_table(
            index="ident", columns="variabel", values="verdi"
        ).reset_index()
        df["highlight"] = df["ident"].isin(
            t.filter(_.refnr == refnr).select(_.ident).to_pandas()["ident"]
        )
    fig = px.scatter(
        df,
        x="fulldyrket",
        y="totalareal",
        hover_name="ident",
        color="highlight",
        color_discrete_map={True: "crimson", False: "steelblue"},
    )
    return fig


def make_table(tabell, skjema, refnr, *time_units):

    with get_connection() as conn:
        t = conn.table(tabell)
        return t.filter(_.refnr == refnr).filter(_.skjema == skjema).to_pandas()


def populate_microlayout(table, form, refnr, *args, **kwargs):
    with get_connection() as conn:
        t = conn.table(table)
        data = t.filter(_.skjema == form).filter(_.refnr == refnr).to_pandas()

    totalareal = data.loc[data["variabel"] == "totalareal"]["verdi"].item()
    fulldyrket = data.loc[data["variabel"] == "fulldyrket"]["verdi"].item()
    innmarksbeite = data.loc[data["variabel"] == "innmarksbeite"]["verdi"].item()
    return totalareal, fulldyrket, innmarksbeite




DataEditorInfoRow(
    variables_dict = {
        "Navn": {
            "source": "enhetsinfo",
            "variable_name": "orgnavn"
        }
    }
)

# layout = [
#     {
#         "row": [
#             {"col": {"table": {"label": "Oversiktstabell", "table_func": make_table}}},
#             {"col": {"figure": {"label": "Barplot", "figure_func": make_fig_bar}}},
#         ]
#     },
#     {
#         "row": [
#             {
#                 "col": {
#                     "microlayout": {
#                         "label": "Test mikrolayout",
#                         "layout": [
#                             {
#                                 "type": "input",
#                                 "label": "Totalareal",
#                                 "variable": "totalareal",
#                             },
#                             {
#                                 "type": "input",
#                                 "label": "Fulldyrket",
#                                 "variable": "fulldyrket",
#                             },
#                             {
#                                 "type": "input",
#                                 "label": "Innmarksbeite",
#                                 "variable": "innmarksbeite",
#                             },
#                         ],
#                         "get_data_func": "default",
#                         "update_func": "default",
#                     },
#                     "kwargs": {"width": 1},
#                 }
#             },
#             {
#                 "col": {
#                     "figure": {
#                         "label": "Scatterplot fulldyrket - totalareal",
#                         "figure_func": make_fig_scatter,
#                     },
#                 }
#             },
#         ]
#     },
# ]

# DataViewCustom(
#     applies_to_tables=["skjemadata_hoved"], applies_to_forms=["RA-7357"], layout=layout
# )

DataViewCustom.from_yaml("/home/onyxia/work/ssb-dash-framework/demo/yaml based/view_skjemadata_hoved_ra_7357.yaml", dict_key="CustomView")

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
DataEditorSidebarEditingStatus()
DataEditorSidebarComment()
# DataEditorTable(applies_to_tables=["skjemadata_hoved"], applies_to_forms=["RA-7357"])

tab_list = [DataEditor()]

window_list = []

app.layout = main_layout(window_list, tab_list, default_values=default_values)

if __name__ == "__main__":
    print("Running app!")
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
