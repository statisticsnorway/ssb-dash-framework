# HB methodology implementation order

- Each numbered item below is one change. Do not combine items unless the dependency requires it. Every sub-point describes one clearly bounded implementation responsibility.
- In plan.md means this task has been added to plan.md and cannot be changed without updating the plan. Items in history of the plan.md are not to be changed.

1. **Define the HB public contract**
   - Add the common HB input schema: `unit_id`, canonical `period`, numeric `value`, optional `strata`, and configured selector context.
   - Add `HBDataHandlerMeta.get_hb_dataframe(...)`.
   - Add schema validation for all six `TimeUnit` frequencies and duplicate `unit_id`/`period` rejection.
   - Add unit tests for each canonical frequency format, configured-frequency mismatches, required columns, types, uniqueness, and clear errors.
   - Do not add Altinn queries or Vaskify calls.

2. **Implement canonical period resolution**
   - Add `resolve_hb_comparison_periods`.
   - Accept canonical strings for YEAR (`YYYY`), HALF_YEAR (`YYYY-1`/`YYYY-2`), QUARTER (`YYYY-Q1`–`YYYY-Q4`), MONTH (`YYYY-MM`), WEEK (`YYYY-Www`), and DAY (`YYYY-MM-DD`).
   - Use `TimeUnit` to derive `(t-1, t)` from the selected period.
   - Keep the resolution policy isolated so it can be changed without changing the data-handler contract.
   - Address the WEEK parsing and QUARTER formatting issues listed in `Issues.md` without changing the canonical input strings.
   - Test `(t-1, t)` rollover behavior and canonical output for all six frequencies, plus invalid and frequency-mismatched inputs.

3. **Retrieve configured Altinn records and select active submissions**
   - Identify the existing Altinn access pattern.
   - Add `AltinnHBDataHandler` implementing `HBDataHandlerMeta`.
   - Use the documented Altinn form, field, unit/period, and selector-context mapping. Follow [altinnapiclient-documentation.md](altinnapiclient-documentation.md).
   - Read through the configured `get_connection()` and Ibis table-query pattern; retrieve only the configured form, selected field, candidate records, and required columns.
   - Select active submissions for each unit and requested period using the policy approved in `plan.md`. The existing `active_no_duplicates_refnr_list` helper filters `aktiv`, orders by `dato_mottatt` descending, and keeps one row per `ident`; if that policy is adopted, apply it separately per period or use period-aware grouping, never across both periods together.
   - Test configured form/field selection, active and missing submissions, and the approved multiple-active policy.

---- In plan.md ----

4. **Normalize Altinn records into the common HB DataFrame**
   - Resolve repeated and nested field matches using the documented field metadata (`feltsti`, `feltnavn`, `dybde`, and `indeks`). Reject ambiguity rather than silently taking the first match or aggregating.
   - Convert the selected `verdi` to numeric, preserve missing values as missing, and reject values that cannot be converted.
   - Return one validated common HB row per unit and period, preserving only selector context required by the module.
   - Test numeric conversion, repeated/nested ambiguity, output schema, and uniqueness.

5. **Add deterministic test data access**
   - Add `FakeHBDataHandler` for deterministic module tests.
   - Make it record the requested variable, periods, and optional stratum.
   - Return validated common-schema data.
   - Keep it out of the production Altinn path.
   - Test that it can exercise the module without a backend connection.

6. **Add the Vaskify dependency and adapter boundary**
   - Add the supported `ssb-vaskify` runtime dependency.
   - Add `run_hb_vaskify`.
   - Construct `Detect(hb_input_dataframe, id_nr="unit_id")`.
   - Add structural preflight checks for exactly two distinct canonical periods, matching input period levels, Vaskify-compatible required dtypes, and a present `strata` column when configured.
   - Pass `value`, `period`, comparison periods, optional stratum, and explicit public API defaults (`pu=0.5`, `pa=0.05`, `pc=20`, `percentiles=(0.25, 0.75)`, `flag="flag_hb"`, `output_format="wide"`, `output_scope="all"`) to `Detect.hb(...)`.
   - Do not filter zero, negative, or missing values or recreate Vaskify eligibility/calculation rules in the framework.
   - Keep Vaskify argument mapping out of the Altinn adapter and Dash callbacks.
   - Add mocked tests for exact Vaskify arguments and preflight failures.

7. **Normalize Vaskify results**
   - Add `normalize_hb_result`.
   - Validate the returned Vaskify shape.
   - Preserve stable identifiers, source context, comparison values, period context, diagnostics, `ratio`, `median_ratio`, limits, and `flag_hb`.
   - Reconcile results with the full handler input so units without Vaskify diagnostics remain visible.
   - Keep flagged (`1`), calculated/unflagged (`0`), and not-comparable (missing diagnostics/flag) states distinct.
   - Use verified Vaskify return behavior to distinguish no eligible population from an error; do not treat an unverified empty result as “no outliers.”
   - Add unit tests for valid, incomplete, missing, not-comparable, and invalid results.

8. **Create the ModuleBase shell**
   - Add `HBMethod` under `src/ssb_dash_framework/modules/`.
   - Set `label`, `icon`, and the handler before `ModuleBase.__init__()`.
   - Implement `layout()` with controls, run button, loading state, errors, empty state, result store, and graph placeholders.
   - Implement `module_callbacks()` using `self.module_id` for every component ID.
   - Use descriptive IDs such as `hb_run_button`, `hb_result_graph`, `hb_error_message`, and `hb_result_store`.
   - Test construction, lifecycle, unique IDs, and tab/window placement.

9. **Connect selector inputs to the run action**
   - Read the selected HB variable and canonical period from `VariableSelector` at callback time.
   - Validate required selector configuration during construction.
   - Resolve comparison periods with `resolve_hb_comparison_periods`.
   - Call `AltinnHBDataHandler.get_hb_dataframe(...)` with the explicit named HB arguments.
   - Do not store per-user selector values on the module instance.
   - Test handler arguments and missing selector configuration.

10. **Execute and display an HB run**
   - On the explicit run action, call the handler, `run_hb_vaskify`, and `normalize_hb_result` in that order.
   - Store the normalized result for the current run.
   - Build the result figure from normalized Vaskify columns.
   - Display ratio, median ratio, limits, and candidate state without reimplementing HB logic.
   - Route failures through `AlertHandler` and log context without row-level sensitive data.
   - Test successful runs, handler failures, Vaskify failures, warning-only paths, and empty or not-comparable data.

11. **Add click-to-selector behavior**
   - Put the stable `unit_id` in Plotly `customdata`.
   - Read the identifier from click data, never from hovertext, labels, or row positions.
   - Update the configured `VariableSelector` output.
   - Read the stored result only; do not call the handler or Vaskify on selection.
   - Test selecting multiple candidates and selecting no point.

12. **Export and register the module**
   - Export `HBMethod` through `ssb_dash_framework.modules` and the package top-level API where required.
   - Register the module with the existing YAML configuration mechanism.
   - Document constructor and handler configuration keys.
   - Search for imports of the experimental prototype before removing or redirecting it.
   - Test normal imports and YAML registration.

13. **Add integration and reference-result tests**
   - Test the installed Vaskify package with deterministic input data.
   - Verify the actual result shape, `ratio`, `median_ratio`, limit and flag columns, and explicit call defaults.
   - Add reference-result cases for positive, zero, negative, missing, flagged, unflagged, and not-comparable observations.
   - Verify the package's return behavior when no unit has eligible values and when it logs warnings without raising.
   - Keep mathematical algorithm tests in Vaskify, not in framework helpers.

14. **Add demo and browser coverage**
   - Add or update a demo that imports and configures `HBMethod`.
   - Use deterministic test data or the configured Altinn path as appropriate.
   - Verify app startup, run action, result display, and click-to-selector flow.
   - Add demo-specific E2E steps under `tests/e2e/hooks/` when needed.

15. **Complete user documentation**
   - Document Altinn handler setup and required configuration.
   - Document the common DataFrame schema and canonical period requirements for all six `TimeUnit` frequencies.
   - Document the selected period `t` and the `TimeUnit`-based `t-1` assumption.
   - Document result flags, missing/not-comparable states, and limitations.
   - Document click-to-selector behavior and the no-write boundary.
   - Update the module/API documentation without duplicating implementation logic.

16. **Validate completed tasks**
   - Run only the tests explicitly listed for the active task in `plan.md`, after that task is complete.
   - Run a broader test session or E2E coverage only when explicitly scheduled in `plan.md`.
   - Confirm that no source data is edited and that all failures remain visible.

17. **Remove temporary design documents**
   - Before integrating to `main`, remove `architecture_design_detailed.md` and `ssb-vaskify-design.md` after their lasting decisions and issue context are recorded in `architecture.md` and `Issues.md`.
   - User will decide what to keep in the end.
