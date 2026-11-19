# Connect to your data

Most apps read data from tables, for example tables in ParquEdit on Dapla or in a
database. This guide shows how your app connects to your data, and how your own code and
the modules use that connection.

Do the guide [Getting started: build your first app](getting_started.md) first.

You will learn:

- how to set up the **connection** with one of the ready-made functions
- how to read data with `get_connection`
- how to use the connection in your app
- how to make your own connection, if none of the ready-made ones fit

## How it works

An app has one shared **connection** to your data. You use two functions:

- A `set_..._connection` function tells the app where your data is. You run it once, at
  the top of `app.py`.
- `get_connection` gives you the connection when you need to read data. You use it inside
  your functions.

Modules that read from tables, such as the DataEditor, use the same connection. So you only
set it up once, and every part of the app uses it.

## Step 1: Choose a ready-made connection

Pick the function that matches where your data is stored:

| Your data is stored in | Use |
| --- | --- |
| ParquEdit tables on Dapla (recommended) | `set_parquedit_connection()` |
| A PostgreSQL database | `set_postgres_connection(database_url)` |
| A SQLite file | `set_sqlite_connection(path)` |

### ParquEdit (recommended on Dapla)

[ParquEdit](https://statisticsnorway.github.io/ssb-parquedit/) stores your team's tables
on Dapla. It finds its settings in your Dapla environment by itself, so you do not need
any arguments:

```python
from ssb_dash_framework import set_parquedit_connection

set_parquedit_connection()
```

### PostgreSQL

Give the address of the database. Do not write passwords in your code. Read them from an
environment variable instead:

```python
import os

from ssb_dash_framework import set_postgres_connection

set_postgres_connection(os.environ["DATABASE_URL"])
```

The address looks like this: `postgresql://user:password@host:5432/database_name`.

### SQLite

A SQLite database is a single file. This is useful for testing on your own machine:

```python
from ssb_dash_framework import set_sqlite_connection

set_sqlite_connection("my_data.sqlite")
```

### Where to put it

Set the connection at the top of `app.py`, right after the imports, before you create any
modules. Then the connection is ready before any module needs it.

The connection is always set in Python. This is also true when you use an app config
(a YAML file).

## Step 2: Read data with `get_connection`

Use `get_connection` inside a `with` block:

```python
from ssb_dash_framework import get_connection


def get_turnover(aar: str):
    with get_connection() as conn:
        t = conn.table("omsetning")
        return t.filter(t.aar == aar).to_pandas()
```

This is what happens:

1. `get_connection()` opens the connection. It is called `conn` inside the block.
2. `conn.table("omsetning")` points to the table `omsetning`. It does not read any data yet.
3. `t.filter(t.aar == aar)` keeps only the rows for the selected year.
4. `.to_pandas()` reads the data, and gives you a pandas DataFrame.
5. When the block ends, the connection is closed or given back.

`conn` is an [Ibis](https://ibis-project.org/) connection. With Ibis you write your
queries in Python, and the same code works for ParquEdit, PostgreSQL and SQLite. See the
Ibis documentation for more ways to filter, select and join tables.

Follow these rules:

- **Always use `with get_connection() as conn:`.** Do not call `get_connection()` without
  `with`.
- **Do all your work inside the block.** Return a DataFrame or another normal Python value.
  Do not keep `conn` or `t` after the block. The connection may be closed when the block
  ends.
- **Call `get_connection()` inside your function**, not at the top of the file. Then you
  get a fresh connection every time the module updates.
- **Filter in the query, before `.to_pandas()`.** Then you only read the rows you need,
  which is much faster for large tables.

## Step 3: Use the connection in your app

Here is the app from step 5 of the getting started guide, changed to read the data from a
table instead of from a DataFrame in the code. Change the table name `omsetning` and the
column names to match your own data.

```python
import os
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

from ssb_dash_framework import AppConfig
from ssb_dash_framework import FigureDisplay
from ssb_dash_framework import build_app_from_config
from ssb_dash_framework import config_parser_yaml
from ssb_dash_framework import get_connection
from ssb_dash_framework import main_layout
from ssb_dash_framework import set_parquedit_connection

# 1. Connect to your data.
set_parquedit_connection()

# 2. Read the app config. It sets up the app and the variable selector.
config_path = Path(__file__).parent / "app.yaml"
config = AppConfig(**config_parser_yaml(str(config_path)))
app, tab_list, window_list = build_app_from_config(config)


# 3. Functions that read the data and make the figures.
def turnover_per_unit(aar: str) -> go.Figure:
    """Bar chart with the turnover of every unit in the selected year."""
    with get_connection() as conn:
        t = conn.table("omsetning")
        selected = t.filter(t.aar == aar).to_pandas()
    return px.bar(selected, x="orgnr", y="omsetning", title=f"Turnover in {aar}")


def turnover_over_time(orgnr: str) -> go.Figure:
    """Line chart with the turnover of the selected unit for every year."""
    with get_connection() as conn:
        t = conn.table("omsetning")
        selected = t.filter(t.orgnr == orgnr).order_by("aar").to_pandas()
    return px.line(selected, x="aar", y="omsetning", title=f"Turnover for {orgnr}")


# 4. Add modules in Python.
tab_list.append(
    FigureDisplay(
        label="Turnover per unit",
        figure_func=turnover_per_unit,
        inputs=["aar"],
        output="orgnr",
        clickdata_func=lambda clickdata: clickdata["points"][0]["x"],
    )
)

window_list.append(
    FigureDisplay(
        label="Turnover over time",
        figure_func=turnover_over_time,
        inputs=["orgnr"],
    )
)

# 5. Build the layout and start the app.
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

What changed:

- `set_parquedit_connection()` is called before the app and the modules are created.
- The functions read the data with `get_connection()`, and only read the rows they need.

> **Tip:** Do you want to try this without access to ParquEdit? Make a small SQLite file
> from the example data in the getting started guide, and use `set_sqlite_connection`
> instead of `set_parquedit_connection`:
>
> ```python
> import sqlite3
>
> with sqlite3.connect("my_data.sqlite") as db:
>     data.to_sql("omsetning", db, if_exists="replace", index=False)
> ```

## More advanced: make your own connection

Use this only if none of the ready-made functions fit your data.

`set_connection` takes a function that gives an Ibis connection. Write the function with
`@contextmanager`, and use `yield` to give the connection:

```python
from contextlib import contextmanager

import ibis

from ssb_dash_framework import set_connection


@contextmanager
def my_connection():
    conn = ibis.duckdb.connect("my_data.duckdb")
    try:
        yield conn
    finally:
        conn.disconnect()


set_connection(my_connection)
```

Every time someone calls `get_connection()`, the app runs `my_connection`. The code before
`yield` opens the connection. The code after `yield` closes it when the `with` block ends.

`set_connection` tests your function once when you call it. If your function does not give
an Ibis connection, you get a `TypeError`.

## Troubleshooting

**`No connection has been set.`**
You called `get_connection()` before any `set_..._connection` function. Set the connection
at the top of `app.py`.

**`Currently this framework only supports connections based on ibis-framework backend objects`.**
Your own connection function gives something that is not an Ibis connection. Make sure it
uses `yield` with an Ibis connection, as in the example above.

**`Table not found` or a similar error.**
Check the table name. To see all tables, run this in a notebook:

```python
with get_connection() as conn:
    print(conn.list_tables())
```

## Next steps

- [Edit a parquet file with the ParquetEditor](parqueteditor.md)
- [Edit form data with the DataEditor](dataeditor.md)
