# MacroModule (experimental)

Drill down from aggregated values to the observations behind them. The **macro table** sums value variables per group for the selected period and a **comparison period**. Clicking a value cell opens the **observation list**: the observations that contribute to that cell in either period, sorted by how much each one contributed to the change. Confirming an observation sends its ident to the variable selector, so other modules can investigate it.

Terms are defined in [GLOSSARY.md](GLOSSARY.md), and design decisions are in [adr/](adr/).

The module is experimental and may change without notice. Import it explicitly:

```python
from ssb_dash_framework.experimental import AltinnMacroModuleDataHandler
from ssb_dash_framework.experimental import MacroModule
```

## Quick start

The variable selector needs a time unit and an ident.

```python
VariableSelectorConfig(
    ident="ident",
    time_units={"name": "periode", "frequency": "year"},
    grouping_variables=["naring"],  # optional, see "Filtering from the variable selector"
)

handler = AltinnMacroModuleDataHandler(
    skjema="RA-0745",
    value_variables={"NyEngArbAreal": "Areal ny eng"},
    grouping_variables=["naring", "kommune"],
    codelists={"naring": {"klass": 6, "level": 5}},
)
tab_list.append(MacroModule(handler, label="Makro"))
```

The same in yaml. The app must import `ssb_dash_framework.experimental` before the config is loaded, so the classes are registered:

```yaml
- type: MacroModule
  label: Makro
  data_handler:
    type: AltinnMacroModuleDataHandler
    skjema: RA-0745
    value_variables: {NyEngArbAreal: Areal ny eng}
    grouping_variables: [naring, kommune]
```

A runnable example with both observation modes is in [demo/macro_module/app.py](../../../../demo/macro_module/app.py).

## Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `data_handler` | required | A `MacroModuleDataHandler` that supplies the observations. |
| `grouping_variables` | all declared by the handler | The grouping variables to offer, in display order. |
| `comparison_lag` | `1` | How many periods back the comparison period starts out as. The user can change it in the module, e.g. 12 to compare a month with the same month last year. |
| `label` | `"Makromodul"` | The label of the tab or window. |

## Using the module

- **Grupper etter**: the grouping variables that make up the rows. Columns always follow the declared order.
- **Verdivariabler**: the value variables shown as columns.
- **Visning**: percent change, the selected period's sum, or the difference. Hovering over a value shows both periods and the change.
- **Sammenlign med N perioder tilbake**: the comparison lag.
- **Vis tomme rader**: shows every combination of codes, including groups without observations.
- **Totalt** (pinned row) sums all groups. **Antall** counts observations in the selected period.
- Codes that are missing or not in the codelist are grouped as **Ukjent**, and a warning tells how many observations that affects.

In the observation list:

| Column | Content |
| --- | --- |
| Status | `Ny` (new in the data), `Inn` (moved into the group), `Ut` (moved out of the group), `Borte` (gone from the data), blank if unchanged. |
| Grouping variables | The value in the selected period. Highlighted, with the comparison value as tooltip, if it changed. |
| Value variables | The value in each period, and the observation's contribution to the change of the clicked cell (`bidrag`). |

**Snu sortering** reverses the order. Clicking a row and then **Velg** writes the ident to the variable selector, plus any configured secondary idents that are columns in the data.

## Filtering from the variable selector

A grouping variable that also exists as a grouping variable in the `VariableSelectorConfig` becomes a filter: when the selector has a value, the module only shows observations with that code. Selector grouping variables the module does not know are ignored, so other modules can keep using them (ADR 0003).

## The data model

Data handlers deliver one pandas DataFrame per period, with one row per observation:

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `ident` | string | yes | The unit. |
| `instance` | string | no | A repeating group instance. With it, an observation is identified by `ident` and `instance`. |
| `name` | string | no | Shown in the observation list. |
| each grouping variable | string | yes | The code. |
| each value variable | numeric | yes | Summed in the macro table. |

Other columns are allowed and ignored. Every fetch is validated: a missing column, a wrong type or two rows with the same key raises an error that names the handler, the period and the column, and the module shows it as an alert.

## Writing a data handler

Subclass `MacroModuleDataHandler`, declare the variables and implement `fetch_observations`. Do the heavy filtering and pivoting in ibis, and call `.to_pandas()` inside the `with get_connection()` block (ADR 0001).

```python
import pandas as pd

from ssb_dash_framework import get_connection
from ssb_dash_framework.experimental import MacroModuleDataHandler


class MyHandler(MacroModuleDataHandler):
    def __init__(self) -> None:
        self.value_variables = {"omsetning": "Omsetning"}  # {name: label}
        self.grouping_variables = ["naring", "fylke"]

    def fetch_observations(self, period: str) -> pd.DataFrame:
        with get_connection() as conn:
            t = conn.table("statistikkfil")
            t = t.filter(t.aar == period).select(
                ident="orgnr", name="navn", naring="naring", fylke="fylke", omsetning="omsetning"
            )
            return t.to_pandas()
```

Optional methods:

- `get_codelists(period)` returns `{grouping variable: {code: label}}`. The codelist decides the row order, and codes outside it become "Ukjent". The selected period's codelists are used for both periods. Without a codelist, the codes found in the data are sorted.
- `last_updated(period)` returns a text shown above the filters.
- `resolve_duplicates(data, period)` is the place to resolve rows that share a key. The default only warns, and validation then fails.

For hierarchical codes such as NACE levels, declare one grouping variable per level (e.g. `naring2`, `naring5`) in the handler.

## AltinnMacroModuleDataHandler

Reads the [Altinn data model](../../../../docs/datamodels.md) through `get_connection()`:

- Only active submissions (`skjemamottak.aktiv`) of `skjema` count. If a unit has several, the latest `dato_mottatt` wins.
- Value variables are `skjemadata` fields matched on `feltnavn`. Values must be numeric; a text value raises an error.
- Grouping variables are read from `enhetsinfo.variabel`, otherwise from `skjemadata.feltnavn`. The name comes from `enhetsNavn` in `enhetsinfo`.
- `codelists` per grouping variable: a list of codes, a `{code: label}` dict, or `{klass: <id>, level: <level>}` to fetch a Klass codelist valid on 31 December of the selected period's year.

Repeating groups (ADR 0004):

- By default an observation is a unit, and a field that occurs in several group instances is summed.
- With `repeating_group="/NyEngSpredUtsGroup"`, each top-level instance (e.g. `/NyEngSpredUtsGroup/9`) is an observation. Value variables, and grouping variables not found in `enhetsinfo`, are then read from fields inside the instance, and values in nested groups are summed into it.
- `exclude_instances={"NyEngSpredUtsID": ["TOTAL_ROW"]}` drops instances where a field has one of the values. Use it for summary rows, which are otherwise counted twice.

## Limitations

- Observations for both periods are loaded into memory, which suits form data but not millions of rows per period.
- Instances are matched across periods on their path. If a form numbers instances differently between periods, they show as `Ny` and `Borte`.
- Nested repeating groups cannot be observations on their own.
- Data is fetched again on every change; there is no caching.
