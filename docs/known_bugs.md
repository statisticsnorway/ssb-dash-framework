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

```python
def get_contact_info(self, refnr: str) -> ContactInfo:
    data = pd.DataFrame()
    row_data = data.to_dict(orient="records")[0]
```

`data` is always an empty DataFrame, so indexing `[0]` always raises `IndexError`. There is a
`kontaktinfo` table in the testdata that this could query.

**Demo workaround:** the contact-info button is left out of the `buttons:` list.

---
