# HB methodology implementation order

- Each numbered item below is one change. Do not combine items unless the dependency requires it. Every sub-point describes one clearly bounded implementation responsibility.
- In plan.md means this task has been added to plan.md and cannot be changed without updating the plan. Items in history of the plan.md are not to be changed.
- The word "stage" refers to the grouping that corresponds to a numbered item in the implementation order. this is repeated in plan.md to keep context clear.
- Bookmark is used when the model are struggeling, but there should not be any unimbuigity as a number is very clear.

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

3. **Identify the existing Altinn access pattern and policy**
   - Document the project's existing database/Ibis access pattern and the Altinn source-table relationships relevant to HB in [altinnapiclient-documentation.md](altinnapiclient-documentation.md).
   - Decide the HB policy for multiple active Altinn submissions
   - Map the configured Altinn form, field, and selector context

4. **Retrieve configured Altinn candidate records**
   - Add an HB-local retrieval component for the configured form, selected HB variable, and requested periods using the approved exact-`feltsti` mapping. Do not implement `HBDataHandlerMeta` yet; its method promises the final validated HB DataFrame.
   - Read through the configured `get_connection()` and Ibis table-query pattern. Scope `enheter` by `skjema` and `iso_periode`, then join to `skjemamottak` and `skjemadata` using the documented keys, including `refnr` for the answer join.
   - Retain source keys and field metadata needed by submission selection and normalization. Do not select active submissions, convert values, or validate the common HB DataFrame in this step.
   - Test configured form/field/period filters, the documented joins, and the required source keys/field metadata.

5. **Select active Altinn submissions per unit and requested period**
   - For each comparison period, call `active_no_duplicates_refnr_list` unchanged with the configured form and that period's filter; never call it once across both periods.
   - Filter candidate records to the returned `refnr` values while preserving the period/unit join keys.
   - Compare selected submissions against identifiers from the scoped `enheter` records and fail clearly when a required unit-period has no active submission.
   - Test active/inactive, missing, and multiple-active submissions with distinct receipt dates, and verify both comparison periods remain present.

------- Bookmark start ------------
6. **Implement AltinnHBDataHandler and normalize records**
   - Add `AltinnHBDataHandler` implementing `HBDataHandlerMeta`, composing candidate retrieval and per-period active-submission selection.
   - Apply the approved exact-path single-answer policy: report multiple matches and provide no selected value for that unit-period. Convert unambiguous `verdi` values to numeric while preserving missing values and rejecting unconvertible values, then return the validated common HB DataFrame.
   - Map `ident` to `unit_id` and `iso_periode` to `period`; retain only selector context required by the module.
   - Test numeric conversion, missing/invalid values, approved field matching, output schema, and uniqueness.
------- Bookmark end ------------

7. **Add deterministic test data access**
   - Add `FakeHBDataHandler` for deterministic module tests.
   - Make it record the requested variable, periods, and optional stratum.
   - Return validated common-schema data.
   - Keep it out of the production Altinn path.
   - Test that it can exercise the module without a backend connection.

8. **Add the Vaskify dependency and adapter boundary**
   - Add the supported `ssb-vaskify` runtime dependency.
   - Add `run_hb_vaskify`.
   - Construct `Detect(hb_input_dataframe, id_nr="unit_id")`.
   - Add structural preflight checks for exactly two distinct canonical periods, matching input period levels, Vaskify-compatible required dtypes, and a present `strata` column when configured.
   - Pass `value`, `period`, comparison periods, optional stratum, and explicit public API defaults (`pu=0.5`, `pa=0.05`, `pc=20`, `percentiles=(0.25, 0.75)`, `flag="flag_hb"`, `output_format="wide"`, `output_scope="all"`) to `Detect.hb(...)`.
   - Do not filter zero, negative, or missing values or recreate Vaskify eligibility/calculation rules in the framework.
   - Keep Vaskify argument mapping out of the Altinn adapter and Dash callbacks.
   - Add mocked tests for exact Vaskify arguments and preflight failures.

9. **Normalize Vaskify results**
   - Add `normalize_hb_result`.
   - Validate the returned Vaskify shape.
   - Preserve stable identifiers, source context, comparison values, period context, diagnostics, `ratio`, `median_ratio`, limits, and `flag_hb`.
   - Reconcile results with the full handler input so units without Vaskify diagnostics remain visible.
   - Keep flagged (`1`), calculated/unflagged (`0`), and not-comparable (missing diagnostics/flag) states distinct.
   - Use verified Vaskify return behavior to distinguish no eligible population from an error; do not treat an unverified empty result as “no outliers.”
   - Add unit tests for valid, incomplete, missing, not-comparable, and invalid results.

10. **Create the ModuleBase shell**
   - Add `HBMethod` under `src/ssb_dash_framework/modules/`.
   - Set `label`, `icon`, and the handler before `ModuleBase.__init__()`.
   - Implement `layout()` with controls, run button, loading state, errors, empty state, result store, and graph placeholders.
   - Implement `module_callbacks()` using `self.module_id` for every component ID.
   - Use descriptive IDs such as `hb_run_button`, `hb_result_graph`, `hb_error_message`, and `hb_result_store`.
   - Test construction, lifecycle, unique IDs, and tab/window placement.

11. **Connect selector inputs to the run action**
   - Read the selected HB variable and canonical period from `VariableSelector` at callback time.
   - Validate required selector configuration during construction.
   - Resolve comparison periods with `resolve_hb_comparison_periods`.
   - Call `AltinnHBDataHandler.get_hb_dataframe(...)` with the explicit named HB arguments.
   - Do not store per-user selector values on the module instance.
   - Test handler arguments and missing selector configuration.

12. **Execute and display an HB run**
   - On the explicit run action, call the handler, `run_hb_vaskify`, and `normalize_hb_result` in that order.
   - Store the normalized result for the current run.
   - Build the result figure from normalized Vaskify columns.
   - Display ratio, median ratio, limits, and candidate state without reimplementing HB logic.
   - Route failures through `AlertHandler` and log context without row-level sensitive data.
   - Test successful runs, handler failures, Vaskify failures, warning-only paths, and empty or not-comparable data.

13. **Add click-to-selector behavior**
   - Put the stable `unit_id` in Plotly `customdata`.
   - Read the identifier from click data, never from hovertext, labels, or row positions.
   - Update the configured `VariableSelector` output.
   - Read the stored result only; do not call the handler or Vaskify on selection.
   - Test selecting multiple candidates and selecting no point.

14. **Export and register the module**
   - Export `HBMethod` through `ssb_dash_framework.modules` and the package top-level API where required.
   - Register the module with the existing YAML configuration mechanism.
   - Document constructor and handler configuration keys.
   - Search for imports of the experimental prototype before removing or redirecting it.
   - Test normal imports and YAML registration.

15. **Add integration and reference-result tests**
   - Test the installed Vaskify package with deterministic input data.
   - Verify the actual result shape, `ratio`, `median_ratio`, limit and flag columns, and explicit call defaults.
   - Add reference-result cases for positive, zero, negative, missing, flagged, unflagged, and not-comparable observations.
   - Verify the package's return behavior when no unit has eligible values and when it logs warnings without raising.
   - Keep mathematical algorithm tests in Vaskify, not in framework helpers.

16. **Add demo and browser coverage**
   - Add or update a demo that imports and configures `HBMethod`.
   - Use deterministic test data or the configured Altinn path as appropriate.
   - Verify app startup, run action, result display, and click-to-selector flow.
   - Add demo-specific E2E steps under `tests/e2e/hooks/` when needed.

17. **Complete user documentation**
   - Document Altinn handler setup and required configuration.
   - Document the common DataFrame schema and canonical period requirements for all six `TimeUnit` frequencies.
   - Document the selected period `t` and the `TimeUnit`-based `t-1` assumption.
   - Document result flags, missing/not-comparable states, and limitations.
   - Document click-to-selector behavior and the no-write boundary.
   - Update the module/API documentation without duplicating implementation logic.

18. **Validate completed tasks**
   - Run only the tests explicitly listed for the active task in `plan.md`, after that task is complete.
   - Run a broader test session or E2E coverage only when explicitly scheduled in `plan.md`.
   - Confirm that no source data is edited and that all failures remain visible.

19. **Remove temporary design documents**
   - Before integrating to `main`, remove `architecture_design_detailed.md` and `ssb-vaskify-design.md` after their lasting decisions and issue context are recorded in `architecture.md` and `Issues.md`.
   - User will decide what to keep in the end.
   - Put back `AGENTS.md`
   - Pull request to integrate the changes into `main`.

20. **Report ISSUES to Github or Magnus**
