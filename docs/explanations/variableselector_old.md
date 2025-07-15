# VariableSelector

The `VariableSelector` is a centralized component designed to manage shared inputs and states across different modules in the application. It ensures that updates to a variable (e.g., the year) are reflected consistently across all modules, promoting synchronization and modularity.

This flexibility allows the framework to adapt to different implementations and variable requirements.

## The two parts

1. **`VariableSelectorOption`**: Each variable is represented as a `VariableSelectorOption`, which defines its name, type, and unique ID. These options are registered globally and can be used by any `VariableSelector`.

2. **`VariableSelector`**: This class manages the selected variables (inputs and states) for a module. It validates the variables, provides Dash components (e.g., `Input`, `State`, `Output`), and provides methods to retrieve Dash components for interacting with the variables.

## Connecting your module to the VariableSelector

To connect your module to the `VariableSelector`, follow these steps:

1. Use the module's `VariableSelector` instance to retrieve the dynamic states:

    ```python
    dynamic_states = [
        *self.variableselector.get_inputs(),
        *self.variableselector.get_states(),
    ]
    ```

    This should be done inside the module's `callbacks()` function.

2. Include the `dynamic_states` in your callbacks:

    ```python
    @callback(
        Output("your-component", "your-attribute"),
        *dynamic_states,
    )
    def your_callback_function(*args):
        # Access values from the VariableSelector using *args
        # Perform your logic here
    ```

3. Use the `debugger_modal` (found in `ssb_dash_framework/utils/debugger_modal.py`) to inspect the values passed from the `VariableSelector` and ensure everything is working as expected.

By following these steps, your module will be seamlessly connected to the `VariableSelector` in the `main_layout`. This ensures that updates to shared variables are automatically reflected across all connected modules.
