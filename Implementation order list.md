# HB methodology implementation order

Each numbered item below is one commit-sized change. Do not combine items unless the dependency requires it. Every sub-point describes one clearly bounded implementation responsibility.

1. **Define the HB public contract**
   - Add the common HB input schema: `unit_id`, canonical `period`, numeric `value`, optional `strata`, and configured selector context.
   - Add `HBDataHandlerMeta.get_hb_dataframe(...)`.
   - Add schema validation and duplicate `unit_id`/`period` rejection.
   - Add unit tests for required columns, types, uniqueness, and clear errors.
   - Do not add Altinn queries or Vaskify calls.

2. **Implement canonical period resolution**
   - Add `resolve_hb_comparison_periods`.
   - Accept framework-canonical period strings such as `YYYY`, `YYYY-Q1`, and `YYYY-MM`.
   - Use `TimeUnit` to derive `(t-1, t)` from the selected period.
   - Keep the resolution policy isolated so it can be changed without changing the data-handler contract.
   - Test every supported frequency and invalid period input.

3. **Implement the Altinn source adapter**
   - Add `AltinnHBDataHandler` implementing `HBDataHandlerMeta`.
   - Select the configured form and field.
   - Resolve active submissions.
   - Convert the selected `verdi` to numeric.
   - Resolve or reject repeated and nested field ambiguity.
   - Return one common HB row per unit and period.
   - Preserve only selector context required by the module.
   - Test active submissions, missing values, numeric conversion, duplicates, and ambiguous source data.

4. **Add deterministic test data access**
   - Add `FakeHBDataHandler` for deterministic module tests.
   - Make it record the requested variable, periods, and optional stratum.
   - Return validated common-schema data.
   - Keep it out of the production Altinn path.
   - Test that it can exercise the module without a backend connection.

5. **Add the Vaskify dependency and adapter boundary**
   - Add the supported `ssb-vaskify` runtime dependency.
   - Add `run_hb_vaskify`.
   - Construct `Detect(hb_input_dataframe, id_nr="unit_id")`.
   - Pass `value`, `period`, comparison periods, optional stratum, and approved output options to `Detect.hb(...)`.
   - Keep Vaskify argument mapping out of the Altinn adapter and Dash callbacks.
   - Add mocked tests for exact Vaskify arguments.

6. **Normalize Vaskify results**
   - Add `normalize_hb_result`.
   - Validate the returned Vaskify shape.
   - Preserve stable identifiers, comparison values, period context, diagnostics, `ratio`, limits, and `flag_hb`.
   - Keep flagged, unflagged, and not-comparable states distinct.
   - Reject invalid results and distinguish errors from valid empty populations.
   - Add unit tests for valid, incomplete, missing, and invalid results.

7. **Create the ModuleBase shell**
   - Add `HBMethod` under `src/ssb_dash_framework/modules/`.
   - Set `label`, `icon`, and the handler before `ModuleBase.__init__()`.
   - Implement `layout()` with controls, run button, loading state, errors, empty state, result store, and graph placeholders.
   - Implement `module_callbacks()` using `self.module_id` for every component ID.
   - Use descriptive IDs such as `hb_run_button`, `hb_result_graph`, `hb_error_message`, and `hb_result_store`.
   - Test construction, lifecycle, unique IDs, and tab/window placement.

8. **Connect selector inputs to the run action**
   - Read the selected HB variable and canonical period from `VariableSelector` at callback time.
   - Validate required selector configuration during construction.
   - Resolve comparison periods with `resolve_hb_comparison_periods`.
   - Call `AltinnHBDataHandler.get_hb_dataframe(...)` with the explicit named HB arguments.
   - Do not store per-user selector values on the module instance.
   - Test handler arguments and missing selector configuration.

9. **Execute and display an HB run**
   - On the explicit run action, call the handler, `run_hb_vaskify`, and `normalize_hb_result` in that order.
   - Store the normalized result for the current run.
   - Build the result figure from normalized Vaskify columns.
   - Display ratio, limits, and candidate state without reimplementing HB logic.
   - Route failures through `AlertHandler` and log context without row-level sensitive data.
   - Test successful runs, handler failures, Vaskify failures, and empty or not-comparable data.

10. **Add click-to-selector behavior**
   - Put the stable `unit_id` in Plotly `customdata`.
   - Read the identifier from click data, never from hovertext, labels, or row positions.
   - Update the configured `VariableSelector` output.
   - Read the stored result only; do not call the handler or Vaskify on selection.
   - Test selecting multiple candidates and selecting no point.

11. **Export and register the module**
   - Export `HBMethod` through `ssb_dash_framework.modules` and the package top-level API where required.
   - Register the module with the existing YAML configuration mechanism.
   - Document constructor and handler configuration keys.
   - Search for imports of the experimental prototype before removing or redirecting it.
   - Test normal imports and YAML registration.

12. **Add integration and reference-result tests**
   - Test the installed Vaskify package with deterministic input data.
   - Verify the actual result shape and expected diagnostic columns.
   - Add reference-result cases for flagged, unflagged, and not-comparable rows.
   - Keep mathematical algorithm tests in Vaskify, not in framework helpers.

13. **Add demo and browser coverage**
   - Add or update a demo that imports and configures `HBMethod`.
   - Use deterministic test data or the configured Altinn path as appropriate.
   - Verify app startup, run action, result display, and click-to-selector flow.
   - Add demo-specific E2E steps under `tests/e2e/hooks/` when needed.

14. **Complete user documentation**
   - Document Altinn handler setup and required configuration.
   - Document the common DataFrame schema and canonical period requirements.
   - Document the selected period `t` and the `TimeUnit`-based `t-1` assumption.
   - Document result flags, missing/not-comparable states, and limitations.
   - Document click-to-selector behavior and the no-write boundary.
   - Update the module/API documentation without duplicating implementation logic.

15. **Run final validation**
   - Run targeted unit and integration tests.
   - Run the required `uvx nox --session=tests` suite.
   - Run E2E coverage when the demo has changed and the environment supports it.
   - Run formatting, linting, and import checks.
   - Confirm that no source data is edited and that all failures remain visible.
