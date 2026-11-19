# Edit a parquet file with the ParquetEditor

The **ParquetEditor** lets you change single values in a parquet file on Dapla. Your file
is never changed. Instead, every change is saved in a change log, together with the
reason for the change and a comment. When you are done, you export a new file with all
the changes.

Do the guide [Getting started: build your first app](getting_started.md) first.

You will learn:

- how to add a ParquetEditor to your app
- how to edit a value, and where the change is saved
- how to see all changes with the ParquetEditorChangelog
- how to connect the table to the variable selector
- how to use the edited data in your own code
- how to export the edited data to a new file

## Before you start

You need:

- A Jupyter service in Dapla Lab, with your team's bucket available under `/buckets/`.
  The ParquetEditor only works with paths that start with `/buckets/`.
- A parquet file that you want to edit. It should be in an `inndata` folder, for example
  `/buckets/produkt/my-statistic/inndata/data_p2024_v1.parquet`.

The file must follow these rules:

- **Some columns must identify each row.** For example `aar` and `orgnr` together. No two
  rows can have the same values in these columns. In this guide these columns are called
  the **id columns**.
- **Column names can not contain `.`, `/`, `-` or spaces.** Use `_` instead, for example
  `antall_ansatte`.
- **The file must have a normal index.** If you make the file with pandas, run
  `df = df.reset_index(drop=True)` before you save it.

In this guide we use the file from the example app:
`/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet`. Its id columns are
`aar` and `orgnr`. Replace the path and the column names with your own.

## Step 1: Add a ParquetEditor

Make a folder for your app, with two files.

`app.yaml`:

```yaml
app_settings:
  port: 8070
  stylesheet: lumen
  variableselector:
    ident: orgnr
    time_units:
      name: aar
      frequency: year
modules:
  tabs:
    - type: ParquetEditor
      statistics_name: Demo
      data_period: "2024"
      data_source: /buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet
      id_vars: ["aar", "orgnr"]
```

`app.py`:

```python
import os
from pathlib import Path

from ssb_dash_framework import AppConfig
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import main_layout

# 1. Read the app config. It sets up the app, the variable selector and the modules.
config_path = Path(__file__).parent / "app.yaml"
config = AppConfig(**config_parser_yaml(str(config_path)))
app, tab_list, window_list = build_app_from_config(config)

# 2. Build the layout and start the app.
app.layout = main_layout(window_list=window_list, tab_list=tab_list)

if __name__ == "__main__":
    app.run(
        debug=False,
        port=config.app_settings.port,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
```

These are the settings for the ParquetEditor:

| Setting | What it is |
| --- | --- |
| `statistics_name` | The name of your statistic. It is saved with every change. |
| `data_period` | The period you edit, for example `"2024"`. It is saved with every change. Write it in quotes, so it is read as text. |
| `data_source` | The path to the parquet file. It must start with `/buckets/`. |
| `id_vars` | The id columns. These columns can not be edited. |

**The id columns must also be fields in the variable selector, with the same names.** In
this example, `orgnr` is the `ident` and `aar` is the time unit. If you have more id
columns, for example `kvartal`, add them under `secondary_idents` or `grouping_variables`
in the `variableselector` block.

Run the app as in the getting started guide. You should see a tab with a pencil icon and
the name of your file. The tab shows your data in a table. You can sort and filter every
column.

The same module in Python looks like this. Put it in `tab_list`:

```python
tab_list.append(
    ParquetEditor(
        statistics_name="Demo",
        data_period="2024",
        data_source="/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet",
        id_vars=["aar", "orgnr"],
    )
)
```

## Step 2: Edit a value

1. Double-click on a cell. You can not edit the id columns.
2. Type the new value, and press `Enter`.
3. A window called *Reason for change* opens. It shows the column, the old value and the
   new value.
4. Choose a reason. The reasons are in Norwegian, for example *Statistisk gjennomgang*
   (statistical review) or *Kontakt med dataleverandør* (contact with the data provider).
5. Write a comment. The comment is required.
6. Click *Confirm*, or press `Enter` in the comment box.

You see the message *Prosesslogg oppdatert!* ("process log updated"). The change is now saved.

### Where is the change saved?

Your parquet file is not changed. The change is saved in a change log next to your data,
in a `temp/parqueteditor` folder. For the example file, the change log is:

```text
/buckets/produkt/editering-eksempel/inndata/temp/parqueteditor/test_p2024_v1-change-data-log.jsonl
```

Every time the ParquetEditor reads the file, it applies all changes from the change log.
So the table always shows your edited data.

Each line in the change log is one change. It has the old and the new value, which unit
(row) was changed, who changed it, when, the reason and the comment.

## Step 3: See all changes

Add a **ParquetEditorChangelog** to see all changes. Add it under `tabs` in `app.yaml`,
after the ParquetEditor:

```yaml
    - type: ParquetEditorChangelog
      data_source: /buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet
      id_vars: ["aar", "orgnr"]
```

Use the same `data_source` and `id_vars` as for the ParquetEditor.

Restart the app. A new tab, called *Changes* and the name of your file, shows every change
as text: the column, the unit, the old and new value, who made the change and the comment.

## Step 4: Connect the table to the variable selector

The ParquetEditor can **write** to the variable selector. Then other modules can react to
the row you click on.

Add `output` to the ParquetEditor in `app.yaml`:

```yaml
    - type: ParquetEditor
      statistics_name: Demo
      data_period: "2024"
      data_source: /buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet
      id_vars: ["aar", "orgnr"]
      output: ["aar", "orgnr"]
```

Now, when you click on a cell in the `orgnr` column, the value is written to the `orgnr`
field in the variable selector. The same goes for `aar`.

Two more settings are useful:

- `output_varselector_name`: Use this if a column has a different name than the field in
  the variable selector. The list must be in the same order as `output`. For example,
  `output: ["orgnr"]` and `output_varselector_name: ["foretak"]` writes the value of the
  column `orgnr` to the field `foretak`.
- `varselector_filtering: true`: The table filters itself when an id field in the variable
  selector changes. For example, when another module selects a unit, the table only shows
  that unit.

## Step 5: Use the edited data in your own code

`apply_edits` reads your parquet file, applies all changes from the change log and gives
you a pandas DataFrame. Use it when you need the edited data, for example in a figure.

Before the first change there is no change log. Then you read the file directly with
`pd.read_parquet`. `get_log_path` gives you the path to the change log, so you can check
if it exists.

In this step you add a figure in Python. Keep `app.yaml` from step 4, and replace the code
in `app.py` with this:

```python
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ssb_dash_framework import AppConfig
from ssb_dash_framework import FigureDisplay
from ssb_dash_framework import apply_edits
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import get_log_path
from ssb_dash_framework import main_layout

DATA_SOURCE = "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet"

# 1. Read the app config. It sets up the app, the variable selector and the modules.
config_path = Path(__file__).parent / "app.yaml"
config = AppConfig(**config_parser_yaml(str(config_path)))
app, tab_list, window_list = build_app_from_config(config)


# 2. Functions that read the edited data and make a figure.
def read_edited_data() -> pd.DataFrame:
    """Read the file with all changes applied."""
    if get_log_path(DATA_SOURCE).exists():
        return apply_edits(DATA_SOURCE)
    return pd.read_parquet(DATA_SOURCE)


def make_bars(aar: str, orgnr: str) -> go.Figure:
    """Bar chart with income and costs for every unit, with all edits applied."""
    data = read_edited_data()
    return px.bar(data, x="orgnr", y=["inntekter", "utgifter"], barmode="group")


# 3. Add the figure as a window.
window_list.append(
    FigureDisplay(
        label="Inntekter og utgifter",
        figure_func=make_bars,
        inputs=["aar", "orgnr"],
    )
)

# 4. Build the layout and start the app.
app.layout = main_layout(window_list=window_list, tab_list=tab_list)

if __name__ == "__main__":
    app.run(
        debug=False,
        port=config.app_settings.port,
        jupyter_server_url=os.getenv("JUPYTERHUB_HTTP_REFERER", None),
        jupyter_mode="tab",
        threaded=False,
    )
```

`inputs=["aar", "orgnr"]` makes the figure update every time you click on an `aar` or
`orgnr` cell in the table. So after you edit a value, click on the row to see the new
figure.

A similar app is in the repository, in
[demo/parqueteditor](https://github.com/statisticsnorway/ssb-dash-framework/tree/main/demo/parqueteditor).

## Step 6: Export the edited data

When you are done editing, export the data to a new file. Do this in a notebook, or in a
separate Python file, not in the app:

```python
from ssb_dash_framework import export_from_parqueteditor

export_from_parqueteditor(
    "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet",
    "/buckets/produkt/editering-eksempel/klargjorte-data/test_editert_p2024_v1.parquet",
)
```

The first path is your original file. The second path is the new file. The edited data
usually goes in the `klargjorte-data` folder.

`export_from_parqueteditor` does two things:

1. It writes the edited data to the new file.
2. It copies the change log to the `logg/prosessdata` folder of your bucket, so the
   changes are documented. For the example, the change log is saved as:

```text
/buckets/produkt/editering-eksempel/logg/prosessdata/klargjorte-data/test_editert_p2024_v1-change-data-log.jsonl
```

If the new file already exists, you get an error. Use `force_overwrite=True` if you want
to replace it.

## Troubleshooting

**`... only work with paths that starts with '/buckets/'`.**
Use the path that starts with `/buckets/`. Check that your team's bucket is available in
your Dapla Lab service.

**`... not in list of options`.**
One of the id columns is not a field in the variable selector. Add it to the
`variableselector` block, for example under `secondary_idents`.

**`Duplicate rows found based on subset ...`.**
The id columns do not identify each row. Add more id columns, so that every row is unique.

**`The column '...' contains a special character ...`.**
Rename the column in your file. Use `_` instead of `.`, `/`, `-` or spaces.

**`... you need to reset your dataframe index`.**
Run `df = df.reset_index(drop=True)` before you save the parquet file.

**`Process log not found ...` when you export.**
No changes have been made to this file yet, so there is nothing to export.

**`... already exists. Use force_overwrite=True to overwrite.`**
The new file, or its change log, already exists. Choose a new file name, or use
`force_overwrite=True`.

## Next steps

- [Connect to your data](connecting_to_data.md)
- [Edit form data with the DataEditor](dataeditor.md)
