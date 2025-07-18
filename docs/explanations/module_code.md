# Module code

Here we will do a deep dive into how the code for modules is structured. We will also touch on why we decided to structure the code in this way.

In order to simplify reuse and maintenance, we wish to keep the code style similar across different modules. We appreciate if you take a look at how other modules are structured and try to follow that general style/logic as far as practically possible.

The code is structured around having a module with functionality and layout created, and then using inheritance to implement the module in the framework.

Pre-requisites for building a new module:
- basic understanding of how to create a class in python.
- knowledge of plotly dash
    - callbacks, input, output, state

## The module structure

Our module structure seeks to accomplish a few things:
- Simplicity: The module should be easy to understand and use.
- Flexibility: The module should be flexible enough to be used in different contexts and with different data sources.
- Reusability: The module should be reusable in different projects and contexts.
- Maintainability: The module should be easy to maintain and extend.

These goals are sometimes contradictory, and we have tried to find a balance between them.

### The base module

Lets take a look at the module structure with a kind of template for a module.

```python
from abc import ABC
from abc import abstractmethod
from ssb_dash_framework import VariableSelector
from ssb_dash_framework import module_validator

class MyModule(ABC):
    _id_number: int = 0

    def __init__(self, inputs: list[str], states: list[str]):
        self.module_number = MyModule._id_number
        self.module_name = self.__class__.__name__
        MyModule._id_number += 1
        self.icon = "?"
        self.label = "my module"
        self.variableselector = VariableSelector(
            selected_inputs=inputs,
            selected_states=states,
        )
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def _create_layout(self):
        return html.Div("My layout", id=f"{self.module_name}{self.module_number}-div")

    @abstractmethod
    def layout():
        pass

    def module_callbacks(self):
        @callback(
            Output(...),
            Input(...),
            State(...)
        )
        def placeholder_callbackfunc(input, state):
            return "My output"
```

#### What is going on here?

- The module is a class that inherits from `ABC`, which is a base class for defining abstract base classes in Python. This allows us to define abstract methods that must be implemented by subclasses.
- The `__init__` method is where we set some general properties for the module, such as the module name and id. We also connect to the variable selector and create the layout for the module. The `__init__` should also take arguments for inputs and states that it connects to through the variable selector.
- `_id_number` is used to make sure that it is possible to have more instances of the class running at the same time. This is why the `__init__` needs to give it +1, so that the number is different next time it is instantiated.
- Assigning `self.module_number` and `self.module_name` is to make it possible to make several instances in the same application, and to simplify identifying which instantiated module is which when debugging and logging.
- The `icon` and `label` attributes are used to make the module simpler to recognize in the layout. These can be set by the user if that makes more sense for your module, but a default value is often practical.
- The `self.variableselector` attribute is used to connect to the variable selector. This allows us to use the variable selector in the module. See separate explanation of how the variable selector works.
- The `_create_layout` method is where we create the layout for the module. It should be set as an attribute of the module called 'module_layout' during the `__init__`.
- The `layout` method is an abstract method that must be implemented by subclasses to define the module's layout. This allows us to define the layout for the module in a consistent way across different modules. For most modules it makes sense to make the layout method abstract to ensure it is possible to implement in many different ways. But if you want it to be useable directly it can instead be an ordinary method and return self.module_layout.
- The `module_callbacks` method is where we create the callbacks for the module. This is where we register the callbacks for the module. Make sure to use the variableselector methods for getting inputs/states/outputs where it is supposed to share data/receive data from the variable selector. It needs to be called in the `__init__`. A tip to ensure it doesn't have name conflicts with id's is to use f"{self.module_name}-{self.module_number}..." in the id-names.
- Running `module_validator(self)` at the end of the `__init__` is useful for ensuring your module has the required attributes.

#### Implementations of the module (mixin classes)

While inheritance increases the complexity of the code, it also allows us to create a more flexible and reusable module structure. By using inheritance, we can create different implementations of modules that share the same interface, making it easier to extend and maintain the code.

As an example we can implement the module above as both a tab and a window module. with very little code, by using the mixin classes.

```python
from ssb_dash_framework import TabImplementation
from ssb_dash_framework import WindowImplementation

class MyModuleTab(TabImplementation, MyModule):
    """MyModule implemented as a tab."""
    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
    ) -> None:
        MyModule.__init__(
            self,
            inputs=inputs,
            states=states,
        )
        TabImplementation.__init__(self)

class MyModuleWindow(WindowImplementation, MyModule):
    """MyModule implemented as a window."""
    def __init__(
        self,
        label: str,
        figure_func: Callable[..., Any],
        inputs: list[str],
        states: list[str] | None = None,
        output: str | None = None,
        clickdata_func: Callable[..., Any] | None = None,
    ) -> None:
        MyModule.__init__(
            self,
            inputs=inputs,
            states=states,
        )
        WindowImplementation.__init__(self)
```

A big advantage of this design is that if we want to add a new way to implement a module, we create a new mixin class. If we want to add more functionality to the window implementation, we edit the WindowImplementation class.

It also makes it simple to validate that a module has the required attributes to play well in the framework and be used as a window.

#### Tips

##### Callback

In order for this code structure to work you need to use @callback and not @app.callback. This is to make the callback code more modular and simplifying imports.

More information: https://community.plotly.com/t/dash-2-0-prerelease-candidate-available/55861#from-dash-import-callback-clientside_callback-5

##### Common annotations for callbacks to make mypy happy

- rowData: list[dict[str, Any]]
- columnDefs: list[dict[str, str]]
- clickData: dict[str, list[dict[str, Any]]]
- error_log: list[dict[str, Any]]

##### Raise PreventUpdate early when possible

It is usually more readable to have PreventUpdate show up early and raised if some condition is not fulfilled, rather than have it as the "else" part of the logic. For short callbacks it doesn't make a huge difference, but for complex or long callbacks it helps a lot to have PreventUpdate at the beginning.

See simple example below.

    @callback(
        Output("some-component", "some-attribute"),
        Input("some-button", "n_clicks")
    )
    def some_callback(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return some_output

## Some choices we have made

During development we have tried numerous different ways of accomplishing the goal of making reusable and simple modules.
- Solutions without using classes were simpler, but also limited the reusability.
- AiO components solved reusability, but were more difficult to maintain and explain to users.

#### Use functions to create the layout

We have chosen to keep the layout creation in a function in order to keep it flexible and simple to understand. A potential benefit of this choice is that we can easily add parameters to the function to customize the layout if necessary at a later time, without changing a lot of other code.

#### Use functions as arguments for getting or updating data

Note that there are exceptions to this when making modules where user friendliness is more important than flexibility.

In order to keep our framework compatible with as many data storage solutions as possible, we have chosen to use functions as arguments to the modules when it needs to get or update data.

This lets the user define the data source and how to get the data from it. This is a bit of a tradeoff, as it makes the code a bit more complex, but it also makes it more flexible and reusable.

#### The user should modify data to fit the requirements of modules

In order to keep the code easier to work with, describe how the required data should look for your module instead of creating functionality to handle different formats. If a user wants to use your module, they need to do the legwork to make their data fit (within reason).

#### Modules should not directly communicate

All communication between modules should go through the VariableSelector. This is to ensure that modules are truly modular, and to avoid making too complex systems.

#### Not using All-in-One (AiO) pattern

Our goal is to make a library of easily reusable, customizable and expandable modules/views. Our approach is a bit of a hybrid design where we get most of the benefits, without introducing all the costs from the AiO design.

The benefits you gain from the AiO component design are in general
- Encapsulation and modularity, as code related to a component is contained within its own class
- Reusability, as all sub-components are connected in the class
- Keeping the layout and callbacks separated and organized within the component
- You can add more of the same component without affecting other components
- They manage their own internal states
- They don't affect each other, potentially leading to easier debugging.

There are some costs involved in using AiO components:
- Increased complexity
- Steeper learning curve
- Potentially harder to track inter-component interactions
- Debugging could be harder, as Dash's callback graph can be harder to interpret in the AiO pattern

We find that our way of structuring the code is easier to understand and use, while still allowing for a high degree of flexibility, reusability and having multiple instances of the same module. We also find that the costs of using AiO components outweigh the benefits in our case as we want the lowest possible barrier to entry for new users to contribute.
