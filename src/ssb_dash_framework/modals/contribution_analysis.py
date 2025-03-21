import eimerdb as db
import pandas as pd
import plotly.express as px

bucket = "ssb-dapla-felles-data-produkt-prod"
db_name = "produksjonstilskudd"
conn = db.EimerDBInstance(bucket, db_name)

year = 2023
group = "fylke"
variables = ["arealtilskudd", "husdyrtilskudd", "beitetilskudd", "fulldyrket"]

a = conn.query(f"SELECT * FROM skjemadata WHERE soeknads_aar = '{year}' AND variable IN {variables}")
a["value"] = a["value"].fillna(0)
a["value"] = a["value"].replace("nan", 0)
a["value"] = a["value"].astype(float)
a["value"] = a["value"].astype(int)

b = conn.query(f"SELECT * FROM enhetsinfo WHERE soeknads_aar = '{year}' AND variable = 'saksbehandlende_kommune'").assign(fylke = lambda x: x["value"].str[:2])[["soeknads_aar", "orgnr", "fylke"]]

df_t0 =pd.merge(a,b, on = ["orgnr", "soeknads_aar"])

a = conn.query(f"SELECT * FROM skjemadata WHERE soeknads_aar = '{year-1}' AND variable IN {variables}")
a["value"] = a["value"].fillna(0)
a["value"] = a["value"].replace("nan", 0)
a["value"] = a["value"].astype(float)
a["value"] = a["value"].astype(int)

b = conn.query(f"SELECT * FROM enhetsinfo WHERE soeknads_aar = '{year-1}' AND variable = 'saksbehandlende_kommune'").assign(fylke = lambda x: x["value"].str[:2])[["soeknads_aar", "orgnr", "fylke"]]

df_t1=pd.merge(a,b, on = ["orgnr", "soeknads_aar"])

a = df_t0.groupby(["variable", group], as_index=False).agg({"value": "sum"})

b = df_t1.groupby(["variable", group], as_index=False).agg({"value": "sum"})

merged = pd.merge(a,b, on = ["fylke", "variable"], suffixes = [f"_{year}", f"_{year-1}"]).assign(percentage_change=lambda x: (x[f"value_{year}"] - x[f"value_{year-1}"]) / x[f"value_{year-1}"] * 100)
merged

px.bar(
    merged,
    y="variable",
    x="percentage_change",
    orientation='h',
    color="fylke",
    title="Bidrag"
)


