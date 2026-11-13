# Known bugs

These were found while building [demo/altinn_app](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/demo/altinn_app)
against the `ssb_dash_framework_testdata` Altinn tables, and while writing the guides in
[docs/guides](guides/README.md). Where a demo or a guide works around a problem, the entry
says so, so the workaround can be removed once the bug is fixed.

The entries are grouped by area. The numbers are only for reference.

## DataEditor

### 1. `enable_table_selector` is never acted on, which kills dataview switching

**Where:** [editor.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/editor.py#L66)

`DataEditor.__init__` takes `enable_table_selector: bool = True`, but the parameter is never
read and `DataEditorTableSelector` is never instantiated. At the same time,
`toggle_view_visibility` takes `Input("dataeditortableselector", "value")`
([editor.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/editor.py#L279)), and
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

**Workaround:** `DataEditorTableSelector` is added explicitly to the `sidebar:` list in
`demo/altinn_app/config/base.yaml` and in the DataEditor guide.

### 2. Saving a field can overwrite every field in the form

**Where:** [core_models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/utils/core_models.py#L409)

`StandardDataHandler.update_field_value` only treats the table as "long" when
`settings.field_name_col == "variabel"`. For any other field name column, such as `feltsti`
in the standard Altinn model, `UpdateSkjemadata.update_ibis` builds:

```sql
UPDATE skjemadata
SET verdi = '<new value>'
WHERE refnr = '<refnr>'
AND ident = '<ident>'
```

There is no filter on the field, so the new value is written to **every field of the form**.
Today this is hidden because the checks in entry 3 fail first for most setups, but it will
destroy data as soon as those checks pass.

**Possible fix:** always filter on the field name column, using the column from the settings
instead of the hardcoded `variabel`:

```python
update_query += f"\nAND {settings.field_name_col} = '{self.variable}'"
```

`UpdateSkjemadata` needs to receive `field_name_col` for this.

### 3. Saving is tied to the NØKU data model

**Where:** [core_models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/utils/core_models.py#L228)

Every save in `UpdateSkjemadata.update_ibis` does NØKU-specific work that the documented
standard model in [datamodels.md](datamodels.md) does not support:

- `_check_datatype` always queries a `datatyper` table (period column, `variabel`,
  `datatype`). The table is not part of the standard model or the test data, so the query
  fails.
- `_validate_ident` requires the ident to be a 9-digit number, and to exist in `enhetsinfo`
  with an `aar` column. The test data idents (`12222222`, `ATF2134661`) are not 9 digits, and
  its `enhetsinfo` has `iso_periode`, not `aar`.
- If the `UPDATE` matches no rows, `_insert_ibis` inserts into a hardcoded
  `core_skjemadata` table, and only works with a Postgres connection pool.

As a result, saving fails in `demo/altinn_app` and for any statistic that is not NØKU.

**Possible fix:** move the NØKU-specific validation and insert logic into a NØKU data
handler that inherits from `StandardDataHandler`, and keep `StandardDataHandler` limited to
the documented standard model.

### 4. Values with a single quote break saving

**Where:** [core_models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/utils/core_models.py#L398)

The `UPDATE` and `INSERT` statements are built with f-strings, for example
`SET {self.column} = '{self.value}'`. A value that contains `'`, such as a comment like
`Kunden's tall`, produces invalid SQL. It is also an SQL injection risk.

**Possible fix:** use parameterised queries, or build the update with Ibis expressions.

### 5. The editing status shows a false error on every load

**Where:** [getter.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L221)
and [editing_status_view.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/sidebar/editing_status_view.py#L274)

`SidebarMeta.update_form_active_status` is declared to return `bool`, and
`DataEditorSidebarEditingStatus` treats a falsy return value as a failure. But
`StandardDataHandler.update_form_active_status` returns `None`. The callback also runs when
a form is loaded, so every load shows the alert *"Kunne ikke oppdatere aktiv-status for
&lt;refnr&gt;"*, even though nothing failed.

**Possible fix:** return `True` after a successful update in
`StandardDataHandler.update_form_active_status`, and only call it when the user changes the
checkbox.

### 6. `dynamic-list` leaks internals and has unstable column order

**Where:** [getter.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L196)
and [dynamic_list.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout_components/dynamic_list.py#L71)

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

**Workaround:** each `dynamic-list` in `demo/altinn_app` is preceded by an explicit `header`
node to supply a visible heading.

### 7. `get_field` returns `NaN` instead of `None` for NULL values

**Where:** [getter.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L37)

`return res.iloc[0, 0]` hands back whatever pandas stored, which for a SQL `NULL` is
`float('nan')` rather than `None`. Downstream comparisons such as
`if old_value != value` are then always true, because `nan != nan`, so a NULL field can be
"saved" with no actual change.

**Possible fix:** normalise before returning:

```python
value = res.iloc[0, 0]
return None if pd.isna(value) else value
```

### 8. `get_info_row_fields` filters the ident column on the refnr

**Where:** [getter.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L138)

For inforow entries with a table as `source`, the query filters
`t[settings.ident_col] == refnr`, comparing the ident column against a reference number. The
filter never matches, so the card is always empty.

**Possible fix:** pass `ident` rather than `refnr` into the ident filter.

**Workaround:** the `inforow:` blocks in `demo/altinn_app` and in the DataEditor guide only
use `source: variableselector` entries, which never touch the database.

### 9. `get_history` is a stub

**Where:** [getter.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/default_getter/getter.py#L74)

`StandardDataHandler.get_history` always returns an empty DataFrame, so the
`DataEditorHistory` window is always empty.

**Possible fix:** implement it against the change log of the standard model, or document
that history needs a custom data handler.

### 10. Custom support tables only load if `DataEditorSupportTables` is the first button

**Where:** [supporting_table.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/helper_buttons/supporting_table.py#L87)

The callback listens to the hardcoded id `DataEditorSupportTables-0-modal`. The number in
the id comes from a counter that is shared with the other helper buttons, so when
`DataEditorHistory` is created first (as in `demo/altinn_app`), the modal is
`DataEditorSupportTables-1-modal` and the callback never fires.

**Possible fix:** build the id from the instance's own `module_number`.

### 11. `DataEditorTable` filters on hardcoded column names

**Where:** [table_view.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/data_view/table_view.py#L136)

The table filters on columns named after the time unit in the variable selector, plus the
hardcoded columns `skjema` and `refnr`, instead of the columns in `EditorSettings`. With
`demo/altinn_app` (time unit `periode`, column `iso_periode`) the filter fails.

**Possible fix:** use `period_col`, `form_name_col` and `refnr_col` from the settings.

### 12. The form name field must be called `altinnskjema`

**Where:** for example [editor.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/editor.py#L280)
and [microlayout.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout.py#L132)

The DataEditor and its parts look up the variable selector field `altinnskjema` by name in
many places. If the app uses another name, construction fails with
`'altinnskjema' not in list of options`.

**Possible fix:** add a setting to `EditorSettings`, for example
`form_varselector_name: str = "altinnskjema"`, and use it everywhere.

**Workaround:** the DataEditor guide tells users to use the name `altinnskjema`.

### 13. The `tabs` component requires a `tabs` key that is never used

**Where:** [models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout_components/models.py#L158)

`Tabs` declares `tabs: list[Tab]` as required, but `create` only renders `children`. Users
have to write `tabs: []` and put the tabs in `children`.

**Possible fix:** render `tabs`, or make `tabs` optional and document `children`.

### 14. A `checklist` with more than one option is never saved

**Where:** [models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/microlayout/microlayout_components/models.py#L452)

With one option, the checklist gets the pattern-matching id
`{"comp_id": ..., "aio": ...}`. With more options, it gets a plain string id, which the
save callback does not match.

**Possible fix:** use the pattern-matching id in both branches.

### 15. The test data has form statuses the DataEditor rejects

**Where:** [skjemamottak.sql](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework_testdata/altinn/skjemamottak.sql)
and [sidebar/meta.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/modules/sidebar/meta.py#L17)

15 rows in the test data have the status `'Ny'`. `RefnrStatus.status` only allows
`Under arbeid`, `Ferdig` and `Ubehandlet`, so the editing status sidebar shows an error for
those forms.

**Possible fix:** decide which status values the standard model allows, and align the test
data and the model.

### 16. The DataEditor data handler base class is not importable, and has an unclear name

**Where:** [data_editor/meta.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/meta.py#L16)

Users who want to use the DataEditor with their own data must write a data handler that
inherits from `FetcherMeta`. Two problems:

- `FetcherMeta` is only importable from `ssb_dash_framework.modules.data_editor`, not from
  `ssb_dash_framework`. This goes against the rule in [architecture.md](architecture.md)
  that everything a user works with should be a top-level import.
- The name does not match the concept. The guides and [GLOSSARY.md](../GLOSSARY.md)
  call it a **data handler**, the ready-made implementation is called
  `StandardDataHandler`, and [architecture.md](architecture.md) calls the pattern
  `*MetaDataHandler`. "Fetcher" also hides that the class writes data, not only fetches it.

**Possible fix:** export `FetcherMeta` from `ssb_dash_framework`. Consider adding a clearer
name, for example `DataEditorDataHandler`, and keep `FetcherMeta` as an alias so existing
code keeps working.

**Note:** the DataEditor guide already imports `FetcherMeta` from `ssb_dash_framework`, so
that import fails until this is fixed.

## Connections

### 17. `set_parquedit_connection` is not importable from `ssb_dash_framework`

**Where:** [connection.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/utils/config_tools/connection.py#L195)

`set_parquedit_connection` is defined next to `set_sqlite_connection` and
`set_postgres_connection`, but unlike them it is not exported from
`ssb_dash_framework.utils.config_tools`, `ssb_dash_framework.utils` or `ssb_dash_framework`.

**Possible fix:** add it to the three `__init__.py` files and their `__all__` lists.

**Note:** the getting started, connection and DataEditor guides import
`set_parquedit_connection` from `ssb_dash_framework`, so that import fails until this is
fixed.

## ParquetEditor

### 18. The *Cancel* button in the "Reason for change" window does nothing

**Where:** [parquet_editor.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/parquet_editor.py#L215)

The button `{module_number}-cancel-edit` has no callback. Because the window uses
`backdrop="static"`, the user can not close it without confirming the change. The edited cell
also keeps the new value in the table.

**Possible fix:** add a callback that closes the window and restores the old value in the
table data.

### 19. `apply_edits` fails when there is no change log

**Where:** [parquet_editor.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/parquet_editor.py#L837)

`apply_edits` reads the change log without checking that it exists, so it raises
`FileNotFoundError` before the first edit is made. `ParquetEditor.get_data` checks this
itself, but users calling `apply_edits` directly (as in `demo/parqueteditor`) do not.

**Possible fix:** return `pd.read_parquet(parquet_path)` when the change log does not exist.

**Workaround:** the ParquetEditor guide checks `get_log_path(...).exists()` before calling
`apply_edits`.

## Configuration and setup

### 20. `from ssb_dash_framework import *` fails

**Where:** [\_\_init\_\_.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/__init__.py#L112)

`__all__` lists `NspekControlViewTab` and `NspekControlViewWindow`, which do not exist. The
module imports `NspekControlView` instead. A star import raises `AttributeError`.

**Possible fix:** replace the two names with `NspekControlView` in `__all__`.

### 21. Unknown keys under `app_settings` are silently ignored

**Where:** [models.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/config/models.py#L92)

Unknown keys in a module block are rejected with a helpful error, but `AppSettings` uses
pydantic's default, which ignores unknown keys. A typo such as `stylsheet: lumen`, or a key
that does not exist such as `connection:`, is dropped without a warning.

**Possible fix:** set `model_config = {"extra": "forbid"}` on `AppSettings`.

### 22. `VariableSelectorConfig.from_yaml` expects an old `time_units` format

**Where:** [set_variables.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/setup/variableselector/set_variables.py#L44)

`from_yaml` loops over `time_units` as a `{name: frequency}` mapping, but `time_units` is now a
`TimeUnit` with `name` and `frequency` keys, as used in the app config. A file in the current
format fails.

**Possible fix:** remove the conversion loop, and let `TimeUnit` parse the frequency, as it
already does for the app config.

### 23. `VariableSelectorConfig` can only be created once per Python process

**Where:** [variableselector.py](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/setup/variableselector/variableselector.py#L527)

Creating a `VariableSelectorConfig` registers its fields globally. Creating it a second time,
for example when a notebook cell is run again, raises
`This option title already exists`. It must also be created before any module, because the
modules look up their fields when they are created.

**Possible fix:** skip fields that already exist with the same settings, instead of raising.

**Workaround:** the getting started guide tells notebook users to restart the kernel.
