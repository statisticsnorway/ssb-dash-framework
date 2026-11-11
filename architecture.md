# HB methodology module architecture

## Scope

This document describes the target architecture for implementing the HB
methodology module. It is an application module in
`src/ssb_dash_framework/modules/`. It does not implement the HB algorithm.
Vaskify remains the calculation provider.

The required production source adapter is `AltinnHBDataHandler`. A prepared
DataFrame or `FakeHBDataHandler` is used only for isolated tests and local
development.

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
4. The HB helper constructs `Detect(hb_input_dataframe, id_nr="unit_id")` and
   calls `hb(...)`.
5. `normalize_hb_result` validates the returned columns and preserves the
   original Vaskify diagnostics.
6. `HBMethod` stores the normalized result for the current run and renders the
   result figure.
7. A graph click reads the stable identifier from Plotly `customdata` and
   updates the configured `VariableSelector` output. It does not rerun HB.

Errors, invalid input, missing comparable observations, and Vaskify failures
are reported through the framework's `AlertHandler` pattern. They must not be
represented as a successful empty result.

## Components and boundaries

| Component | Location | Owns | Must not own |
|---|---|---|---|
| `HBMethod` | `modules/hb_method.py` | Dash layout, callbacks, run state, result figure, click-to-selector behavior | Altinn queries, source reshaping, HB mathematics |
| `HBDataHandlerMeta` | HB data-handler module | Contract and common DataFrame validation | Vaskify invocation |
| `AltinnHBDataHandler` | HB data-handler module | Altinn query, active-submission resolution, field selection, numeric conversion, source context | Plotting, Vaskify arguments, Vaskify result mapping |
| `FakeHBDataHandler` | Test support | Deterministic handler responses for module tests | Production data access |
| `resolve_hb_comparison_periods` | HB helper | Canonical period validation and `(t-1, t)` resolution | Source access |
| `run_hb_vaskify` | HB helper | `Detect` construction and `hb(...)` argument mapping | Altinn-specific logic, Dash callbacks |
| `normalize_hb_result` | HB helper | Stable result schema, flags, diagnostics, and identifier preservation | UI layout |
| `VariableSelector` | Framework setup | Shared selections and selected-unit output | HB calculation state |
| `Vaskify` | External dependency | HB calculation | Framework UI and source access |

The source adapter ends at the common DataFrame boundary. It is not also a
Vaskify adapter.

## Data contracts

### Common HB input DataFrame

One row represents one unit in one period for the selected target variable.

Required columns:

| Column | Type | Meaning |
|---|---|---|
| `unit_id` | `str` | Stable unit identifier used by Vaskify and graph selection |
| `period` | `str` | Framework-canonical period, for example `YYYY`, `YYYY-Q1`, or `YYYY-MM` |
| `value` | numeric | Selected numeric target value |

Optional:

| Column | Meaning |
|---|---|
| `strata` | Grouping value passed to Vaskify when configured |
| selector context columns | Source values needed when updating configured selector outputs |

The adapter must return at most one row per `unit_id` and `period`. Repeated
or ambiguous source values are explicitly resolved or rejected; they are not
silently aggregated.

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
    output_format="wide",
    output_scope="all",
)
```

The normalized result retains the stable identifier, comparison values, period
context, `ratio`, limits, `flag_hb`, and method-specific diagnostics returned
by Vaskify. Flagged, unflagged, and not-comparable states remain distinct.

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
- Required selector configuration and canonical period resolution for each
  supported `TimeUnit`.
- `AltinnHBDataHandler` active-submission filtering, numeric conversion,
  duplicate/repeated-field handling, and common-schema validation.
- `FakeHBDataHandler` module-flow tests without backend access.
- Exact Vaskify arguments and result normalization.
- Empty, invalid, missing, not-comparable, and exception paths.
- Stable click-to-selector behavior without rerunning HB.
- Integration coverage against the installed `ssb-vaskify` package.
- Demo browser coverage for import, run, display, and click selection.
