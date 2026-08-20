"""For å eksportere data fra ParquetEditor kjøres koden nedenfor."""

from ssb_dash_framework import export_from_parqueteditor

filsti = "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet"

export_from_parqueteditor(
    filsti,
    "/buckets/produkt/editering-eksempel/klargjorte-data/test_editert_p2024_v1.parquet",
)
