# Evaluate Pydantic for HB validation

**Scope:** Evaluation only. No HB behavior or validation code was changed.

## Recommendation

Do not migrate HB validation wholesale to Pydantic. Keep the pandas-based common
DataFrame contract and the Altinn- and Vaskify-specific runtime checks at their
current boundaries. Continue using Pydantic for structured configuration where
it adds a clear schema; introduce an HB-specific configuration model only if
that configuration becomes a distinct serialized input with a real validation
need.

This follows the boundary-based convention proposed in
[FRAMEWORK-VALIDATION-001](./Issues.md): use Pydantic for structured
configuration, explicit validation results for user-correctable UI input, and
typed exceptions for invalid data or API contracts. The issue is still proposed,
not an approved mandate to convert existing code.

## Assessment by boundary

| Boundary | Current responsibility | Pydantic fit | Recommendation |
|---|---|---|---|
| Common HB DataFrame contract | `validate_hb_dataframe` checks required columns, duplicate columns, identifier and period values, numeric values, configured frequency, and unique `(unit_id, period)` rows. Missing numeric values are allowed. | A model can validate that a field is a DataFrame, but not its schema or vectorized contents by default. Custom validation would still need to call or reproduce the existing pandas checks. | Keep the shared validator. Do not model each row as a Pydantic object. |
| HB configuration and module input | `TimeUnit` and `VariableSelectorConfig` already use Pydantic. `HBMethod` also checks selector names and their relationship to the live `VariableSelector` state. | Pydantic is a good fit for static, structured configuration. Live registry and Dash-state checks depend on runtime state and do not become static schema rules by wrapping them in a model. | Keep existing Pydantic configuration models; keep live selector checks at module initialization. Do not add a wrapper model without a concrete config boundary. |
| Altinn-specific checks | The adapter validates source records, exact field-path selection, period-scoped active submissions, answer ambiguity, numeric conversion, and strata coverage and values. | Static form and field-path configuration could be modeled if loaded from an external configuration source. Retrieved record checks depend on source data, joins, and unit-period grouping. | Keep retrieval and record normalization checks in the Altinn adapter. Consider Pydantic only for a separately serialized static configuration, if one is introduced. |
| Vaskify preflight and output | Checks cover the common input contract, comparison-period pair and frequency, requested periods in the data, strata requirements, and Vaskify result schema and identifiers. | Pydantic supports custom cross-field validators, but period/data relationships and result membership still require explicit DataFrame-aware logic. | Keep method-specific checks in the Vaskify boundary. A Pydantic model would not replace the core checks. |

## Evidence and trade-offs

### Pandas integration

In the selected workspace environment, Pydantic 2.14.3 and pandas 3.1.1 were
available. A Pydantic model with a plain `pd.DataFrame` field failed schema
generation. With `arbitrary_types_allowed=True`, Pydantic accepted the
DataFrame instance but also accepted one with the wrong columns. Enforcing the
HB contract in that model would still require a custom validator that invokes
the current pandas checks.

The current validator uses DataFrame and Series operations for duplicate
columns, required fields, dtypes, periods, and duplicate unit-period pairs.
That is a direct fit for the tabular input and preserves vectorized checks.
Creating a Pydantic object for every row would add per-record model validation
without eliminating cross-row checks. No performance benchmark was run, so no
quantitative performance claim is made.

### Cross-field and boundary rules

Some HB invariants depend on multiple inputs or records:

- The two comparison periods must be distinct, canonical, and have a compatible
  frequency.
- The requested periods must correspond to periods in the input DataFrame.
- Configured strata must be present and consistent for each unit.
- Vaskify output identifiers must satisfy the input/result contract.
- Altinn selection and answer rules depend on source fields and grouped
  unit-period records.

Pydantic model validators could host custom implementations of some of these
rules, but the logic would remain custom and DataFrame-aware. Moving it into a
generic model would obscure which boundary owns the check rather than simplify
it.

### Error reporting

Pydantic can provide structured errors with field locations. That is useful
for configuration errors, but it does not automatically make runtime failures
clearer to HB users. The module currently routes run failures through its
existing alert and logging path; any migration would need to map validation
errors to safe, user-appropriate messages and avoid exposing sensitive input
values. It could also change the exception shape relied on by callers and
tests.

### Repeated validation

The current Altinn normalization calls `validate_hb_dataframe`. The production
flow then calls Vaskify, whose input preflight invokes that validator, and
`normalize_hb_result` repeats the input preflight. The Vaskify result checks
also run after execution and again during normalization. These checks serve
different boundaries, but the common contract is currently evaluated multiple
times in one run.

A Pydantic wrapper that validates the same DataFrame while leaving those checks
in place would add another validation layer. Any future consolidation should
first assign one owner to each invariant and preserve checks needed at
independent trust boundaries; changing that ownership is outside this
evaluation.

## Suggested migration scope

1. Keep `validate_hb_dataframe` and the Altinn/Vaskify boundary checks as
   explicit runtime validators.
2. Keep Pydantic for structured static configuration. Add an HB-specific
   configuration model only if a concrete serialized configuration contract
   needs it.
3. Keep runtime checks that depend on the live `VariableSelector` state at the
   module boundary.
4. If validation ownership is later changed, first document which boundary
   guarantees each invariant and avoid running equivalent checks redundantly.
5. Do not migrate code until the user approves a specific scope.