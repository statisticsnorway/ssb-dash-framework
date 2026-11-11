# The module owns aggregation; data handlers only translate and validate

The MacroModule has its own data model: one row per observation, with a fixed `ident` column, optional `instance`/`name` columns, string grouping columns and numeric value columns. `MacroModuleDataHandler` subclasses convert their storage model (e.g. the long Altinn model) into this model, and the module does all filtering, aggregation, period comparison and observation-list logic itself. We chose this "thin handler" over handlers that compute macro tables and observation lists themselves, so that a handler can be written in a few lines, the comparison logic lives in one tested place, and bad data fails early in a shared `validate` step. ibis still pushes the aggregation down to the backend.

## Considered Options

- **Thick handler** (`get_macro_table`, `get_observation_list`): more freedom for backend-specific optimisation, but every handler would reimplement grouping, comparison, entry/exit and sorting, and behaviour would drift between handlers.

## Consequences

- Column names are fixed class attributes on the base class, so handlers can be allowed to override them later without changing the module.
- The base class's `get_observations` (fetch → resolve duplicates → validate) is the only entry point the module uses, so custom handlers cannot skip validation.
