# The module owns aggregation; data handlers only translate and validate

The MacroModule has its own data model: one row per observation, with a fixed `ident` column, optional `instance`/`name` columns, string grouping columns and numeric value columns. `MacroModuleDataHandler` subclasses convert their storage model (e.g. the long Altinn model) into this model and return it as a pandas DataFrame. The module does all filtering, aggregation, period comparison and observation-list logic itself. We chose this "thin handler" over handlers that compute macro tables and observation lists themselves, so that a handler can be written in a few lines, the comparison logic lives in one tested place, and bad data fails early in a shared `validate` step.

## Considered Options

- **Thick handler** (`get_macro_table`, `get_observation_list`): more freedom for backend-specific optimisation, but every handler would reimplement grouping, comparison, entry/exit and sorting, and behaviour would drift between handlers.
- **Handler returns a lazy ibis table**: keeps aggregation in the database, but an ibis table is tied to the connection from `with get_connection()`. Pooled Postgres and parquedit return that connection when the handler's block ends, so the module would query a closed connection.
- **Module passes its connection to the handler**: keeps full pushdown, but ties every handler to the app's `get_connection()` backend and requires every module operation to work in SQLite, Postgres and DuckDB.

## Consequences

- Handlers should do the heavy work (filtering, long-to-wide pivot) in ibis and call `.to_pandas()` inside their own connection block. The module aggregates observation-level data in pandas, which suits form data but not tables with millions of rows per period.
- Column names are fixed class attributes on the base class, so handlers can be allowed to override them later without changing the module.
- The base class's `get_observations` (fetch → resolve duplicates → validate) is the only entry point the module uses, so custom handlers cannot skip validation.
