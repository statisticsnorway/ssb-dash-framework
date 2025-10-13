import ibis
import eimerdb as db

conn = db.EimerDBInstance(
    "ssb-dapla-felles-data-produkt-prod",
    "produksjonstilskudd_altinn3",
)
con = ibis.duckdb.connect()

skjema = "all"
time_units = ["aar"]

_t_0 = "2024"
_t_1 = "2023"


skjemamottak = conn.query(
    "SELECT * FROM skjemamottak", partition_select={"aar": [_t_0, _t_1]}
)
skjemadata = conn.query(
    "SELECT * FROM skjemadata_hoved", partition_select={"aar": [_t_0, _t_1]}
)
datatyper = conn.query(
    "SELECT * FROM datatyper", partition_select={"aar": [_t_0, _t_1]}
)

con.create_table("skjemamottak", skjemamottak)
con.create_table("skjemadata_hoved", skjemadata)
con.create_table("datatyper", datatyper)

skjemamottak_tbl = con.table("skjemamottak")
skjemadata_tbl = con.table("skjemadata_hoved")
datatyper_tbl = con.table("datatyper")

skjemamottak_tbl = (  # Get relevant refnr values from skjemamottak
    skjemamottak_tbl.filter(skjemamottak_tbl.aktiv)
    .order_by(ibis.desc(skjemamottak_tbl.dato_mottatt))
    .distinct(on=[*time_units, "ident"], keep="first")
)
if skjema != "all":
    skjemamottak_tbl = skjemamottak_tbl.filter(skjemamottak_tbl.skjema == skjema)

relevant_refnr = skjemamottak_tbl["refnr"].to_list()

skjemadata_tbl = (
    skjemadata_tbl.filter(skjemadata_tbl.refnr.isin(relevant_refnr))
    .join(datatyper_tbl.select("variabel", "datatype"), ["variabel"], how="inner")
    .filter(datatyper_tbl.datatype == "int")
    .cast({"verdi": "int", "aar": "str"})
    .pivot_wider(
        id_cols=["variabel"],
        names_from="aar",  # TODO: Tidsenhet
        values_from="verdi",
        values_agg="sum",
    )
    .mutate(
        diff=lambda t: t[_t_0] - t[_t_1],
        pdiff=lambda t: ((t[_t_0].fill_null(0) - t[_t_1].fill_null(0))
        / t[_t_1].fill_null(1)
        * 100).round(2),
    )
)

print(skjemadata_tbl.to_pandas())
