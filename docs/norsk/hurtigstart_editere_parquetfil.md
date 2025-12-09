# Hurtigstart parquetfil

I denne veiledning er målet at du skal få satt opp en enkel app for å editere en parquet fil, og få se hvordan du eksporterer den editerte filen når du er ferdig.

## Appen

Nedenfor er kode du kan kopiere til din egen .py fil eller notebook, det eneste du trenger å endre er listen over 'id_variabler' og 'filstien' til parquet filen din.

'id_variabler' er nøkkelvariabler som tilsammen identifiserer en unik rad i datasettet ditt og brukes for å kunne loggføre endringer du gjør.

Når du kjører koden vil det dukke opp en lenke i bunnen som du kan klikke på for å åpne appen og starte med editeringen.

I den appen har du modulene 'ParquetEditor' og 'ParquetEditorChangelog' satt opp, og du har et utgangspunkt for å utvide med flere moduler om du ønsker det. Mer om hvordan du gjør dette finner du i andre veiledninger.

```python
import os

from ssb_dash_framework import ParquetEditor
from ssb_dash_framework import ParquetEditorChangelog
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables
import plotly.express as px

port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug")

id_variabler = ["aar", "orgnr"] # Endre denne
filsti = "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet" # Endre denne

set_variables(id_variabler)

parquet_editor = ParquetEditor(
    statistics_name="Demo",
    id_vars=id_variabler,
    data_source=filsti,
    output=id_variabler, # Optional
    output_varselector_name=id_variabler # Optional
)

parquet_changelog = ParquetEditorChangelog(
    id_vars=id_variabler,
    file_path=filsti,
)

tab_list = [parquet_editor, parquet_changelog]

window_list = []

app.layout = main_layout(window_list, tab_list)

if __name__ == "__main__":
    app.run(debug=True, port=port, jupyter_server_url=domain, jupyter_mode="tab")
```

## Eksport

For å eksportere filen når du er ferdig med å editere skal du bruke funksjonen 'export_from_parqueteditor'. Dette sikrer at det opprettes en logg fil som inneholder endringene på nåværende tidspunkt, og at denne lagres på riktig sted.

Slik kan du lett kan vite hvordan loggen så ut når du gjorde eksporten.

```python
from ssb_dash_framework import export_from_parqueteditor

export_from_parqueteditor(filsti, "/buckets/produkt/editering-eksempel/klargjorte-data/test_editert_p2024_v1.parquet")
```
