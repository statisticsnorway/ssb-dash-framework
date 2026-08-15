import os

from dash import no_update
import plotly.express as px
import pandas as pd
from ibis import _
from ssb_dash_framework.config.yaml_parser import config_parser_yaml
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
    from ssb_dash_framework import set_sqlite_connection
    from ssb_dash_framework import get_connection

    set_sqlite_connection(f"/home/onyxia/work/ssb-dash-framework/demo/demo.sqlite")
    try:
        with get_connection() as conn:
            t = conn.table("enheter")
            t = t.select("ident").to_pandas()
    except Exception as e:
        raise e
else:
    raise NotImplementedError(
        "Demo currently only works inside of SSB's Dapla Prod environment using the 'Dapla felles' buckets."
    )


from ssb_dash_framework import EditingTableWindow, app_setup
from ssb_dash_framework import get_connection
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables
from ssb_dash_framework.experimental.modules.data_editor.core import DataEditor
from ssb_dash_framework.experimental.modules.data_editor.core import DataEditorInfoRow
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import (
    DataViewCustom,
)
from ssb_dash_framework.utils.config_tools.set_variables import TimeUnitType
from ssb_dash_framework.utils.config_tools.set_variables import VariableSelectorConfig

VariableSelectorConfig(
    refnr="refnr",
    ident="ident",
    time_units={"aar": TimeUnitType.YEAR},
    grouping_variables=["fylke", "komm_nr"],
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

tab_list = []
window_list = []

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


config = config_parser_yaml(str("demo/demo.yaml"))
check: DataViewCustom = DataViewCustom.from_dict(config)

DataEditorInfoRow(
    variables={"Navn": {"source": "enhetsinfo", "variable_name": "orgnavn"}}
)


def support_table_get_data(aar, skjema):
    with get_connection() as conn:
        t = conn.table("skjemadata_hoved")
        t = t.filter(t.aar == aar).filter(t.skjema == skjema)
        return t.to_pandas()


DataEditorSupportTable(
    label="Demo",
    get_data_func=support_table_get_data,
    inputs=["aar", "altinnskjema"],
)
DataEditorSupportTables()
DataEditorSidebarEditingStatus()
DataEditorSidebarComment()

tab_list.append(DataEditor())


def fylke_table(aar):
    with get_connection() as conn:
        e = conn.table("enhetsinfo")
        e = (
            e.filter(e.aar == aar)
            .filter(e.variabel == "kommunenr")
            .mutate(fylke=e.verdi.left(2))
        )
        t = conn.table("skjemadata_hoved")
        return (
            t.filter(t.aar == aar)
            .filter(t.variabel == "totalareal")
            .join(e, "ident", how="left")
            .mutate(verdi=t.verdi.cast(float))
            .group_by("fylke")
            .agg(totalt_areal=_.verdi.sum())
            .to_pandas()
        )


window_list.append(
    EditingTableWindow(
        label="Fylkestabell",
        inputs=["aar"],
        states=[],
        get_data_func=fylke_table,
        output="fylke",
    )
)


def kommune_table(aar, fylke):
    if not fylke:
        return pd.DataFrame()
    with get_connection() as conn:
        e = conn.table("enhetsinfo")
        e = (
            e.filter(e.aar == aar)
            .filter(e.variabel == "kommunenr")
            .mutate(fylke=e.verdi.left(2))
            .mutate(kommunenr=e.verdi)
        )
        t = conn.table("skjemadata_hoved")
        return (
            t.filter(t.aar == aar)
            .filter(t.variabel == "totalareal")
            .join(e, "ident", how="left")
            .filter(_.fylke == fylke)
            .mutate(verdi=t.verdi.cast(float))
            .group_by("kommunenr")
            .agg(totalt_areal=_.verdi.sum())
            .to_pandas()
        )


window_list.append(
    EditingTableWindow(
        label="Kommunetabell",
        inputs=["aar", "fylke"],
        states=[],
        get_data_func=kommune_table,
        output="kommunenr",
        output_varselector_name="komm_nr",
    )
)


def units_in_kommune_table(aar, komm_nr):
    if not komm_nr:
        return pd.DataFrame()
    with get_connection() as conn:
        e = conn.table("enhetsinfo")
        e = (
            e.filter(e.aar == aar)
            .filter(e.variabel == "kommunenr")
            .mutate(kommunenr=e.verdi)
        )
        t = conn.table("skjemadata_hoved")
        return (
            t.filter(t.aar == aar)
            .filter(t.variabel == "totalareal")
            .join(e, "ident", how="left")
            .filter(_.kommunenr == komm_nr)
            .mutate(verdi=t.verdi.cast(float))
            .to_pandas()
        )


window_list.append(
    EditingTableWindow(
        label="Enheter i kommune tabell",
        inputs=["aar", "komm_nr"],
        states=[],
        get_data_func=units_in_kommune_table,
        output="ident",
    )
)


app.layout = main_layout(window_list, tab_list, default_values=default_values)

if __name__ == "__main__":
    print("Running app!")
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
