from functools import reduce

import ibis
import eimerdb as db

conn = db.EimerDBInstance(
    "ssb-dapla-felles-data-produkt-prod",
    "produksjonstilskudd_altinn3",
)
"""
SELECT
    s.variabel,
    {column_name_expr_s} AS time_combination,
    SUM(CAST(s.verdi AS NUMERIC)) AS verdi
FROM {tabell} AS s
JOIN (
    SELECT
        {column_name_expr_t2} AS time_combination,
        t2.ident,
        t2.refnr,
        t2.dato_mottatt
    FROM
        skjemamottak AS t2
    WHERE aktiv = True
    QUALIFY
        ROW_NUMBER() OVER (
            PARTITION BY {column_name_expr_t2}, t2.ident
            ORDER BY t2.dato_mottatt DESC
        ) = 1
) AS mottak_subquery
    ON {column_name_expr_s} = mottak_subquery.time_combination
    AND s.ident = mottak_subquery.ident
    AND s.refnr = mottak_subquery.refnr
JOIN (
    SELECT
        d.variabel,
        {column_name_expr_d} AS time_combination,
        d.radnr,
        d.datatype
    FROM datatyper AS d
) AS datatype_subquery
    ON s.variabel = datatype_subquery.variabel
    AND {column_name_expr_s} = datatype_subquery.time_combination
WHERE datatype_subquery.datatype = 'int' {where_query_add}
GROUP BY
    s.variabel,
    datatype_subquery.radnr,
    {group_by_clause}
ORDER BY datatype_subquery.radnr;
"""

# SQL_COLUMN_CONCAT = " || '_' || "

# column_name_expr_s = SQL_COLUMN_CONCAT.join(
#     [f"s.{unit}" for unit in self.time_units]
# )
# column_name_expr_t2 = SQL_COLUMN_CONCAT.join(
#     [f"t2.{unit}" for unit in self.time_units]
# )
# column_name_expr_d = SQL_COLUMN_CONCAT.join(
#     [f"d.{unit}" for unit in self.time_units]
# )

# group_by_clause = ", ".join([f"s.{unit}" for unit in self.time_units])

con = ibis.duckdb.connect()

skjemamottak = conn.query("SELECT * FROM skjemamottak", partition_select={"aar": ["2024", 2023]})
skjemadata = conn.query("SELECT * FROM skjemadata_hoved", partition_select={"aar": ["2024", 2023]})
datatyper = conn.query("SELECT * FROM datatyper", partition_select={"aar": ["2024", 2023]})

con.create_table("skjemamottak", skjemamottak)
con.create_table("skjemadata", skjemadata)
con.create_table("datatyper", datatyper)

skjemamottak_tbl = con.table("skjemamottak")
skjemadata_tbl = con.table("skjemadata")
datatyper_tbl = con.table("datatyper")

# Your time units
time_units = ['aar']

# helper to concatenate time units into one string column
def concat_time_units(tbl, units):
    return reduce(lambda a, b: a.concat('_').concat(b), [tbl[unit].cast("string") for unit in units])

# -----------------------------
# Step 1: mottak_subquery (latest per ident & time)
# -----------------------------
time_comb_mottak = concat_time_units(skjemamottak_tbl, time_units)

mottak_subquery_base = skjemamottak_tbl.mutate(time_combination=time_comb_mottak)

row_number_window = ibis.window(
    group_by=[mottak_subquery_base['time_combination'], mottak_subquery_base['ident']],
    order_by=mottak_subquery_base['dato_mottatt'].desc(),
)
print(row_number_window)
mottak_subquery = (
    mottak_subquery_base
    .filter(mottak_subquery_base['aktiv'] == True)
 #   .mutate(row_number=ibis.row_number().over(row_number_window))
  #  .filter(lambda t: t['row_number'] == 1)
    .select(['time_combination', 'ident', 'refnr', 'dato_mottatt'])
)
print(mottak_subquery.to_pandas())

# -----------------------------
# Step 2: datatype_subquery
# -----------------------------
time_comb_dtype = concat_time_units(datatyper_tbl, time_units)

datatype_subquery = (
    datatyper_tbl
    .mutate(time_combination=time_comb_dtype)
    .select(['variabel', 'time_combination', 'radnr', 'datatype'])
)

# -----------------------------
# Step 3: main query
# -----------------------------
time_comb_data = concat_time_units(skjemadata_tbl, time_units)

skjemadata_with_time = skjemadata_tbl.mutate(time_combination=time_comb_data)

query = (
    skjemadata_with_time
    .join(
        mottak_subquery,
        (skjemadata_with_time['time_combination'] == mottak_subquery['time_combination'])
        & (skjemadata_with_time['ident'] == mottak_subquery['ident'])
        & (skjemadata_with_time['refnr'] == mottak_subquery['refnr']),
    )
    .join(
        datatype_subquery,
        (skjemadata_with_time['variabel'] == datatype_subquery['variabel'])
        & (skjemadata_with_time['time_combination'] == datatype_subquery['time_combination']),
    )
    .filter(datatype_subquery['datatype'] == 'int')
    .group_by([skjemadata_with_time['variabel'], datatype_subquery['radnr']] + [skjemadata_with_time[u] for u in time_units])
    .aggregate(verdi=skjemadata_with_time['verdi'].cast("int64").sum())
    .order_by(datatype_subquery['radnr'])
)
print(query.to_pandas())