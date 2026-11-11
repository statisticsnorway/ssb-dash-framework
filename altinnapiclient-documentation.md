# Altinn access pattern and HB adapter notes

## What this repository provides

The framework does not implement a direct Altinn HTTP/API client. Its existing
Altinn integration reads tables produced in the Altinn data model through a
configured database connection. The framework's connection layer is based on
Ibis; connection configuration and lifecycle are handled by
[`connection.py`](./src/ssb_dash_framework/utils/config_tools/connection.py).
The project's direct dependencies do not include a dedicated Altinn API client.

The Altinn schema documented by the framework is the default model generated
from `ssb-altinn-form-tools`; see [`docs/datamodels.md`](./docs/datamodels.md)
and its [schema diagram](./docs/datamodels/altinn.d2). This package expects the
backend or deployment to provide access to those tables. It does not fetch
submissions from Altinn itself.

## Database access

`set_connection()` configures a connection factory, and `get_connection()`
opens that configured connection as an Ibis backend. The common access pattern
is to get a table with `conn.table(...)`, filter and select columns with Ibis,
then execute the query or convert the result to pandas:

```python
with get_connection() as conn:
    submissions = conn.table("skjemamottak")
    active_submissions = submissions.filter(submissions.aktiv == True)
    active_submission_dataframe = active_submissions.to_pandas()
```

The Altinn demo uses the same connection abstraction, but seeds the bundled
Altinn testdata into SQLite with `set_sqlite_connection()`; see
[`demo/altinn_app/app.py`](./demo/altinn_app/app.py). This demonstrates local
database access, not an Altinn API connection.

## Existing Altinn-related code

### Active submission helper

[`active_no_duplicates_refnr_list`](./src/ssb_dash_framework/utils/core_query_functions.py)
reads `skjemamottak`, filters to rows where `aktiv` is true, sorts by
`dato_mottatt` descending, and keeps the first row for each `ident`. It can
also filter by `skjema` and additional columns, then returns unique `refnr`
values.

This helper's duplicate policy is therefore **latest active submission per
identifier**, not an error on multiple active submissions. It does not group
by period while dropping duplicate identifiers. If used for both comparison
periods at once, it can retain only the latest period's submission for an
identifier. Call it separately per period or implement period-aware grouping.
The HB adapter plan must decide whether this established policy is appropriate
for HB or whether ambiguous active submissions should instead be rejected.

### Data-editor reads

[`StandardDataHandler`](./src/ssb_dash_framework/modules/data_editor/default_getter/getter.py)
and [`FormGetterCached`](./src/ssb_dash_framework/modules/data_editor/default_getter/form_cache.py)
read the configured form-data table through `get_connection()`. The editor's
[`EditorSettings`](./src/ssb_dash_framework/modules/data_editor/utils.py)
configures the form-data table and the columns for submission reference,
form, identifier, period, field name, and field value.

`get_refnrs_by_period_ident()` filters `skjemamottak` by identifier and period,
orders by latest receipt, and returns submission references with their `aktiv`
and status values. It returns the rows; it does not itself select an active
submission. `get_form_status()` reads `aktiv` and `status` for a specific
`refnr`.

`get_field()` filters a form by `refnr` and the configured field-name column.
If more than one row matches, the existing editor logs an error and uses the
first value. That is a legacy UI behavior, not a safe HB ambiguity policy; the
HB adapter should follow the explicit repeated/nested-field rule agreed for HB.

### Other Altinn integration

[`AltinnDataCapture`](./src/ssb_dash_framework/experimental/modules/altinn_data_capture.py)
is an experimental receipt-count visualization. It is limited to a database
type named `altinn_default` and uses a custom `database.query(...,
partition_select=...)` interface for its queries. It is not a general,
production Altinn client or an implementation of the HB data-handler contract.

[`AltinnFormParqueditHandler`](./src/ssb_dash_framework/modules/data_editor/default_getter/form_tools_parquedit_handler.py)
is a `ParquEdit`-based data-editor handler. Its Altinn-specific methods access
editing history and update fields or reception metadata; it is not the common
read adapter for the HB module.

## Relevant table relationships

The documented schema identifies these fields:

| Table | Relevant columns | Use |
|---|---|---|
| `enheter` | `iso_periode`, `skjema`, `ident` | Unit/form membership for a period |
| `skjemamottak` | `iso_periode`, `skjema`, `ident`, `refnr`, `dato_mottatt`, `aktiv`, `status` | Submission metadata and active flag |
| `skjemadata` | `iso_periode`, `skjema`, `ident`, `refnr`, `feltsti`, `feltnavn`, `verdi`, `dybde`, `indeks` | Individual response values and nested/repeated-field metadata |

The schema diagram relates `enheter` to `skjemamottak` by
`(iso_periode, skjema, ident)`, then relates `skjemamottak` to `skjemadata` by
those same columns plus `refnr`. Use the selected submission's `refnr` when
retrieving answers so values from a different delivery are not mixed in.

`skjemadata.verdi` is stored as text. `feltsti`, `feltnavn`, `dybde`, and
`indeks` carry field identity and nesting/repetition context; a field-name
match alone may not uniquely identify one answer. `enhetsinfo` has a separate
`variabel`/`verdi` representation, so do not assume its field naming is the
same as `skjemadata`.

## Implications for `AltinnHBDataHandler`

The HB adapter is a source adapter: it should use the configured connection to
read the selected form and field, resolve submissions for each requested
period, convert the selected `verdi`, and return the common HB DataFrame. It
must not call Vaskify or use UI/editor behavior as a substitute for source
selection.

Before implementation, the plan needs to settle or explicitly reuse the
existing latest-active rule, identify the configured field using the agreed
field-path/field-name semantics, and define how repeated or nested matches
are handled. Preserve only selector context required by HB, and reject
unresolved ambiguity rather than silently selecting the first field row.
