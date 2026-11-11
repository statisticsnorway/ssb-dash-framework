# HB methodology module architecture

## Scope

This document describes the target architecture for implementing the HB
methodology module. It is an application module in
`src/ssb_dash_framework/modules/`. It does not implement the HB algorithm.
Vaskify remains the calculation provider.

The required production source adapter is `AltinnHBDataHandler`. A prepared
DataFrame or `FakeHBDataHandler` is used only for isolated tests and local
development.

The repository's existing Altinn database access patterns and their HB
implications are documented in
[altinnapiclient-documentation.md](altinnapiclient-documentation.md).

## Runtime architecture

```mermaid
flowchart LR
    VS[VariableSelector] -->|selected_hb_variable<br/>canonical period t<br/>selector outputs| HB[HBMethod]
    ALT[Altinn source] --> AH[AltinnHBDataHandler]
    AH -->|common HB DataFrame| HB
    HB -->|Detect(...).hb(...)| V[Vaskify]
    V -->|HB diagnostics DataFrame| N[normalize_hb_result]
    N --> FIG[Plotly result figure]
    FIG -->|click customdata: stable unit identifier| VS
    HB --> ERR[AlertHandler]
```

### Request flow

1. `HBMethod` reads the current selector values when the user presses the
   explicit run button.
2. `resolve_hb_comparison_periods` receives the selected canonical period
   `t` and the configured `TimeUnit`. The initial implementation derives
   `t-1`. This is a product-design assumption to confirm.
3. `AltinnHBDataHandler.get_hb_dataframe(...)` reads Altinn data and returns
   the common DataFrame for `(t-1, t)`.
4. `HBMethod` checks the handler result and Vaskify call preconditions: the
   comparison contains exactly two distinct canonical periods, the frame
   contains exactly those period levels, required columns and dtypes are
   acceptable, and a configured `strata` column exists.
5. The HB helper constructs `Detect(hb_input_dataframe, id_nr="unit_id")` and
   calls `hb(...)` with one explicit, centrally defined parameter set.
6. `normalize_hb_result` validates the returned columns, preserves Vaskify
   diagnostics, and reconciles results with the full handler input so units
   without diagnostics remain visible as not comparable.
7. `HBMethod` stores the normalized result for the current run and renders the
   result figure.
8. A graph click reads the stable identifier from Plotly `customdata` and
   updates the configured `VariableSelector` output. It does not rerun HB.

Errors, invalid input, missing comparable observations, and Vaskify failures
are reported through the framework's `AlertHandler` pattern. They must not be
represented as a successful empty result. Vaskify may log warnings rather than
raise for some invalid calls, so the HB module validates known API preconditions
before calling it and validates the returned shape afterward.

## Components and boundaries

| Component | Location | Owns | Must not own |
|---|---|---|---|
| `HBMethod` | `modules/hb_method.py` | Dash layout, callbacks, structural input/call validation, run state, result figure, click-to-selector behavior | Altinn queries, source reshaping, positive-value eligibility rules, HB mathematics |
| `HBDataHandlerMeta` | HB data-handler module | Contract and common DataFrame validation | Vaskify invocation |
| `AltinnHBDataHandler` | HB data-handler module | Altinn query, active-submission resolution, field selection, numeric conversion, source context | Plotting, Vaskify arguments, Vaskify result mapping |
| `FakeHBDataHandler` | Test support | Deterministic handler responses for module tests | Production data access |
| `resolve_hb_comparison_periods` | HB helper | Resolve `(t-1, t)` using shared canonical-period validation and the HB-local WEEK and QUARTER formatters | Source access |
| `run_hb_vaskify` | HB helper | `Detect` construction and `hb(...)` argument mapping | Altinn-specific logic, Dash callbacks |
| `normalize_hb_result` | HB helper | Stable result schema, source-context reconciliation, flags, diagnostics, and identifier preservation | UI layout, recomputing eligibility or HB diagnostics |
| `VariableSelector` | Framework setup | Shared selections and selected-unit output | HB calculation state |
| `Vaskify` | External dependency | HB calculation | Framework UI and source access |

The source adapter ends at the common DataFrame boundary. It is not also a
Vaskify adapter.

Altinn reads use the configured framework connection and Ibis, as described in
[altinnapiclient-documentation.md](altinnapiclient-documentation.md). The active
submission rule must be approved for HB before implementation. The existing
`active_no_duplicates_refnr_list` helper keeps the latest active row per
`ident`, not per period; if that rule is reused, apply it separately for each
requested period or use period-aware grouping. Do not apply one identifier-only
deduplication across both comparison periods.

## Data contracts

### Common HB input DataFrame

One row represents one unit in one period for the selected target variable.

Required columns:

| Column | Type | Meaning |
|---|---|---|
| `unit_id` | `str` | Stable unit identifier used by Vaskify and graph selection |
| `period` | `str` | Canonical period for `YEAR` (`YYYY`), `HALF_YEAR` (`YYYY-1`/`YYYY-2`), `QUARTER` (`YYYY-Q1`–`YYYY-Q4`), `MONTH` (`YYYY-MM`), `WEEK` (`YYYY-Www`), or `DAY` (`YYYY-MM-DD`) |
| `value` | numeric | Selected numeric target value |

Optional:

| Column | Meaning |
|---|---|
| `strata` | Grouping value passed to Vaskify when configured |
| selector context columns | Source values needed when updating configured selector outputs |

The adapter must return at most one row per `unit_id` and `period`. Repeated
or ambiguous source values are explicitly resolved or rejected; they are not
silently aggregated.

The shared contract allows missing numeric values and does not implement
Vaskify's positive-value eligibility rule. The HB module validates data shape
and API preconditions, but passes value eligibility and all statistical
decisions to Vaskify.

### Handler interface

```python
class HBDataHandlerMeta(ABC):
    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> pd.DataFrame: ...
```

`AltinnHBDataHandler` is the required production implementation. Other source
adapters implement the same contract and do not require changes to
`HBMethod`.

### Vaskify call boundary

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

The normalized result retains the stable identifier, comparison values, period
context, `ratio`, `median_ratio`, `lower_limit`, `upper_limit`, `flag_hb`, and
method-specific diagnostics returned by Vaskify. Flagged (`1`), unflagged
(`0`), and not-comparable (missing diagnostics/flag) states remain distinct.

### Validation boundary: HB module and Vaskify

The HB module validates only the integration contract: DataFrame type and
required columns; non-empty string identifiers; canonical period strings for
all six framework `TimeUnit` frequencies; numeric, non-boolean values; unique
`unit_id`/`period` rows; exactly two distinct requested periods; and that the
input period levels match that pair. When the configured frequency is
available, period validation also requires the strings to match it. When
stratification is requested, the HB module verifies that the mapped `strata`
column is present. It validates the configured Vaskify argument choices and
result shape before display.

The HB week helper validates ISO weeks and uses the shared `TimeUnit.parse()`
when available. It falls back locally only for the known Pendulum
`Unsupported token: WW` error and formats the result using ISO week values.
A strict-xfail round-trip test signals when shared WEEK support is fixed, at
which point the fallback and sentinel can be removed. The separate QUARTER
formatter emits canonical `YYYY-Qn` periods from the selected date's year and
month, without changing `SelectedTimeUnit.to_str()`. A strict-xfail round-trip
test signals when the shared QUARTER formatter is fixed, at which point the HB
formatter and sentinel can be removed. These issues are tracked in
[Issues.md](Issues.md).

The HB module must not filter out zero, negative, or missing values to decide
eligibility, calculate ratios or limits, or recreate flags. Vaskify owns those
method rules. Vaskify's HB implementation uses only positive values in both
periods; as a result, `output_scope="all"` does not guarantee a diagnostic row
for every input unit.

Keep the complete handler DataFrame and reconcile Vaskify output to its
identifiers and context. Missing diagnostics must remain not comparable, not
be converted to flag `0`. If Vaskify returns no eligible results or only logs
a warning, the integration must use the verified return behavior to show a
not-comparable state or a visible error; an empty result must never silently
look like a successful run with no outliers. Do not infer this state from an
empty frame until the installed Vaskify behavior is covered by integration
tests.

Use the public API defaults in one HB/Vaskify configuration location and pass
them explicitly: `pu=0.5`, `pa=0.05`, `pc=20`,
`percentiles=(0.25, 0.75)`, `flag="flag_hb"`, `output_format="wide"`, and
`output_scope="all"`. These are Vaskify API defaults, not user-facing controls
or a claim that the methodology has approved other parameter values. Any
future configurable values must be validated at the integration boundary;
do not invent statistical bounds in the framework.

## Module structure

```text
src/ssb_dash_framework/
├── modules/
│   ├── hb_method.py                 # HBMethod, layout, callbacks
│   └── hb/
│       ├── data_handler.py          # HBDataHandlerMeta, Altinn adapter
│       ├── period_resolution.py     # canonical period and TimeUnit logic
│       └── vaskify.py               # call and result normalization
└── ...

tests/unittests/
├── module_tests/
│   └── test_hb_method.py
└── ...
```

The exact helper file split may follow existing package conventions, but the
boundaries must remain the same.

## Dash state and identifiers

`HBMethod` inherits from `ModuleBase`. Every component ID is prefixed by
`self.module_id`, with descriptive suffixes such as:

```text
<module_id>-hb_run_button
<module_id>-hb_result_graph
<module_id>-hb_error_message
<module_id>-hb_result_store
```

The result store contains the result for the most recent explicit run.
Selection callbacks read from this stored result and do not call the handler
or Vaskify again.

The graph carries the stable `unit_id` in `customdata`. Display labels,
hovertext, and row positions are not identifiers.

## Naming rules

Names must expose both domain and responsibility:

| Avoid | Use |
|---|---|
| `DataHandler` | `HBDataHandlerMeta`, `AltinnHBDataHandler` |
| `data` | `hb_input_dataframe` |
| `result` | `hb_result_dataframe` or `hb_vaskify_result_dataframe` |
| `periods` | `hb_comparison_periods` |
| `variable` | `selected_hb_variable` |
| `run_hb` for a source function | `build_hb_dataframe_from_altinn` |
| fixed `run_button` ID | module-prefixed `hb_run_button` ID |

Selector context uses separate names such as `selector_unit_identifier` and
`source_submission_reference`. Do not reuse `ident`, `refnr`, or `unit_id`
for values with different semantics.

## Tests

The implementation is complete only when these boundaries are covered:

- `HBMethod` construction, `ModuleBase` lifecycle, placement as tab/window,
  and unique IDs for multiple instances.
- Required selector configuration and canonical period resolution for all six
  framework `TimeUnit` frequencies, including week and quarter handling that
  preserves their canonical strings.
- `AltinnHBDataHandler` active-submission filtering, numeric conversion,
  duplicate/repeated-field handling, and common-schema validation.
- `FakeHBDataHandler` module-flow tests without backend access.
- HB preflight checks for exactly two canonical period levels, requested
  periods matching the input, Vaskify-compatible types, and configured strata.
- Exact explicit Vaskify arguments and result normalization, including
  `median_ratio`.
- Positive, zero, negative, and missing values; preserve Vaskify's
  not-comparable outcomes without reimplementing its eligibility rule.
- Empty results, warning-only Vaskify paths, invalid results, and exceptions;
  verify the installed package's no-eligible-population behavior.
- Stable click-to-selector behavior without rerunning HB.
- Integration coverage against the installed `ssb-vaskify` package.
- Demo browser coverage for import, run, display, and click selection.
