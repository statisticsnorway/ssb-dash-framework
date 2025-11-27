# Hurtigstart parquetfil

I denne veiledning er målet at du skal få satt opp en enkel app for å editere en parquet fil.


```python
import os

from ssb_dash_framework import ParquetEditor
from ssb_dash_framework import ParquetEditorChangelog
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_variables


port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "darkly")

id_variabler = ["aar", "orgnr"]
filsti = "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet"

set_variables(id_variabler)

parquet_editor = ParquetEditor(
    id_vars=id_variabler,
    file_path=filsti,
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
