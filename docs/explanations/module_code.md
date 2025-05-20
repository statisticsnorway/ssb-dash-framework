# Module code

Here we will do a deep dive into how the code for modules is structured and why. We will also touch on what we have tried before and the reasons for doing it differently.

## The module structure

Our module structure seeks to accomplish a few things:
- Simplicity: The module should be easy to understand and use.
- Flexibility: The module should be flexible enough to be used in different contexts and with different data sources.
- Reusability: The module should be reusable in different projects and contexts.
- Maintainability: The module should be easy to maintain and extend.

These goals are sometimes contradictory, and we have tried to find a balance between them.

### Overview of the module structure

The diagram below shows an overview of the module structure. We will go through each part of the module in detail, the diagram is intended to show how they relate to eachother.

![module_structure_diagram](../illustrations/module_structure.drawio.svg)

### The base module

Lets take a look at the module structure with a kind of template for a module.

```python
from abc import ABC
from abc import abstractmethod
from ssb_dash_framework import VariableSelector

class MyModule(ABC):
    _id_number = 0 # In order to give each module a unique id

    def __init__(self, inputs, states):
        # First set some general properties
        self.module_name = self.__class__.__name__
        self._id = MyModule._id_number
        MyModule._id_number += 1

        self.variableselector = VariableSelector( # Connect to variable selector
            selected_inputs=[inputs],
            selected_states=[states],
        )

        self.module_layout = slef._create_layout() # Set the layout as an attribute
        self.module_callbacks() # Register callbacks

    def _create_layout(self):
        # Create the layout for the module inside a html.Div
        return html.Div()

    def module_callbacks(self):
        # Create the callbacks for the module in this function
        # You should always use "{self._id}..." in the callback ids to make sure the ids are unique
        pass

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the EditingTable module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass
```

#### What is going on here?

- The module is a class that inherits from `ABC`, which is a base class for defining abstract base classes in Python. This allows us to define abstract methods that must be implemented by subclasses.
- The `__init__` method is where we set some general properties for the module, such as the module name and id. We also connect to the variable selector and create the layout for the module.
- The `_create_layout` method is where we create the layout for the module. It should be set as an attribute of the module.
- The `module_callbacks` method is where we create the callbacks for the module. This is where we register the callbacks for the module.
- The `layout` method is an abstract method that must be implemented by subclasses to define the module's layout. This allows us to define the layout for the module in a consistent way across different modules.
- The `self.variableselector` attribute is used to connect to the variable selector. This allows us to use the variable selector in the module.

### Implementations of the module (mixin classes)

While inheritance increases the complexity of the code, it also allows us to create a more flexible and reusable module structure. By using inheritance, we can create different implementations of modules that share the same interface, making it easier to extend and maintain the code.

As an example we can implement the module above as both a tab and a window module. with little boilerplate code.

```python
class MyModuleTab(MyModule, TabImplementation):
    def __init__(self,inputs, states):
        MyModule().__init__(self, inputs, states)

        TabImplementation.__init__(
            self,
        )

    def layout(self) -> html.Div:
        """Generate the layout for the module as a tab."""
        layout = TabImplementation.layout(self)
        logger.debug("Generated layout")
        return layout

class MyModuleWindow(MyModule, WindowImplementation):
    def __init__(self,inputs, states):
        MyModule().__init__(self, inputs, states)

        WindowImplementation.__init__(
            self,
        )

    def layout(self) -> html.Div:
        """Generate the layout for the module as a window."""
        layout = WindowImplementation.layout(self)
        logger.debug("Generated layout")
        return layout
```

## Some choices we have made

#### Use functions to create the layout

We have chosen to keep the layout creation in a function in order to keep it flexible and simple to understand. A potential benefit of this choice is that we can easily add parameters to the function to customize the layout if necessary at a later time.

#### Using functions as arguments

In order to keep our framework compatible with as many data storage solutions as possible, we have chosen to use functions as arguments to the module. This lets the user define the data source and how to get the data from it. This is a bit of a tradeoff, as it makes the code a bit more complex, but it also makes it more flexible and reusable.



#### Why not use All-in-One (AiO) modules

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

We find that our way of structuring the code is easier to understand and use, while still allowing for a high degree of flexibility and reusability. We also find that the costs of using AiO components outweigh the benefits in our case as we want the lowest possible barrier to entry for new users.


