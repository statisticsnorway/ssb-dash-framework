# Implementation plan: HB methodology module for SSB Dash Framework

## Goal

Implement an application module that runs an HB outlier method for a selected
reporting period, displays the results, and sends a clicked unit's identifier
to `VariableSelector`. Treat the selected period as `t` and provisionally
compare it with `t-1` at the configured publication frequency. Keep the module
independent of both the data source and the HB calculation: a prepared
DataFrame or source adapter supplies the common input, the HB module calls
Vaskify, and Vaskify performs the methodology.

This plan describes a module in `ssb-dash-framework`; it does not implement or
re-specify the HB algorithm.

## Current state and constraints

* The framework's intended module contract is `ModuleBase`, with `layout()` and
  `module_callbacks()`. It supplies unique `module_id` values and tab/window
  wrapping.
* The current prototype is
  [`experimental/modules/hb_method.py`](ssb-dash-framework/src/ssb_dash_framework/experimental/modules/hb_method.py).
  It does not inherit from `ModuleBase`; it uses the older implementation
  patterns, has an abstract `layout()`, and its HB calculation call is
  commented out. Its plot expects calculated columns such as `ratio`,
  `upperLimit`, and `outlier`, so it is not a complete working implementation.
* The framework architecture calls for independent modules, shared values via
  `VariableSelector`, backend-agnostic data access, and YAML-configurable
  modules where practical.
* Vaskify is the selected HB methodology provider and is owned by the
  methodology department. Its public API is `Detect(data, id_nr).hb(...)`,
  returning a DataFrame. The Dash framework owns the UI and integration only:
  the HB module must call Vaskify through its helper and must not reimplement
  or fork the HB algorithm.
* Scope is limited to the `ssb-dash-framework` repository and its feature
  branch. Vaskify is consumed as an installed dependency; this work does not
  check out, branch, or modify the Vaskify repository.
* Implement the new module in the normal `modules/` package on this feature
  branch. The branch is the development boundary; there is no need to first
  expose the feature under `experimental/` and later move/promote it.

## Target architecture

```text
VariableSelector ── selected variable / periods ──┐
                                                  v
Data source ──> source adapter ──> common HB DataFrame
                                             │
                                             v
                                      HB module ──> Vaskify
                                             │          │
                                             └── figure/result DataFrame
                                                        │
Clicked unit ───────────────────────────────> VariableSelector output
```

**Lag ett felles DataFrame-format for HB, og én adapter per datakilde.**
The HB calculation consumes only this common DataFrame format. The required
Altinn adapter supplies it to the interactive module; source-specific reading
and conversion belong in that handler, not in the module. A prepared
DataFrame or fake handler remains useful for isolated tests, but does not
replace the required Altinn adapter in the product implementation. Different future adapters can follow the same pattern without affecting the HB module.

See [altinnapiclient-documentation.md](altinnapiclient-documentation.md) for
the repository's existing Altinn database access patterns, schema relationships,
and decisions the HB adapter must make explicitly.

Responsibilities:

| Component | Responsibility |
|---|---|
| `HBMethod` Dash module | Inputs, run action, loading/error state, result figure, and click-to-select |
| `HBDataHandlerMeta` | Define the contract for supplying and validating the common HB DataFrame |
| Source adapter | Read/receive one source's data, convert it once to the common HB DataFrame, and preserve selector context |
| HB/Vaskify call helper | Translate the common DataFrame and selected periods to `Detect.hb()` and normalize its result |
| Vaskify | Perform and own the HB calculation |
| `VariableSelector` | Share configured analysis selections and receive the clicked unit identifier |

The module must not read another module's component IDs or callbacks. It should
receive data through an explicit handler interface and share state only through
the selector. The handler interface is not an instruction for each module to
implement data loading: a concrete adapter is written once per source and can
be reused by the HB module wherever that source is used.
The source adapter's responsibility ends when it has produced the common
DataFrame; it is not also a Vaskify adapter. The HB module owns the Vaskify call,
result normalization, and presentation.

## Naming and scope rules

Names must make both the domain and the responsibility visible. Do not
introduce generic public names such as `DataHandler`, `Result`, `periods`, or
`get_data` when the same names could later describe another module's concept.
A name that is technically available in Python is not sufficient if its
meaning would be ambiguous to a reader or to a later module.

Apply these rules to the implementation:

1. **Public HB symbols are explicitly scoped.** Use `HBMethod`,
   `HBDataHandlerMeta`, `PreparedHBDataHandler` or `FakeHBDataHandler`,
   `resolve_hb_comparison_periods`, `run_hb_vaskify`, and
   `normalize_hb_result`. Do not expose a generic `DataHandler`, `Detector`,
   `Result`, or `calculate` symbol for HB functionality.
2. **Local variables carry their domain meaning.** Prefer
   `selected_hb_period`, `hb_comparison_periods`, `hb_input_dataframe`,
   `hb_result_dataframe`, `hb_unit_id`, `selected_hb_variable`, and
   `configured_hb_strata_variable` over `period`, `periods`, `data`, `result`,
   `id`, or `variable` when more than one interpretation is possible.
3. **Selector context is named separately from HB input.** Use names such as
   `selector_period_value`, `selector_unit_identifier`, and
   `source_submission_reference`; do not reuse `unit_id`, `ident`, or `refnr`
   for values with different semantics. The common DataFrame column names are
   interface names, not permission to use the same name for unrelated Python
   variables.
4. **Functions and classes state their boundary.** A source adapter function
   should describe source-to-HB conversion, for example
   `build_hb_dataframe_from_altinn`; a Vaskify helper should describe
   HB-to-Vaskify execution or result normalization. Do not name a source
   function `run_hb` if it also calls Vaskify, and do not name a Vaskify
   function `get_data`.
5. **Component IDs are scoped by `module_id`.** Dash IDs must use the
   `HBMethod` instance's prefix and descriptive suffixes such as
   `hb_run_button`, `hb_result_graph`, and `hb_error_message`; never use
   shared fixed IDs such as `run_button` or `result`.

Before adding a new symbol, search the repository for the proposed name and
for similarly named concepts. If a collision is intentional because it is a
framework-wide interface, document that shared meaning and keep the
module-specific values explicitly qualified at call sites.

## Phase 1 — Agree and document the method boundary

Before implementation, settle the common input/output contract. Keep
source-specific conversion in source adapters and Vaskify-specific argument
and result mapping in the HB method helper:

1. **One common DataFrame format:** One row per unit and period for the
   selected target variable. For an HB run, it contains the two comparison
   periods (`t-1` and `t`). Required columns are `unit_id` (string),
   `period` (canonical framework period string: `YYYY` for YEAR, `YYYY-1` or
   `YYYY-2` for HALF_YEAR, `YYYY-Q1` through `YYYY-Q4` for QUARTER, `YYYY-MM`
   for MONTH, `YYYY-Www` for WEEK, or `YYYY-MM-DD` for DAY), and `value`
   (numeric). `strata` is optional.
   Adapters may preserve additional columns needed to populate configured
   `VariableSelector` outputs; these are context, not HB calculation inputs.
2. **Uniqueness:** The adapter must produce at most one row per
   `unit_id`/`period` for the selected target. It must explicitly resolve or
   reject duplicate/repeated values rather than silently aggregating them.
3. **Comparison periods:** Vaskify's HB implementation requires two period
   values. Use the framework's canonical period strings for all six
   `TimeUnit` frequencies. Validate each period against the configured
   frequency. The initial implementation uses the period selected in
   `VariableSelector` as `t` and derives `t-1` using the configured `TimeUnit`
   frequency. This is an implementation assumption to be confirmed as part of
   the product design. Keep the period-resolution rule isolated so it can be
   changed if the intended comparison policy differs. The current framework
   `TimeUnit.parse` cannot parse week strings with the installed Pendulum token
   set, and quarter `SelectedTimeUnit.to_str()` does not currently produce
   canonical quarter strings; the period-resolution implementation must
   address both limitations before supporting those frequencies.
4. **Target variable:** Select/configure the source variable before it becomes
   the common numeric `value` column; do not make source-specific field names
   part of the HB module contract.
5. **Stratification:** Make stratification optional, with no stratum as the
   default. Vaskify supports `strata_var`; offer it only when the input data
   contains a suitable grouping variable, and test missing and small groups.
6. **Parameters:** Start with Vaskify defaults unless there is a concrete need
   to expose parameters. If exposed, validate bounds and document their units.
7. **Results:** Agree the minimum normalized columns: identifier, period or
   period pair, original values, ratio/diagnostics where available, and a
   configurable outlier flag.
8. **Selection semantics:** A clicked graph point should update the configured
   selector output with the unit identifier. Preserve any additional
   source-specific selector values separately; for Altinn, `ident` and
   submission-level `refnr` have distinct roles.

Do not treat an algorithm error or an empty eligible population as a successful
“no outliers” result. Preserve missing/not-comparable separately from flag 0.
The framework validates the structural input and call contract, but does not
duplicate Vaskify's positive-value eligibility filter, ratio/limit calculation,
stratification algorithm, or flag decisions. Vaskify owns those method rules.
Because Vaskify uses only positive values in both periods, its `output_scope`
of `"all"` may still omit input units that have no diagnostics. Preserve the
full input and reconcile the returned diagnostics by stable identifier so
omitted units remain distinguishable from unflagged units. Confirm the
installed package's return behavior when no unit is eligible; do not treat an
empty return or warning as success without that verification.

## Phase 2 — Define the shared DataFrame and source-adapter contract

```python
class HBDataHandlerMeta(ABC):
    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        # Ordered as previous period, then selected/current period.
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> pd.DataFrame: ...
```

Define and validate the common DataFrame schema at this boundary. Implement
source-specific handlers outside `HBMethod`. The required
`AltinnHBDataHandler` converts Altinn data, while a future
`ExcelHBDataHandler` can convert Excel data to the same columns. The handler
instance can be injected into the Dash module. A deterministic
`FakeHBDataHandler` or a DataFrame already prepared by the caller is
sufficient for isolated tests; it does not replace the required Altinn
adapter. The calculation function itself should accept a DataFrame, not a
filepath or database connection.

The common validator and HB module are responsible for API-level preflight,
not the HB algorithm. The validator accepts canonical strings for all six
framework `TimeUnit` frequencies and checks them against the configured
frequency when supplied. Before calling Vaskify, verify that the requested
period pair contains exactly two distinct canonical periods, that the input
contains exactly those two period levels, that required columns and dtypes are
Vaskify-compatible, and that a configured stratum maps to an existing
`strata` column. Do not filter input units by positive or missing values to
recreate Vaskify's eligibility behavior.

Read the selected canonical period `t` from `VariableSelector`; use the
configured `TimeUnit` frequency to resolve the preceding period `t-1`. Pass
the ordered pair `(t-1, t)` to the data handler (when one is used) and to
Vaskify. This period-resolution rule is an implementation assumption to be
confirmed as part of the product design. Keep it in a small helper separate from
source adapters, so a different comparison policy can be adopted without
changing the DataFrame contract.

The Altinn handler must select the configured form/field, resolve active
submissions and any repeated-field ambiguity, convert the selected `verdi` to
numeric, and return one HB row per unit and period. Keep those Altinn rules out
of `HBMethod`. An Excel handler can perform the corresponding column mapping
and reshaping later, without changes to the HB module.

Use the framework's existing `get_connection()` and injected data-function
patterns inside a source handler where appropriate. Avoid a generic plugin or
runner framework: source adapters only supply the agreed DataFrame. They do
not call Vaskify or contain Vaskify-specific result mapping. The HB module
calls Vaskify on the common DataFrame through a small helper:

```python
hb_detector = Detect(hb_input_dataframe, id_nr="unit_id")
hb_vaskify_result_dataframe = hb_detector.hb(
    y_var="value",
    time_var="period",
    time_periods=list(hb_comparison_periods),
    strata_var="strata" if configured_hb_strata_variable else "",
    pu=0.5,
    pa=0.05,
    pc=20,
    percentiles=(0.25, 0.75),
    flag="flag_hb",
    output_format="wide",
    output_scope="all",
)
```

These are Vaskify's public API defaults, set explicitly in one helper so the
integration is deterministic and testable. They are not user-facing controls
or an assertion that the methodology has approved alternative values. Do not
invent framework-side statistical bounds; validate only configured types and
the public call contract unless approved parameter constraints are documented.

Map Vaskify's `flag_hb`, `ratio`, `median_ratio`, `lower_limit`, and
`upper_limit` into the module's result view, while retaining the returned
DataFrame and its method-specific columns. Preserve the original handler input
and reconcile the output using stable unit identifiers. A missing diagnostic
or flag is not comparable; flag `0` is calculated and unflagged. Do not
interpret `output_scope="all"` as guaranteeing one diagnostic row per source
unit: Vaskify only uses positive values in both comparison periods. Keep this
eligibility rule inside Vaskify. If no eligible result is returned, use
integration-tested behavior to distinguish not-comparable observations from
an error; never render an unverified empty result as “no outliers.”

The UI module must not open a source connection or contain source-specific
queries. A handler can use the configured connection and return pandas data;
the module then passes that DataFrame to the Vaskify helper and displays the
normalized result.

## Phase 3 — Implement the normal `ModuleBase` module

1. Implement `HBMethod` as a `ModuleBase` subclass under
   `src/ssb_dash_framework/modules/`.
2. Set `label`, `icon`, and data handler before calling
   `super().__init__()`.
3. Implement `layout()` for the method controls, run button, progress/loading
   state, error/empty-result message, and result visualization.
4. Implement `module_callbacks()` using `self.module_id` for every component
   ID. Remove the prototype's class-level counter and fixed IDs.
5. Keep the visual content presentation-neutral so `main_layout` can place the
   module as either a tab or a window.
6. Use `VariableSelector` helper methods for configured shared values. Validate
   required selector configuration early and provide actionable errors.
7. On run, gather current selector/local inputs, ask the injected handler for
   the common DataFrame, validate the structural input and Vaskify call
   preconditions, call `Detect.hb()` through the small Vaskify helper, then
   validate/reconcile/normalize its result and update the view. Do not
   reimplement Vaskify's eligibility or statistical rules.
8. On a clicked result, map the point to a stable identifier and update the
   configured selector output. Avoid relying on display labels or positional
   row indices as identity.
9. Keep the computed result set available after a run. Selecting a candidate
   and moving to another candidate must not rerun HB. Only the explicit Run
   action starts a new calculation.
10. Treat HB flags as candidates, not corrections. The initial module only
    displays results and sends the selected identifier to `VariableSelector`;
    it does not edit or write source data. Any later editing workflow is a
    separate concern.
11. Route user-visible failures through the existing `AlertHandler` pattern and
    log useful context without logging sensitive row-level data.

Export the module from `ssb_dash_framework.modules` and the package top level,
following the framework's public API convention. Before removing the old
experimental path, search for imports and either retain a short compatibility
re-export or document that the prototype was never a supported public API.

## Phase 4 — Configuration and Vaskify dependency

* Add `ssb-vaskify` as a runtime dependency at a version compatible with the
  supported Vaskify API. The new normal module imports `Detect` and delegates
  the calculation to it; do not add another HB implementation.
* Use the existing module configuration conventions for selecting a data
  handler. A Python handler instance cannot be represented directly in YAML;
  if YAML setup is required, provide a documented app-level factory or
  serializable adapter configuration. Do not add a generic plugin system just
  to resolve this.
* Implement the common `HBDataHandlerMeta` contract and the required
  `AltinnHBDataHandler`. A prepared DataFrame or deterministic fake handler
  may be used for isolated tests. Any additional source adapter, such as
  Excel, implements the same contract and returns the same DataFrame schema;
  it does not call Vaskify or require changes to `HBMethod`.
* Verify that the class is registered for YAML when its module is imported
  and document the supported constructor/configuration keys.
* Keep Vaskify method defaults and argument mapping in one place (the
  small helper/configuration object), not duplicated between UI state and
  calculation code. Initially pass the documented API defaults explicitly:
  `pu=0.5`, `pa=0.05`, `pc=20`, `percentiles=(0.25, 0.75)`,
  `flag="flag_hb"`, `output_format="wide"`, and `output_scope="all"`.
  Treat these as API defaults, not methodology approval for alternative
  values. Do not invent parameter bounds in the framework.

## Phase 5 — Tests and documentation

### Unit tests

Add tests under `tests/unittests/` for:

* module construction and valid `ModuleBase` lifecycle;
* unique prefixed IDs, including two instances in one app;
* missing selector configuration and invalid inputs;
* handler receives the selected variable/period inputs and returns the
  documented DataFrame schema;
* the required Altinn adapter maps active submissions, numeric values, and
  repeated/nested field ambiguity;
* the prepared DataFrame/fake handler supplies the same required columns for
  isolated module tests;
* Vaskify is called with the expected `y_var`, `time_var`, `time_periods`,
  optional `strata_var`, explicit API-default parameters, and output options;
* preflight rejects malformed period pairs, unexpected period levels,
  Vaskify-incompatible required column types, and missing configured strata
  without duplicating method eligibility rules;
* canonical framework period strings are accepted and checked against the
  configured frequency for all six `TimeUnit` frequencies;
* the selected `VariableSelector` period is treated as `t`, and the
  period-resolution helper returns the expected `(t-1, t)` pair for all six
  frequencies, including canonical quarter/week formatting despite the current
  framework parser/formatter limitations;
* normalized result flags, `ratio`, `median_ratio`, limits, diagnostics,
  identifier/context reconciliation, and missing-flag semantics;
* positive, zero, negative, and missing values, including Vaskify's
  not-comparable behavior without framework-side eligibility filtering;
* warning-only and no-eligible-result behavior, empty results, invalid data,
  and Vaskify exceptions;
* click selection updates the configured shared identifier;
* tab and window placement both work without changing module behavior.

Use a deterministic fake handler for UI/module unit tests. Test source
adapters separately, and test the Vaskify call/normalization helper with a
mocked `Detect` where isolation is useful. Add integration tests using the
installed `ssb-vaskify` package to verify that the actual call and result
shape work together.

### Integration/e2e tests

Add a fixture-based integration test that calls Vaskify and compares known
inputs with expected flags/limits. Add or extend a demo and browser smoke test
to verify module import, run, result display, and click-to-selector behavior.
Do not test mathematical internals through private framework helpers.

### Documentation

Update the framework's module documentation and API reference with:

* installation and Altinn data-handler setup;
* prepared-DataFrame/fake-handler setup for isolated tests;
* the common DataFrame schema and period requirements;
* how the selected period is used as `t` and how `t-1` is derived;
* how the required Altinn adapter and future Excel adapters map to that
  schema;
* module configuration and usage;
* Vaskify's positive-value eligibility behavior and its effect on which input
  units receive diagnostics;
* the distinction between flagged, calculated/unflagged, and not-comparable
  results, including how source context is retained for units without
  diagnostics;
* the explicit Vaskify API defaults used by the integration and which
  parameter choices have not been approved for user configuration;
* how clicking a candidate updates the configured `VariableSelector` output;
* unsupported shapes and known limitations;
* the module's supported status, requirements, and known limitations.

## Acceptance criteria

The first usable version is complete when:

- The module conforms to `ModuleBase` and can be placed in either a tab or a
  window.
- It obtains production data through the required Altinn handler implementing
  `HBDataHandlerMeta`; the HB calculation itself receives only the common
  DataFrame. Prepared DataFrames and fake handlers are supported for isolated
  tests.
- The required Altinn adapter returns the documented schema, while a fake
  handler can exercise the UI flow independently of backend data access.
  Integration tests exercise the real Vaskify call, and later adapters can
  return the same schema without changing the HB module.
- The result view clearly distinguishes flagged, unflagged, and
  not-comparable observations.
- Selecting a result updates the configured shared unit identifier.
- Selecting a candidate does not require the HB module to know about or access
  the underlying source.
- The HB module does not edit or write source data.
- The initial module does not automatically change source values based on HB
  flags.
- Failures are visible and do not produce success-shaped empty results.
- Tests cover module lifecycle, handler/Vaskify wiring, output normalization,
  and selection behavior.
- The module is available through the normal framework import/configuration
  path, and documentation states the schema and Vaskify call boundary.
- HB-specific public symbols, local variables, and component IDs make their
  domain and responsibility explicit; no generic name is reused for a
  different concept without documenting the shared interface meaning.

## Risks and open decisions

| Question | Why it matters | Recommended default |
|---|---|---|
| Which Vaskify version will the framework support? | Determines the install requirement and verified API | Pin a compatible range in runtime dependencies |
| How are comparison periods selected? | Controls which observations are compared | Initial implementation assumption: treat the selector's canonical period as `t` and derive `t-1` from its configured `TimeUnit` frequency; confirm this as product design and isolate the rule so it can be changed |
| Is stratification needed in the initial implementation? | Changes data requirements and method invocation | Optional, omitted unless configured |
| How are handler instances configured in YAML? | Python instances cannot be represented directly in YAML | Use an app factory or serializable adapter configuration if required |
| Which selector identifies the clicked unit? | `ident` and `refnr` have distinct framework meanings | Confirm against the app's `VariableSelectorConfig` |
| Which extra columns must a source adapter preserve for selector output? | The selected HB unit may need additional context in the app | Require `unit_id`; preserve only configured selector values as extra columns |
## Suggested implementation order

1. Confirm the open decisions that affect public inputs and selection.
2. Define and document the common HB DataFrame schema and
   `HBDataHandlerMeta`.
3. Implement and test the required `AltinnHBDataHandler`, while also adding a
   prepared DataFrame/fake handler for isolated module tests.
4. Add the supported `ssb-vaskify` dependency and a minimal integration test.
5. Implement `HBMethod` as a normal `ModuleBase` module under `modules/`.
6. Search proposed public symbols and component-ID suffixes for existing
   meanings, then add unit tests for the module, Vaskify result mapping, and
   any source adapters that are actually implemented.
7. Add reference-result integration tests.
8. Add/update demo, e2e coverage, top-level exports, YAML support, and user
   documentation.

## Research findings from Statistics Norway GitHub

The following public implementations provide useful precedents. They support
the plan's boundaries and input/output decisions; they are examples, not
automatic requirements for the new module.

### Reusable Dash module and data access patterns

* [`MapDisplay`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/building_blocks/map_display.py)
  and [`EditingTable`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/building_blocks/tables.py)
  are `ModuleBase` modules that receive a `get_data_func`, keeping data
  retrieval outside the display component. This is a useful injection
  precedent; source-specific conversion should live in a reusable adapter,
  rather than being reimplemented in each module. `MapDisplay` also uses
  `VariableSelector` inputs/states and can send a clicked value back to a
  selector output. This supports a handler seam for HB and the same
  selector pattern for returning a selected unit.
* The [`Altinn demo`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/demo/altinn_app/app.py)
  demonstrates a data function using `get_connection()`, selecting only needed
  columns, and converting the result to pandas with `to_pandas()`. The HB
  source adapter should return the agreed identifier, period, numeric value,
  optional stratum, and any configured selector context.
* The framework's
  [`active_no_duplicates_refnr_list`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/utils/core_query_functions.py)
  helper identifies active Altinn submissions, and
  [`AggDistPlotter`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/experimental/modules/agg_dist_plotter.py)
  contains an experimental, source-specific query and conversion. These are
  useful references, not a ready-made HB adapter: the latter is tied to
  `skjemadata_hoved` and its own aggregation/plotting workflow.
* The documented
  [Altinn data model](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/docs/datamodels.md)
  is already long-form at the field-answer level. If an Altinn adapter is
  implemented, it must narrow the model to one selected numeric target value
  per unit and period; it must not merely reshape raw Altinn rows into long
  format again.
* The existing
  [`experimental HB prototype`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/experimental/modules/hb_method.py)
  is a UI prototype, not a working calculation. Reuse/adapt these parts:
  * **Reuse the visual idea:** a run button, loading-wrapped Plotly figure,
    ratio-versus-size scatter, and upper/lower limit lines. Build the figure
    from Vaskify's returned columns, mapping `ratio`, `lower_limit`,
    `upper_limit`, and `flag_hb` to the graph; do not expect the prototype's
    `maxX`, `upperLimit`, `lowerLimit`, `id`, or `outlier` columns.
  * **Reuse the selection interaction:** clicking a plotted unit updates the
    shared identifier through `VariableSelector.get_output_object(...)`.
    Adapt the point data to carry the identifier in Plotly `customdata`; the
    prototype reads it from `hovertext`, which is display content rather than
    a robust identity field.
  * **Reuse data injection, not source-specific reads in the module:** let a
    handler supply the common DataFrame. Define one shared schema and put
    source mapping in an adapter that can be reused independently of the UI.
  * **Reuse parameter controls only if approved:** the prototype displays
    `pu`, `pa`, and `pc`, but its defaults are not automatically the
    methodology department's approved settings. Start from the agreed
    Vaskify defaults; add editable controls only if users need them and their
    valid ranges are documented.
  * **Do not copy the prototype's lifecycle:** it does not inherit from
    `ModuleBase`, has its own class counter, uses fixed component IDs, and
    declares an abstract `layout()`. Use `ModuleBase`, `self.module_id`, and
    concrete `layout()`/`module_callbacks()` implementations instead.
  * **Do not copy its calculation or methodology text:** the calculation call
    is commented out, while the plotting code assumes its results exist. Its
    info text also describes special inclusion rules that must be checked
    against Vaskify and confirmed by the methodology department before being
    shown to users.
  * **Do not store a user's selected variable on `self`:** the prototype's
    callback mutates `self.variable`. Pass the current selection as a
    callback input/state to avoid sharing mutable selection state between
    users of the same module instance.

### Lessons from other completed framework modules

* [`FigureDisplay`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/building_blocks/figuredisplay.py)
  is the closest visualization precedent: it separates figure generation
  from the callback, gets shared values through `VariableSelector`, and
  optionally converts Plotly click data into a selector output. Reuse those
  separations in `HBMethod`, but keep the HB-specific run button, result state,
  and error/empty states in the dedicated module rather than wrapping it in
  `FigureDisplay`.
* [`Aarsregnskap`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/aarsregnskap.py)
  checks that required selector variables exist before the module is set up.
  Adopt the fail-early validation idea for the HB identifier/time variables.
  Do not copy its fixed component IDs; HB IDs must use `self.module_id`.
* [`DataEditor` metadata interfaces](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/data_editor/meta.py)
  show how backend retrieval can be abstracted behind a fetcher contract.
  The full `FetcherMeta`/context hierarchy is more than this read-only module
  needs. Use a small `HBDataHandlerMeta` contract and reusable source adapters
  that return the common DataFrame.
* [`BofInformation`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/src/ssb_dash_framework/modules/bofregistry.py)
  probes its database during construction and contains backend-specific file
  access. Do not copy that approach: creating the HB module should not perform
  data queries or require a particular database to be available. Fetch data
  when the user runs the method and surface a clear error if that operation
  fails.
* The existing [`FigureDisplay tests`](https://github.com/statisticsnorway/ssb-dash-framework/blob/main/tests/unittests/module_tests/test_figuredisplay.py)
  mostly cover import, construction, placement, and direct callable behavior.
  They are useful smoke-test examples, but are not enough for this feature.
  Also test the callback data flow, Vaskify invocation/result normalization,
  and click-to-selector behavior.

### Vaskify use in other SSB projects

* In [`play-aiml-edit`](https://github.com/statisticsnorway/play-aiml-edit),
  [`hb_accumulation_common.py`](https://github.com/statisticsnorway/play-aiml-edit/blob/main/src/HB_and_accumulation_models/hb_accumulation_common.py)
  prepares panel data with a unit identifier, period, value, and NACE grouping;
  forms two-period datasets; and calls
  `Detect(subset, "unit_id").hb(...)`. It passes `pu`, `pc`, `pa`, and
  `strata_var` explicitly, then renames period columns and adds plotting
  context such as maximum value and comparison period. Its README says HB
  parameters were calibrated by industry group and month pair. For this module
  that means:
  * construct a clear, two-period input for Vaskify;
  * treat parameter defaults/calibration as methodology-department-owned, not
    casual UI sliders;
  * keep the optional stratum aligned with the actual domain grouping and
    selected comparison periods.
* The same research helper skips subsets that do not have exactly two periods
  or expected result columns and may return `None` when no result is produced.
  That is acceptable as an offline research workflow, but the interactive
  module should instead report “not enough comparable data” or a clear error
  and retain a consistent result shape.
* The
  [`speshelse review script`](https://github.com/statisticsnorway/speshelse/blob/22c4283731a4da2471dc7e2192cee9ae6ffc28d5/experimental/skj47_gjennomsyn.py)
  constructs a Vaskify `Detect` from a prepared DataFrame, runs
  `thousand_error`, `accumulation_error`, and `hb`, filters flagged rows, then
  joins those identifiers back to the source records for human review. This
  supports preserving the original values and identifiers alongside the
  normalized HB diagnostics. Its Oracle access and survey-specific field
  preparation should not be copied into the reusable framework module.

### Result and integration implications

Based on those examples, use this first-version integration contract:

1. A prepared DataFrame or source adapter supplies the common HB DataFrame: one
   row per unit/period, with string `unit_id`, canonical framework `period`,
   numeric `value`, and optional
   `strata`. Any configured selector context is preserved as extra columns.
2. The HB module calls Vaskify with an explicit pair of periods and requests a
   predictable output format/scope. It normalizes Vaskify's result but keeps
   its original diagnostics available. Source adapters only prepare the
   DataFrame.
3. Keep the source identifier and both compared values so a flagged result can
   be traced and reviewed; use a stable identifier in Plotly `customdata` for
   selector updates.
4. Preserve not-comparable cases as an explicit missing/not-assessable state.
   Do not silently drop them or translate a failed/empty calculation into
   “no outliers.”
5. Keep method parameter defaults in configuration owned in coordination
   with the methodology department. The research project demonstrates that
   parameter calibration can vary by group and comparison period; do not
   assume one universal set of slider defaults.

The HB module does not distinguish Altinn from Excel or another source. Each
source adapter implements the same handler contract and converts its input to
this DataFrame schema; the module and Vaskify call remain unchanged.
