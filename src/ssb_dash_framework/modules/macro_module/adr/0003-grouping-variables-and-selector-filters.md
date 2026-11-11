# Grouping variables come from the data handler; matching selector options act as filters

The grouping variables a MacroModule can show are those declared by its data handler, optionally narrowed by the module's `grouping_variables` argument. Variable selector grouping options are not a source of grouping columns: a selector option whose name matches a shown grouping variable becomes a filter on the macro table and observation list, and non-matching options are ignored. We chose this because apps already use selector grouping variables for unrelated purposes (e.g. `altinnskjema` in the Altinn demo), so requiring every selector grouping variable to be a data column would break existing apps.

## Considered Options

- **Match or fail**: raise at startup for non-matching selector options. Rejected because it breaks apps where other modules own those options.
- **Pass non-matching values to the handler as context** (e.g. the form from `altinnskjema`). Rejected for now because handler results would depend on hidden UI state; it remains a possible extension. The Altinn handler takes its form as a constructor argument instead.
