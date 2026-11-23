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

6. **Implement AltinnHBDataHandler and normalize records**
   - Add `AltinnHBDataHandler` implementing `HBDataHandlerMeta`, composing candidate retrieval and per-period active-submission selection.
   - Add the HB-specific `HBDataResult` and `HBDataWarning` contract: return the validated common HB DataFrame with structured warning records containing the approved message, unit, and period. The HB module sends each warning through the existing `AlertHandler`; source handlers do not call Dash.
   - Apply the approved exact-path single-answer policy: for multiple matches, provide no selected value, preserve the unit-period with a missing value, and add its `HBDataWarning`. Convert unambiguous `verdi` values to numeric while preserving missing values and rejecting unconvertible values, then return the data and warnings in `HBDataResult`.
   - Map `ident` to `unit_id` and `iso_periode` to `period`; retain only selector context required by the module.
   - Test numeric conversion, missing/invalid values, approved field matching, `HBDataResult`/`HBDataWarning` details, output schema, and uniqueness.

7. **Altinn strata support**
   - Define the exact Altinn field mapping for `configured_hb_strata_variable` and the approved handling of missing or multiple strata answers before implementation; do not assume the numeric measure's ambiguity policy automatically applies.
   - Extend candidate retrieval to include the configured strata field from the same selected active submission and unit-period as the HB measure.
   - Extend normalization to return the optional `strata` column while preserving source group-value types; keep numeric conversion limited to `value` and preserve existing unstratified behavior.
   - Keep Altinn access and conversion in the source handler; do not add Dash, `AlertHandler`, or Vaskify calls.
   - Test exact field mapping, same-submission and period scoping, strata type preservation, approved missing/ambiguous behavior, output schema and uniqueness, and unchanged unstratified runs.

8. **Account for VariableSelector alerts on HB selection**
   - Document that `VariableSelector` emits an ephemeral alert when its value changes by default.
   - When repeated graph-click selection should be quiet, configure the selected-unit selector's `VariableSelectorOption` display title in `VariableSelectorConfig.ignore_alerts_on_varchange` at the consuming-application level; the framework matches the display title, not the component ID.
   - Keep alert suppression in the app's selector configuration; do not mutate shared `VariableSelector` configuration or add duplicate selection alerts in `HBMethod`.
   - Verify configured suppression in the HB selector integration, preserving default alerts for selector display titles not listed for suppression.

9. **Add deterministic test data access**
   - Add `FakeHBDataHandler` for deterministic module tests.
   - Make it record the requested variable, periods, and optional stratum.
   - Return validated common-schema data.
   - Keep it out of the production Altinn path.

10. **Add the Vaskify dependency and adapter boundary**
   - Add the supported `ssb-vaskify` runtime dependency.
   - Add `run_hb_vaskify`.
   - Construct `Detect(hb_input_dataframe, id_nr="unit_id")`.
   - Add structural preflight checks for exactly two distinct canonical periods of the same `TimeUnit` frequency, matching input period levels, Vaskify-compatible required dtypes, and a present `strata` column when configured.
   - Pass `value`, `period`, comparison periods, optional stratum, and explicit public API defaults (`pu=0.5`, `pa=0.05`, `pc=20`, `percentiles=(0.25, 0.75)`, `flag="flag_hb"`, `output_format="wide"`, `output_scope="all"`) to `Detect.hb(...)`.
   - Do not filter zero, negative, or missing values or recreate Vaskify eligibility/calculation rules in the framework.
   - Keep Vaskify argument mapping out of the Altinn adapter and Dash callbacks.
   - Add mocked tests for exact Vaskify arguments and preflight failures.

11. **Normalize Vaskify results**
   - Reject HALF_YEAR comparisons in `run_hb_vaskify` until Vaskify supports their canonical period strings; keep HALF_YEAR valid in the common HB schema and resolver.
   - Keep a strict-xfail test that calls `Detect.hb()` directly with raw half-year periods; when it passes, verify native behavior before removing the execution guard.
   - Add `normalize_hb_result`.
   - Validate the returned Vaskify shape.
   - Preserve stable identifiers, source context, comparison values, period context, diagnostics, `ratio`, `median_ratio`, limits, and `flag_hb`.
   - Keep context that is stable per unit in one column; retain time-varying extra context in period-qualified columns rather than selecting one period's value.
   - When configured, require a unit's `strata` to be stable across both comparison periods; fail clearly before calling Vaskify if it changes.
   - Reconcile results with the full handler input so units without Vaskify diagnostics remain visible.
   - Keep flagged (`1`), calculated/unflagged (`0`), and not-comparable (missing diagnostics/flag) states distinct.
   - Use verified Vaskify return behavior to distinguish no eligible population from an error; do not treat an unverified empty result as “no outliers.”
   - Add unit tests for valid, incomplete, missing, not-comparable, and invalid results.

12. **Create the ModuleBase shell**
   - Add `HBMethod` under `src/ssb_dash_framework/modules/`.
   - Set `label`, `icon`, and the handler before `ModuleBase.__init__()`.
   - Implement `layout()` with controls, run button, loading state, errors, empty state, result store, and graph placeholders.
   - Implement `module_callbacks()` using `self.module_id` for every component ID.
   - Use descriptive IDs such as `hb_run_button`, `hb_result_graph`, `hb_error_message`, and `hb_result_store`.
   - Test construction, lifecycle, unique IDs, and tab/window placement.

13. **Connect selector inputs to the run action**
   - Read the selected HB variable and canonical period from `VariableSelector` at callback time.
   - Validate required selector configuration during construction.
   - Resolve comparison periods with `resolve_hb_comparison_periods`.
   - Call `AltinnHBDataHandler.get_hb_dataframe(...)` with the explicit named HB arguments.
   - Do not store per-user selector values on the module instance.
   - Test handler arguments and missing selector configuration.

14. **Execute and display an HB run**
   - On the explicit run action, call the handler, `run_hb_vaskify`, and `normalize_hb_result` in that order.
   - Store the normalized result for the current run.
   - Build the result figure from normalized Vaskify columns.
   - Display ratio, median ratio, limits, and candidate state without reimplementing HB logic.
   - Route failures through `AlertHandler` and log context without row-level sensitive data.
   - Test successful runs, handler failures, Vaskify failures, warning-only paths, and empty or not-comparable data.
   - Add a module integration test that supplies `FakeHBDataHandler`, exercises the handler-to-result path without an Altinn or database connection, and verifies that the production backend is not accessed.

15. **Add click-to-selector behavior**
   - Put the stable `unit_id` in Plotly `customdata`.
   - Read the identifier from click data, never from hovertext, labels, or row positions.
   - Update the configured `VariableSelector` output.
   - Read the stored result only; do not call the handler or Vaskify on selection.
   - Test selecting multiple candidates and selecting no point.

16. **Evaluate restrictions against usability**
   - Inventory restrictions across HB input validation, Altinn data access, Vaskify preflight, strata handling, and empty/not-comparable outcomes.
   - For each restriction, distinguish API limitations, method assumptions, data-integrity safeguards, and presentation behavior.
   - Record the real-world use case it blocks, the evidence for keeping it, and any safe less-restrictive alternative.
   - Present recommendations for user approval; do not relax approved behavior as part of this evaluation.
   - Evaluate if some restrictions happen late in the flow causing late warning on non passing data, investigate as a usability issue.

17. **Evaluate Pydantic for HB validation**
   - Consider whether migrating HB module validation to Pydantic would improve clarity and consistency; use [FRAMEWORK-VALIDATION-001 in Issues.md](Issues.md) as cross-module context.
   - Review the common HB DataFrame contract, configuration and input validation, Altinn-specific checks, and Vaskify preflight. Decide which fit Pydantic models and which should remain boundary-specific runtime checks.
   - Assess error reporting, pandas/DataFrame integration, cross-field validation, performance, and the risk of duplicating checks.
   - Record the recommendation and migration scope for approval. This step evaluates the approach; do not migrate validation without approval.

18. **Export and register the module**
   - Export `HBMethod` through `ssb_dash_framework.modules` and the package top-level API where required.
   - Register the module with the existing YAML configuration mechanism.
   - Document constructor and handler configuration keys.
   - Warn users of the legacy HB import path and direct them to the supported top-level API; remove obsolete HB prototype documentation.
   - Test normal imports and YAML registration.

19. **Add integration and reference-result tests**
   - Test the installed Vaskify package with deterministic input data.
   - Verify the actual result shape, `ratio`, `median_ratio`, limit and flag columns, and explicit call defaults.
   - Add reference-result cases for positive, zero, negative, missing, flagged, unflagged, and not-comparable observations.
   - Verify the package's return behavior when no unit has eligible values and when it logs warnings without raising.
   - Keep mathematical algorithm tests in Vaskify, not in framework helpers.

20. **Add demo and browser coverage**
   - Add or update a demo that imports and configures `HBMethod`.
   - Load a deterministic copy of the bundled Altinn fixture into process-local in-memory SQLite and use it with `AltinnHBDataHandler` and the framework `DataEditor`; never edit the bundled or production data.
   - Add one deterministic outlier and verify a confirmed DataEditor edit changes the next HB result; discard the in-memory data when the demo exits.
   - Use `variabel` to load the synthetic value, then stage edits in a demo-only handler until the user confirms the save dialog; do not change `StandardDataHandler` or DataEditor source.
   - Keep the selected submission reference synchronized with the selected unit, form, and period; discard a staged edit when that selection changes.
   - Require a reason and written justification in the demo's **Lagre redigering** dialog; save both with the synthetic value in the in-memory database.
   - Prevent an initial result-display callback on tab remount from overwriting the result of a new HB run.
   - Keep graph sizing adjustments local to the demo.
   - Verify app startup, run action, result display, click-to-selector flow, unit/period switching, unsaved-state clearing, required reason/justification, and that editing 900000007 from 200 to 40 updates the displayed graph value.
   - Add demo-specific E2E steps under `tests/e2e/hooks/` when needed.

21. **Conduct self acceptance testing on the demo**
   - Have intended users exercise the demo with deterministic or approved test data.
   - Cover configuration, period/variable selection, running HB, interpreting results and candidate states, and click-to-selector behavior.
   - Record usability issues and decisions in `plan.md`; make behavior changes only through approved follow-up tasks.

22. refractoring
   - Map if lessons from demo can be applied to the main HB module implementation.
   - hb_module into the hb folder. Maybe a subfolder.
   - Move HB unit tests and their fake handler into `tests/unittests/module_tests/hb/`.
   - Move strict-xfail tests that detect newly available shared `TimeUnit` or Vaskify behavior into `tests/unittests/module_tests/hb/availability_sentinels/`, separate from the regular HB test files.
   - This will break a lot of things.
   - Update all import paths and references to the hb module and its tests accordingly.
   - On first entry to the HB module, run automatically when the required variable and period are available; retain the **Kjør HB-metoden** button for manual reruns. 
   - Verify automatic first run, 15-second retry, and latest-result handling with focused HB unit tests and the HB demo E2E hook on Linux.
   - Add an information icon with a `dbc.Tooltip` explaining the HB method. Use a unique target ID for each module instance; do not add a dependency.


------- Bookmark start ------------
23. **Complete user documentation**
   - Document Altinn handler setup and required configuration.
   - Document the common DataFrame schema and canonical period requirements for all six `TimeUnit` frequencies.
   - Document the selected period `t` and the `TimeUnit`-based `t-1` assumption.
   - Document result flags, missing/not-comparable states, and limitations.
   - Document click-to-selector behavior and the no-write boundary.
   - Update the module/API documentation without duplicating implementation logic.
------- Bookmark end ------------

24. **Conduct user acceptance testing on the demo**
   - Have intended users exercise the demo with deterministic or approved test data.
   - Cover configuration, period/variable selection, running HB, interpreting results and candidate states, and click-to-selector behavior.
   - Record usability issues and decisions in `plan.md`; make behavior changes only through approved follow-up tasks.

25. **Validate completed tasks**
   - Run only the tests explicitly listed for the active task in `plan.md`, after that task is complete.
   - Run a broader test session or E2E coverage only when explicitly scheduled in `plan.md`.
   - Confirm that no source data is edited and that all failures remain visible.

26. **Remove temporary design documents**
   - Before integrating to `main`, remove `architecture_design_detailed.md` and `ssb-vaskify-design.md` after their lasting decisions and issue context are recorded in `architecture.md` and `Issues.md`.
   - User will decide what to keep in the end.
   - Put back `AGENTS.md`
   - Pull request to integrate the changes into `main`.

27. **Report ISSUES to Github or Magnus**
   - Apply all the issues and delete the issues file, move it to boards if not resolved.

-- At this point the initial implementation and documentation tasks should be complete. And we are working on the next version. This is a cutoff point for v1 tasks. ---

28. **restrictions_research.md**
   - Look at the restrictions research document to understand the timing and feedback recommendations for user approval.

29. **Implement fixes for ISSUES where possible**
   - If approved follow trough in v2.

30. nice to haves 
   - Show analysis context with results. A compact label with the selected variable and actual (t-1, t) periods would make results easier to interpret independently of the selector state. This is optional; the shared selector already supplies that context. 