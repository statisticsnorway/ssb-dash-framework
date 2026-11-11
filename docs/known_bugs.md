# Known bugs found while building the Altinn demo

These were found while wiring up [demo/altinn_app](../demo/altinn_app) against the
`ssb_dash_framework_testdata` Altinn tables. Each entry notes where the demo works around
the problem, so the workaround can be removed once the bug is fixed.

---

## 1. `enable_table_selector` is never acted on, which kills dataview switching

**Where:** [editor.py](../src/ssb_dash_framework/modules/data_editor/editor.py#L66)

`DataEditor.__init__` takes `enable_table_selector: bool = True`, but the parameter is never
read and `DataEditorTableSelector` is never instantiated. At the same time,
`toggle_view_visibility` takes `Input("dataeditortableselector", "value")`
([editor.py](../src/ssb_dash_framework/modules/data_editor/editor.py#L279)), and
`DataViewCustom` and `DataEditorTable` listen to the same id.

Because the component does not exist, Dash reports *"A nonexistent object was used in an
`Input` of a Dash callback"* and the callback never fires, so an app with more than one
dataview can never switch between them.

**Possible fix:** build the selector in `DataEditor.__init__` when `enable_table_selector`
is true, prepending it to the sidebar list:

```python
if enable_table_selector:
    sidebar = [
        DataEditorTableSelector(
            form_data_tables=[settings.form_data_table],
            starting_table=settings.starting_table,
        ),
        *(sidebar or []),
    ]
```

**Demo workaround:** `DataEditorTableSelector` is added explicitly to the `sidebar:` list in
`base.yaml`.

---

## 2. `update_refnr` crashes unless the ident/period pair has exactly one submission

**Where:** [editing_status_view.py](../src/ssb_dash_framework/modules/data_editor/modules/sidebar/editing_status_view.py#L170)

```python
refnr = self.fetcher.get_refnrs_by_period_ident(self.settings, ident, period)
if refnr is not None:
    skjema = refnr["skjema"].item()
    return refnr[self.settings.refnr_col].tolist()[0], skjema
```

`get_refnrs_by_period_ident` returns a DataFrame, and `Series.item()` only works when that
frame has exactly one row. The `is not None` guard never catches an empty frame, because an
empty DataFrame is still not `None`.

Both failure modes are reachable in the testdata:

- **0 rows** — ident `ATF2134660` with period `2026-03` (RA-0745 is yearly, so no such period).
- **2 rows** — ident `12111111` with period `2026-01` has an inactive superseded submission
  (`6bac48976d75`) plus the active one (`1043f5eb9897`).

Both produce `ValueError: can only convert an array of size 1 to a Python scalar`, which is
swallowed into a warning alert, leaving `refnr` unset and the form blank.

**Possible fix:** guard on emptiness and take the first row explicitly. The query is already
sorted by `dato_mottatt` descending, so the first row is the newest submission:

```python
if refnr is None or refnr.empty:
    return no_update, no_update
row = refnr.iloc[0]
return row[self.settings.refnr_col], row["skjema"]
```

Filtering on `aktiv` as well would be better still, so a superseded submission is never picked.

**Demo workaround:** none. The demo documents which ident/period pairs to use, and the
"Se innsendinger" modal can be used to pick a refnr by hand.

---

## 3. `handle_field_value_change` returns `None` and triggers a Dash 500

**Where:** [microlayout.py](../src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout.py#L135)

The callback body is wrapped in `if ctx.triggered_id and isinstance(ctx.triggered_id, dict):`
with no `else`, so whenever the callback is triggered by something that is not a
pattern-matching field id, the function falls off the end and implicitly returns `None`.
The callback declares a dict output, so Dash raises:

```
dash._grouping.SchemaTypeValidationError: ... Expected type: <class 'dict'>
Received value of type <class 'NoneType'>: None
```

This shows up as a 500 in the browser console on nearly every refnr change. It is harmless in
practice — the field values are loaded by a separate callback — but it is noisy and masks
real errors.

**Possible fix:** replace the implicit fall-through with an explicit no-op return (or
`raise PreventUpdate`) at the end of the function:

```python
return {item._id: no_update for item in ids}
```

---

## 4. `dynamic-list` leaks internals and has unstable column order

**Where:** [getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L210)
and [dynamic_list.py](../src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout_components/dynamic_list.py#L71)

Three separate problems in the same feature:

1. `get_dynamic_list` pivots with `columns="feltnavn"` hardcoded, rather than using a value
   from `EditorSettings`. It happens to match the Altinn testdata, but any other schema will
   raise a `KeyError`. A `field_label_col` setting (defaulting to `"feltnavn"`) would fix it.
2. The pivot index column `f"{settings.field_name_col}_parent"` (here `feltsti_parent`) is
   left in the result, so the grid shows a `Feltsti_parent` column full of raw field paths.
   It should be dropped before `to_dict`, or at least hidden in the `columnDefs`.
3. `DynamicListEditor` builds `columnDefs` by iterating a `set` of keys, so column order is
   non-deterministic between runs. Iterating the DataFrame columns in order would make the
   layout stable.

Separately, `DynamicListView.label` is required by the model but never rendered, so the grids
have no visible heading.

**Demo workaround:** each `dynamic-list` is preceded by an explicit `header` node to supply a
visible heading.

---

## 5. `get_field` returns `NaN` instead of `None` for NULL values

**Where:** [getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L61)

`return res.iloc[0, 0]` hands back whatever pandas stored, which for a SQL `NULL` is
`float('nan')` rather than `None`. Downstream comparisons such as
`if old_value != value` are then always true, because `nan != nan`, so a NULL field can be
"saved" with no actual change.

**Possible fix:** normalise before returning:

```python
value = res.iloc[0, 0]
return None if pd.isna(value) else value
```

---

## 6. `get_info_row_fields` queries the wrong column and the wrong identifier

**Where:** [getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L148)

> **Update (MacroModule work):** the first point below no longer applies. The query uses
> `variabel` and the schemas define `variabel`. The second point is still true: the ident
> column is compared with `refnr` at
> [getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L152).

Two issues in one query:

- It filters `t.filter(_.variabel == info_var.source_variable_name)`, but the `enhetsinfo`
  table defines the column as `variable` (see `schema_sqlite.sql`). Any inforow entry sourced
  from `enhetsinfo` raises an attribute error.
- It filters `t[settings.ident_col] == refnr`, comparing the ident column against a reference
  number. Even with the column name fixed, the filter cannot match.

**Possible fix:** make the lookup column configurable (the mapping-table settings already use
`mapping_match_column` for this kind of thing) and pass `ident` rather than `refnr` into the
ident filter.

**Demo workaround:** the `inforow:` block only uses `source: variableselector` entries, which
never touch the database.

---

## 7. `get_contact_info` is an unimplemented stub that raises

**Where:** [getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L79)

> **Update (MacroModule work):** this appears fixed. `get_contact_info` now reads the
> `kontaktinfo` table
> ([getter.py](../src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L77)),
> and `test_dataeditor.py` checks the result. The entry can likely be removed.

```python
def get_contact_info(self, refnr: str) -> ContactInfo:
    data = pd.DataFrame()
    row_data = data.to_dict(orient="records")[0]
```

`data` is always an empty DataFrame, so indexing `[0]` always raises `IndexError`. There is a
`kontaktinfo` table in the testdata that this could query.

**Demo workaround:** the contact-info button is left out of the `buttons:` list.

---

# Found while building the generic MacroModule

These were found while building the experimental
[MacroModule](../src/ssb_dash_framework/modules/macro_module/README.md). Workarounds in the
MacroModule are noted so they can be removed once the problem is fixed.

---

## 8. `AlertHandler.error` shows errors as warnings

**Where:** [alert_handler.py](../src/ssb_dash_framework/utils/alert_handler.py#L119)

```python
def error(cls, msg: str, ephemeral: bool | None = True, duration: int | None = 5):
    cls._add_alert(msg, "warning", ephemeral=ephemeral, duration=duration)
```

`error` adds the alert with the colour `"warning"`. The AlertHandler has no error variant
at all: no colour, no icon in `_map_icon`
([alert_handler.py](../src/ssb_dash_framework/utils/alert_handler.py#L365)) and no filter
button in the alert modal. Errors therefore look the same as warnings and cannot be filtered
out from them.

**Possible fix:** add an error variant (e.g. `"danger"`) with an icon, a CSS class and a filter
button, and use it in `error`.

---

## 9. `AlertHandler` can only be called while a callback is running

**Where:** [alert_handler.py](../src/ssb_dash_framework/utils/alert_handler.py#L108)

`_add_alert` uses `dash.set_props`, which raises
`MissingCallbackContextException: dash.callback_context.set_props is only available from a callback!`
outside a callback. Code that is shared between callbacks and plain Python (data handlers,
helpers, scripts, unit tests) can therefore not report through the AlertHandler without
crashing outside the app.

**Possible fix:** fall back to logging when there is no callback context.

**MacroModule workaround:** the unit tests monkeypatch `AlertHandler.warning`
([test_macro_module_data_handler.py](../tests/unittests/module_tests/macro_module/test_macro_module_data_handler.py)).

---

## 10. Lazy ibis tables do not survive the end of `with get_connection()`

**Where:** [connection.py](../src/ssb_dash_framework/utils/config_tools/connection.py#L38)

`get_connection()` lends out a connection for the duration of the `with` block. Pooled
Postgres (`set_postgres_connection`) and parquedit (`set_parquedit_connection`) give the
connection back when the block ends, so an ibis table expression returned from inside the
block points to a connection that is no longer usable. SQLite happens to work because it
opens a new connection per call. Nothing in the docs warns about this, and a design that
returns ibis tables from a data handler works in SQLite tests but fails in production.

**Possible fix:** document in `get_connection` and `docs/architecture.md` that results must
be executed (`.to_pandas()`/`.execute()`) inside the `with` block.

**MacroModule workaround:** data handlers return a pandas DataFrame (see
[ADR 0001](../src/ssb_dash_framework/modules/macro_module/adr/0001-module-owns-aggregation.md)).

---

## 11. `experimental/` cannot import modules directly

**Where:** [\_\_init\_\_.py](../src/ssb_dash_framework/__init__.py#L3)

The top-level package runs `from . import experimental` before any of its other imports, and
ruff's import sorting keeps it there. If `experimental/__init__.py` imports from
`..modules`, the import is circular (`cannot import name 'app_setup' from partially
initialized module`).

**Possible fix:** remove `from . import experimental` from the top-level package. Users import
`ssb_dash_framework.experimental` explicitly anyway.

**MacroModule workaround:** [experimental/\_\_init\_\_.py](../src/ssb_dash_framework/experimental/__init__.py)
resolves its names lazily with a module-level `__getattr__`.

---

## 12. Experimental modules are not registered for yaml configs

**Where:** [experimental/\_\_init\_\_.py](../src/ssb_dash_framework/experimental/__init__.py)
and [models.py](../src/ssb_dash_framework/config/models.py#L74)

A class is registered for yaml when it is defined, i.e. when its module is imported. The
package never imports experimental modules, so `type: MacroModule` in an app config fails
with `No module named 'MacroModule' found` unless the app first imports
`ssb_dash_framework.experimental` and touches the class (or imports it by name).

**Possible fix:** have `build_app_from_config` import `ssb_dash_framework.experimental` when
an unknown type is requested, or document the explicit import for experimental modules.

---

## 13. YamlLoadable subclasses defined inside a test break on the second backend

**Where:** [models.py](../src/ssb_dash_framework/config/models.py#L74)

Every `YamlLoadable` subclass registers itself by class name, and a second registration
raises `Module '<name>' is already registered`. The `db_backend` fixture runs every test once
per backend, so a handler or module subclass defined inside a test function passes on the
first backend and fails on the next.

**Possible fix:** document that test classes must be defined at module level, or let the
registry replace a class whose `__module__` and `__qualname__` are the same.

---

## 14. Test fixture only resets part of the VariableSelector state

**Where:** [conftest.py](../tests/unittests/conftest.py#L84) and
[set_variables.py](../src/ssb_dash_framework/setup/variableselector/set_variables.py#L108)

`clear_VariableSelector_variableselectoroptions` clears `_variableselectoroptions`, but not
`_time_unit`, `_ident`, `_refnr`, `_secondary_ident` or `_grouping_variables`. `apply_config`
only sets the values that are present, so a `VariableSelectorConfig` without `ident` keeps
the ident from an earlier test. Tests that depend on these values can pass or fail
depending on test order.

**Possible fix:** reset all the class variables in the fixture.

**MacroModule workaround:** the `selector` fixture in
[test_macro_module.py](../tests/unittests/module_tests/macro_module/test_macro_module.py)
saves, resets and restores them.

---

## 15. `VariableSelectorConfig.from_yaml` and `from_dict` expect the old `time_units` format

**Where:** [set_variables.py](../src/ssb_dash_framework/setup/variableselector/set_variables.py#L44)
and [L69](../src/ssb_dash_framework/setup/variableselector/set_variables.py#L69)

Both loop over `config["time_units"]` as a dict of `{name: frequency}`, but the field is a
single `TimeUnit(name, frequency)`. A config in the current format (as in
`demo/altinn_app/config/base.yaml`) iterates over the keys `name` and `frequency` and raises
`RuntimeError: The time unit you selected was invalid`. `from_dict` also raises `KeyError`
when `time_units` is missing. App configs loaded through `AppConfig` are not affected,
because they use pydantic validation directly.

**Possible fix:** delete the loops; `TimeUnit` already parses frequency strings.

---

## 16. The Altinn demo's time unit cannot parse yearly periods

**Where:** [base.yaml](../demo/altinn_app/config/base.yaml#L12)

The demo configures `frequency: month` for both RA-0187 (monthly) and RA-0745 (yearly). That
works as long as the period is only string-matched, but any module that parses the period
with `TimeUnit.parse`, such as the MacroModule's comparison period, fails for `2024`.

**Possible fix:** none in the demo while one time unit serves two frequencies. The
MacroModule has its own demo with a yearly time unit
([demo/macro_module](../demo/macro_module/app.py)).

---

## 17. `pinnedTopRowData` is not a property of this dash-ag-grid version

**Where:** [hardcoded_version.py.txt](../src/ssb_dash_framework/modules/macro_module/reference/hardcoded_version.py.txt#L600)

Using `Output(grid_id, "pinnedTopRowData")` makes the browser report *"Invalid prop for this
component"*. The hardcoded MacroModule does this, so its count row would not show if the code
were used again.

**Possible fix:** set it through grid options:
`dashGridOptions={..., "pinnedTopRowData": rows}`, as the generic MacroModule does.

---

## 18. The architecture test does not catch modules that write to other modules' components

**Where:** [test_architecture.py](../tests/unittests/test_architecture.py#L78)

`test_modules_are_independent` only checks imports. The hardcoded MacroModule wrote to
DataEditor's `"dataeditortableselector"` component
([hardcoded_version.py.txt](../src/ssb_dash_framework/modules/macro_module/reference/hardcoded_version.py.txt#L1362)),
which breaks the rule that modules only communicate through the variable selector, without
failing the test.

**Possible fix:** none simple, since component ids are strings. A convention that ids start
with `self.module_id` could be checked by inspecting the registered callbacks.

---

## 19. Parquedit tests emit ibis deprecation warnings

**Where:** ibis' DuckDB backend (`ibis/backends/duckdb/__init__.py`), reached through
`set_parquedit_connection`

Every query through the parquedit backend warns
`DeprecationWarning: fetch_arrow_table() is deprecated, use to_arrow_table() instead.` The
unit tests show these warnings (from DataEditor, the Altinn testdata checks and the
MacroModule's Altinn handler), although `AGENTS.md` requires the suite to pass without
warnings. The warning comes from ibis itself, not from the framework.

**Possible fix:** upgrade ibis once a release uses `to_arrow_table()`, or filter this specific
warning in the pytest configuration until then.

---

## 20. Documentation gaps

- [architecture.md](architecture.md#L135): the "Recommended test suite" section is empty,
  although `AGENTS.md` points to it for how tests should be written. [testing.md](testing.md)
  is also an empty file.
- [architecture.md](architecture.md#L123): the link text says `docs/datamodels/README.md`, but
  the file is `docs/datamodels.md` (the link target itself works).
- [architecture.md](architecture.md#L106) names ssb-parquedit as the standard backend, but
  `set_parquedit_connection`
  ([connection.py](../src/ssb_dash_framework/utils/config_tools/connection.py#L195)) is not
  exported, and only the tests use it.
- [datamodels.md](datamodels.md#L31) does not say that `indeks` is only the index within the
  innermost repeating group, and that outer indices are only found in `feltsti`
  (e.g. `/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/...`).
