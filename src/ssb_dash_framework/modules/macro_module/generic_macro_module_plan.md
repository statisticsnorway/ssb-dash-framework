# Plan: generic MacroModule

Status: implemented (experimental). Terms follow [GLOSSARY.md](GLOSSARY.md) and [docs/GLOSSARY.md](../../../../docs/GLOSSARY.md). User documentation is in [README.md](README.md).

## Changes made during implementation

- **Data handlers return a pandas DataFrame, not an ibis table.** A lazy ibis table is tied to the `get_connection()` connection, which pooled Postgres and parquedit return when the handler's block ends. ADR 0001 is updated. As a result, the Altinn handler pivots in pandas, so the SQLite string-function risk below no longer applies.
- **`hardcoded_version.py` moved to `reference/hardcoded_version.py.txt`.** The yaml tests and docgen import every `.py` file under `src/`, and its class name `MacroModule` clashed with the generic module in the yaml registry.
- **`experimental/__init__.py` resolves its names lazily** with a module `__getattr__`. The top-level package imports `experimental` before its modules, so a direct import is circular.
- **`MacroModule` got a `label` argument**, so several instances can have different tab names.
- **The macro table's pinned Totalt row is set through `dashGridOptions`**, because this dash-ag-grid version has no `pinnedTopRowData` prop.

## Goal

A generic version of `hardcoded_version.py` for drilling down from a **macro table** (aggregated value variables per group, selected period vs comparison period) to an **observation list**. From there an observation is sent to the variable selector so other modules can investigate it.

Priorities: readable, short, easy for a person to extend. The module should fit in one `.py` file. Data handlers live in separate files.

## Non-goals (first version)

- Hardcoded-only features:
  - foretak/bedrift toggle
  - NACE letter groups
  - `consolidated` flag
  - latin-1 decoding
  - "re-fetch every row for these units"
  - output to `dataeditortableselector`
- Prefix/hierarchy levels. Users define one grouping variable per level, or write their own handler.
- Pivot-heatmap layout.
- Caching.
- Passing selector context to handlers.
- Nested repeating groups as observations.
- Smarter instance matching across periods.
- Changes to `hardcoded_version.py`, the existing `MacroModule` JS namespace or the `macromodule-*` CSS.
- A larger expansion of the demo data. That is planned, but not in this scope.

## File layout (`modules/macro_module/`)

| File | Content |
|---|---|
| `__init__.py` | Exports `MacroModule`, `MacroModuleDataHandler`, `AltinnMacroModuleDataHandler` |
| `macro_module.py` | `MacroModule(ModuleBase)`: layout, callbacks, pure aggregation/compare helpers |
| `data_handler.py` | `MacroModuleDataHandler(YamlLoadable, ABC)`: data model, validation, duplicate hook |
| `altinn_data_handler.py` | `AltinnMacroModuleDataHandler`: default handler for the Altinn data model |
| `README.md` | User docs: configuration, YAML, writing your own handler, limitations |
| `GLOSSARY.md` | Module terms |
| `adr/` | Decision records for the module |
| `reference/hardcoded_version.py.txt` | Untouched reference, stored as text so the test suite and docgen never import it. |

Export only through `ssb_dash_framework.experimental`, never top-level. The test suite requires `__init__.py` in every source directory.

## Data model (owned by `MacroModuleDataHandler`)

The module's model is deliberately separate from the storage model. Handlers convert between the two.

One row per observation per period:

| Column | Type | Required | Notes |
|---|---|---|---|
| `ident` | string | yes | Unit identifier |
| `instance` | string | no | Repeating-group instance key. Key = `ident` (+ `instance`) |
| `name` | string | no | Shown in the observation list |
| each grouping variable | string | yes | Code. Null or not in codelist → `"Ukjent"` |
| each value variable | numeric | yes | Cast to float64 by the module |

The fixed names live as class attributes on the base class (`ident_column = "ident"`, `instance_column = "instance"`, `name_column = "name"`). Everything references these attributes so handlers can override them later if needed (Q12).

### Base class contract

```python
class MacroModuleDataHandler(YamlLoadable, ABC):
    ident_column: ClassVar[str] = "ident"
    instance_column: ClassVar[str] = "instance"
    name_column: ClassVar[str] = "name"

    value_variables: dict[str, str]  # name -> label, display order
    grouping_variables: list[str]    # display order

    @abstractmethod
    def fetch_observations(self, period: str) -> pd.DataFrame:
        """Build the query in ibis and call .to_pandas() inside the handler's own
        `with get_connection()` block (see ADR 0001)."""

    def get_codelists(self, period: str) -> dict[str, dict[str, str]]:
        """Optional. grouping variable -> {code: label} in display order.
        The module fetches codelists for the selected period only and uses them for both periods.
        Missing variable -> fallback to sorted distinct codes in data."""
        return {}

    def last_updated(self, period: str) -> str | None:
        return None

    def resolve_duplicates(self, data: pd.DataFrame, period: str) -> pd.DataFrame:
        """Optional hook. Default: AlertHandler warning if duplicates exist, returns data unchanged
        (validate then raises). Override to resolve duplicates; this is the intended extension point."""

    def validate(self, data: pd.DataFrame, period: str) -> None:
        """Raises ValueError naming handler, period and column."""

    def get_observations(self, period: str) -> pd.DataFrame:
        """Concrete, final: fetch -> resolve_duplicates -> validate. The module only calls this."""
```

### Validation rules

- **Structural problems raise an error.** These are:
  - a missing `ident` column
  - a missing grouping column or value column
  - a value column that isn't numeric
  - a grouping, `ident`, `instance` or `name` column that isn't a string
  - a duplicate key within a period
- **Content problems become findings.** Null codes and codes outside the codelist go into an `"Ukjent"` group, and an AlertHandler warning gives the count.
- **At `__init__`, the module checks** that:
  - there is at least one value variable
  - no variable names clash with the fixed column names
  - each requested grouping variable is declared by the handler

  It raises a `ValueError` if any of these fail.

## MacroModule

```python
MacroModule(data_handler: MacroModuleDataHandler,
            grouping_variables: list[str] | None = None,  # default: handler's list
            comparison_lag: int = 1,
            label: str = "Makromodul")
```

- All component IDs are `f"{self.module_id}-..."`.
- `from_yaml` resolves `data_handler` by class name and kwargs, as `DataEditor` does.
- The period comes from `VariableSelector.get_timevar`. The comparison period is `TimeUnit.parse(...).subtract(lag)`.
- **Selector grouping variables (Q21a):**
  - A selector grouping option whose name matches a grouping variable shown by the module becomes an `Input` filter. A non-empty value filters both the macro table and the observation list.
  - Non-matching options are ignored.
  - Grouping columns come only from the handler and the module argument.
- **Error handling in callbacks:**
  - catch, `logger.exception`, `AlertHandler.error(handler, period, message)`
  - return empty tables

### Sidebar (Norwegian labels)

- **Grupper etter**: multi-select of grouping variables. Defaults to the first one. Columns always follow the declared order.
- **Verdivariabler**: multi-select of value variables. Defaults to all, in declared order.
- **Visning**: Prosentendring / Periodens sum / Differanse.
- **Sammenlign med N perioder tilbake**: number input, min 1, default `comparison_lag`.
- **Vis tomme rader**: checkbox. It adds codelist combinations that have no observations in either period (the cartesian product of the selected codelists), shown as zeros.
- Last-updated text, if the handler returns one.

### Macro table (flat)

- **Columns:**
  - the grouping columns, showing code and label, in codelist order with `Ukjent` last
  - **Antall**: observation count in the selected period
  - one column per selected value variable, in the chosen display mode
- **Value cell styling:**
  - heatmap colouring, keeping the hardcoded thresholds
  - tooltip showing both periods' values and the difference
- **Pinned top row Totalt:** the sum over all groups.
- **Clicking a value cell** opens the observation list for that row's group, scoped to that value variable. Clicking a grouping cell, Antall or Totalt does nothing.

### Observation list

- **Contents:** observations whose key belongs to the clicked group in either period, using the grouping values from each observation's own period.
- **Columns, in order:**
  1. `ident`
  2. `name`
  3. `instance`
  4. status
  5. each grouping variable, showing the current value. A coloured cell plus a tooltip show the comparison value if it changed.
  6. for each value variable: current, comparison and difference (contribution to the cell), with the clicked variable first
- **Status values:**

  | Status | Meaning |
  |---|---|
  | `Ny` | new in data |
  | `Inn` | moved into the group |
  | `Ut` | moved out of the group |
  | `Borte` | gone from data |
  | (blank) | unchanged |

  `Inn`/`Ut`/`Ny`/`Borte` are the glossary's Entry/Exit.
- **Sorting:** by the clicked variable's contribution. Descending if the cell increased, ascending if it decreased. A "Snu sortering" button reverses it.
- **Selecting an observation:**
  1. Clicking a row opens a confirm popup.
  2. "Velg" writes `ident` to the selector's ident option.
  3. It also writes any column matching a configured secondary ident.
  4. It writes nothing to other modules' components.

### Pure helpers (unit-testable, no Dash)

The module should have small functions such as:
- `aggregate(current, comparison, group_by, value_vars, filters)` → pandas
- `observation_list(current, comparison, group, value_var)` → pandas
- `apply_codelists(...)`, which also handles Ukjent and empty rows

The callbacks only wire these together.

### JavaScript

Add a small new namespace in `assets/dashAgGridFunctions.js` for value formatting, heatmap styling, changed-group highlighting and status styling. The existing `MacroModule` namespace stays for the hardcoded version.

## AltinnMacroModuleDataHandler

```python
AltinnMacroModuleDataHandler(
    skjema: str,
    value_variables: dict[str, str] | list[str],          # feltnavn
    grouping_variables: list[str],                         # enhetsinfo.variabel, else skjemadata.feltnavn
    codelists: dict[str, list[str] | dict[str, str] | dict] | None = None,  # list, {code: label}, or {klass: id, level: n}
    repeating_group: str | None = None,                    # e.g. "/NyEngSpredUtsGroup"
    exclude_instances: dict[str, list[str]] | None = None, # e.g. {"NyEngSpredUtsID": ["TOTAL_ROW"]}
)
```

- **Connection and filtering:**
  - Reads through `get_connection()`.
  - Filters `iso_periode == period` (the selector string is passed through) and `skjema`.
- **Duplicates:** `resolve_duplicates` keeps only submissions where `skjemamottak.aktiv` is true. If an ident still has several, the one with the latest `dato_mottatt` wins. The docstring must state that overriding this method is the intended way to resolve duplicates (Q23).
- **Value variables:** taken from `skjemadata` by `feltnavn`, with `verdi` cast to float. A non-numeric value raises an error.
- **Default mode (per unit):** values are summed per ident across all group instances, including nested ones.
- **`repeating_group` mode (per instance):**
  - An observation is (ident, instance).
  - The instance is the path prefix `"{repeating_group}/{i}"`.
  - Values in nested groups are summed into their top-level instance.
  - Grouping variables can be fields inside the instance.
  - Instances are matched across periods on the instance path. Renumbering between periods shows as `Ny`/`Borte`; this is a documented limitation.
- **Excluded instances:** `exclude_instances` drops any instance where the named field has one of the listed values.
- **Grouping variables:** looked up in `enhetsinfo.variabel` (`verdi`) first, then `skjemadata.feltnavn`.
- **Name column:** `name` comes from `enhetsinfo` `enhetsNavn`.
- **Codelists:** Klass entries use `ssb-klass-python` (already a dependency) for the selected period. The same codelist is used for both periods.
- **SQLite risk (resolved):** instance paths are extracted in pandas, after `.to_pandas()`, so no backend-specific string functions are needed.
- **YAML:** all constructor arguments are plain YAML types.

## Test data additions (`ssb_dash_framework_testdata/altinn/enhetsinfo.sql`)

- Add `naring` and `kommune` rows for the three RA-0745 units in 2024–2026, which is 18 rows.
- One unit changes `naring` between 2025 and 2026, so the demo shows an entry and an exit.
- Do not touch `skjemadata`/`skjemamottak`. `test_altinn_testdata.py` asserts 443 skjemadata rows, and the DataEditor tests rely on single refnrs.

## Demo

`demo/macro_module/app.py`:
- seeds SQLite from the test data, like `altinn_app`
- uses a yearly time unit
- imports from `ssb_dash_framework.experimental`
- runs two tabs:
  1. RA-0745 per unit, grouped by `naring`/`kommune`
  2. RA-0745 per instance on `/NyEngSpredUtsGroup`, excluding `TOTAL_ROW`

The e2e hook `tests/e2e/hooks/macro_module.py` sets the period to 2026, clicks a value cell and checks that the observation list fills in.

## Tests (`tests/unittests/module_tests/macro_module/`)

- **Pure helpers, using a stub handler over an in-memory DuckDB:** aggregation, the display modes, Ukjent, empty rows, the comparison lag, entry/exit statuses, instance keys and sort direction.
- **Base class:** each validation error message, default duplicate warning followed by a raised error, and the codelist fallback.
- **`AltinnMacroModuleDataHandler` over the `backends.py` fixture (sqlite/parquedit/postgres):**
  - several active submissions resolved by latest `dato_mottatt` (in-memory fixture)
  - inactive submissions ignored
  - per-unit sums
  - per-instance mode
  - `exclude_instances`
  - enhetsinfo vs skjemadata grouping
- **Module:** the `__init__` checks, building the layout, registering callbacks, and the YAML round-trip.
- **Regenerate** `docs/yaml_reference.md` (required by `test_yaml_reference_is_up_to_date`).

## Docs

- `modules/macro_module/README.md`: usage, YAML example, how to write a handler (minimal example), the duplicate hook, limitations.
- Keep both glossaries up to date as terms change.

## Discrepancies found (report, do not fix here)

- `docs/architecture.md`:
  - "Recommended test suite" is empty.
  - It links `docs/datamodels/README.md`, which doesn't exist; the file is `docs/datamodels.md`.
  - It mentions `*MetaDataHandler` naming, but no module in `src/` uses it.
- `set_parquedit_connection` is not exported, although the architecture names parquedit as the standard backend.
- `docs/datamodels.md` doesn't say that `indeks` is only the innermost index, or that outer indices exist only in `feltsti`.
- `VariableSelectorConfig.from_yaml`/`from_dict` treat `time_units` as a dict of name→frequency, which doesn't match `TimeUnit`.
- `docs/known_bugs.md` #6 says the `enhetsinfo` column is `variable`, but the schema uses `variabel`.

## Suggested implementation order

1. `data_handler.py` with its tests.
2. Pure helpers in `macro_module.py` with tests.
3. `altinn_data_handler.py`, the test data rows and the backend tests. Check SQLite string functions first.
4. Layout, callbacks and JS.
5. The experimental export, YAML and `yaml_reference.md`.
6. Demo, e2e hook, README.
7. `uvx nox --session=tests`, then `--session=e2e`.
