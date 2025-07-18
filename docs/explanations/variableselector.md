# VariableSelector

The `VariableSelector` is a centralized component designed to manage shared inputs and states across different modules in the application. It ensures that updates to a variable (e.g., the year) are reflected consistently across all modules, promoting synchronization and modularity.

This flexibility allows the framework to adapt to different implementations and variable requirements.

## The problem

The problem that needed solving was how we could make sure all modules communicate and show data for the same periods, while keeping each module isolated from eachother.

In addition to this, we needed a way for users to define which information should be shared between modules, and how. And without making the configuration too complex.

### The solution

The solution was the VariableSelector which consists of two classes. These classes used together ensures that a central state storage exists to coordinate all modules.

#### VariableSelectorOption

The VariableSelectorOption consists of a title and id (type is defined in case a use case arises later, but curently only text is used).

The title is what is shown in the interface, while id is used for callbacks.

When initialized, it adds itself to a list used later for coordinating modules through the VariableSelector class. It also makes sure that there are no duplicate options.

To simplify initialization we have created the function `set_variables()` which takes a list of strings and sets up each as an option.

#### VariableSelector

This class will be used to set up most interactions between modules. It contains a class variable containing all currently initialized options and several methods to access them.

During the app setup the main_layout function will create a variable selector module in the app layout

Ideally each module should define its own VariableSelector instance with their own inputs and states specified.

## How it is used in a module

First it needs to be defined as an attribute of the module in the `init` function of a module.

```python
class MyModule(ABC):
    def __init__(self, inputs: list[str], states: list[str]):
        self.inputs = inputs
        self.states = states
        self.variableselector = VariableSelector(
            selected_inputs=inputs,
            selected_states=states,
        )
        self.module_callbacks()
```

Secondly, it needs to be included in callbacks. There are many ways to connect your variable selector to the callbacks. The simplest is to use the built in methods `get_inputs()`, `get_states()`, `get_callback_objects()` and `get_output_object()`.

In order to simplify usage of inputs and states we recommend creating a dict called dynamic_states.

Lets assume you have the input 'identifier' and the states 'year' and 'quarter', and want to return a dataframe filtered on those variables. You could try something like the below example.

```python
    def module_callbacks(self):
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]
        @callback(
            Output("my-ag-grid", "rowData"),
            Output("my-ag-grid", "columnDefs"),
            *dynamic_states
        )
        def placeholder_callbackfunc(*args):
            data = pd.read_parquet(my_path)
            for column, arg in zip(self.inputs+self.states, args):
                data = data.loc[data[column] == arg]
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": True if col == "row_id" else False,
                }
                for col in df.columns
            ]
            return df.to_dict("records"), columns
```

If the code is set up like in the above example, a user creating an instance of MyModule in their application using inputs=["ident"] and states=["year", "month"] will have a module with a callback where a dataframe being read will be filtered on "ident", "year" and "month" before being loaded to an ag grid table.
