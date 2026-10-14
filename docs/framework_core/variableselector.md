# Connecting modules with VariableSelector

Modules communicate through shared selections, not through each other's components:

```text
Selection module -> VariableSelector -> Display module
                         ^
                         |
                  Selector panel
```

Following the [architecture](../architecture.md), each module must also work on its
own. A consumer must not require a particular producer: the user can set the same
selection in the selector panel.

## For app authors: configure the shared selections

`VariableSelectorConfig` maps roles to variable names. For example,
`refnr="Refnr"` names the reference-number variable; it does **not** select a
reference number.

Configure these roles once, **before constructing modules**. Module construction
registers callbacks that resolve the configured variables.

The [hello-world app](../../demo/hello_world/app.py) uses this pattern:

```python
from hello_module import HelloModule, HelloModuleDataHandlerDefault
from ssb_dash_framework import VariableSelectorConfig, app_setup, main_layout

VariableSelectorConfig(refnr="Refnr")
app = app_setup(port=8070)
modules = [
    HelloModule(label="Messages", data_handler=HelloModuleDataHandlerDefault()),
]
app.layout = main_layout(
    window_list=[],
    tab_list=modules,
    default_values={"Refnr": "1"},
)
```

Run this alongside the demo's `hello_module.py`. The `default_values` argument is
an addition to the demo setup: it supplies initial **values**, keyed by variable
title. Without defaults, the selector fields start empty. The default hello-world
handler has messages for reference numbers `"1"` and `"2"`.

For a YAML-configured app, the equivalent role mapping is:

```yaml
app_settings:
  variableselector:
    refnr: Refnr
```

This is an app-config fragment, not a complete app or a declaration of initial
values. Keep module configuration in the app's `modules` section; see the
[YAML reference](../yaml_reference.md).

Available roles and their callback helpers:

| Configuration field | Purpose | Helper |
|---|---|---|
| `refnr` | Unique observation/reference identifier | `get_refnr(...)` |
| `ident` | Primary unit identifier | `get_ident(...)` |
| `time_units` | Time variable and frequency | `get_timevar(...)` |
| `secondary_idents` | Additional identifiers | `get_secondary_ident(...)` |
| `grouping_variables` | Grouping/filtering variables | `get_grouping_vars(...)` |

Configure the roles required by your chosen modules. Missing required scalar roles
raise errors when callback dependencies are resolved; an unset secondary-identifier
or grouping-variable list returns an empty list. Configuration creates selector
options automatically: do not register the same option again.

## For module authors: consume and publish selections

Inherit from `ModuleBase` and use `self.module_id` for local component IDs, as in
[HelloModule](../../demo/hello_world/hello_module.py). Use top-level imports from
`ssb_dash_framework` for the framework's public API.

Call the `VariableSelector` class methods in `module_callbacks`; no per-module
selector instance is needed for this pattern. These helpers return Dash callback
dependencies, **not current values**. Values arrive as callback arguments.

### Choose Input, State, or Output

| Dependency | Intended Dash behavior |
|---|---|
| `VariableSelector.get_refnr(Input)` | Run when the shared reference number changes. |
| `VariableSelector.get_refnr(State)` | Read the reference number when another input triggers the callback. |
| `VariableSelector.get_refnr(Output)` | Publish a reference number to the shared selector. |

### Read: the hello-world example

The callback in [hello_module.py](../../demo/hello_world/hello_module.py) declares:

```python
@callback(
    Output(message_id, "value"),
    VariableSelector.get_refnr(State),
    Input(get_id, "n_clicks"),
    Input(update_id, "n_clicks"),
    State(message_id, "value"),
    prevent_initial_call=True,
)
```

Its arguments are `refnr`, the Get and Update click counts, and the textbox value,
in that order. Using State reads the current reference number when a button is
clicked, without triggering the callback when the reference number changes.
The callback then uses the module's data handler to retrieve or update its message.

The demo creates two HelloModule instances with different data handlers. Both
read the same reference-number selection, but neither reads the other's textbox.
This example **consumes** shared state; updating a stored message is not the same
as publishing a selection.

### Publish: a selection module

This method belongs in a `ModuleBase` subclass whose layout provides a local
`dcc.Dropdown` with ID `f"{self.module_id}-refnr-picker"` and string values such as
`"1"` and `"2"`. Configure the `refnr` role before constructing the module.

```python
from dash import Input, Output, callback
from dash.exceptions import PreventUpdate
from ssb_dash_framework import VariableSelector


def module_callbacks(self) -> None:
    @callback(
        VariableSelector.get_refnr(Output),
        Input(f"{self.module_id}-refnr-picker", "value"),
        prevent_initial_call=True,
    )
    def publish_refnr(refnr: str | None) -> str:
        if not refnr:
            raise PreventUpdate
        return refnr
```

The output helper allows duplicate outputs. Use `prevent_initial_call=True` for
this pattern, and avoid competing callbacks that write different selections at
the same time.

### React: another module

This method belongs in a separate `ModuleBase` subclass with an `html.Div` whose
ID is `f"{self.module_id}-selection"`.

```python
from dash import Input, Output, callback
from ssb_dash_framework import VariableSelector


def module_callbacks(self) -> None:
    @callback(
        Output(f"{self.module_id}-selection", "children"),
        VariableSelector.get_refnr(Input),
    )
    def show_selection(refnr: str | None) -> str:
        return f"Selected reference: {refnr}" if refnr else "Select a reference."
```

This reacts whether the selection came from the producer or the selector panel.
It still works when the producer is removed. Handle empty selections before
querying data, and keep data access behind the module's data-handler interface.
Changing backend data does not automatically notify other modules through the
selector.

### Custom variables and list-returning helpers

For a shared selection without a standard role, register it once in app setup:

```python
from ssb_dash_framework import VariableSelectorOption

VariableSelectorOption("Region", variable_id="region")
```

Modules can consume it with `*VariableSelector.get_input("Region")` in a callback
declaration and publish it with `VariableSelector.get_output_object("Region")`.
Named `get_input()` and `get_state()` return **lists**, even for one variable;
unpack them when declaring positional callback dependencies. The secondary-ident
and grouping-variable helpers also return lists, in configured order.

Prefer role helpers when a standard role fits: they avoid hardcoding an app's
variable names. Do not hardcode another module's IDs, read the selector's private
class attributes as runtime values, or use the deprecated `set_variables()`.

## Troubleshooting

- **Missing role/option:** configure it before module construction; check titles
  and roles rather than wiring directly to another module.
- **Duplicate option:** configuration already registers its variables. Register
  each title and ID only once.
- **Unexpected callback on selection change:** use Input to react to selection
  changes, or State to read the selection only when another input triggers.
- **No data on startup:** supply valid defaults or handle an empty selection.
- **Feedback loops:** do not republish an unchanged selection in response to that
  same selection; keep producer triggers local.

Implementation details: [VariableSelector and VariableSelectorOption](../../src/ssb_dash_framework/setup/variableselector/variableselector.py)
and [VariableSelectorConfig](../../src/ssb_dash_framework/setup/variableselector/set_variables.py).
