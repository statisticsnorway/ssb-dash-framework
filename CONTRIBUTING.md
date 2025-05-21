# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [GNU license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

## Table of contents

1. [Our Design and Making a New Module](#our-design-and-making-a-new-module)
   - [The Class Structure](#the-class-structure)
   - [VariableSelector](#variableselector)

2. [Our Design Choices](#our-design-choices)

3. [Tips and Tricks](#tips-and-tricks)

4. [How to Set Up Your Development Environment](#how-to-set-up-your-development-environment)

5. [How to Test the Project](#how-to-test-the-project)

6. [How to Submit Changes](#how-to-submit-changes)

7. [How to Report a Bug](#how-to-report-a-bug)

8. [How to Request a Feature](#how-to-request-a-feature)

## Our design and making a new module

Pre-requisites for building a new module:
- basic understanding of how to create a class in python.
- knowledge of plotly dash
    - callbacks, input, output, state

In order to simplify reuse and maintenance, we wish to keep the code style similar across different modules. We appreciate if you take a look at how other modules are structured and try to follow that general style/logic as far as practically possible.

The code is structured around having a module with functionality and layout created, and then using inheritance to implement the module in the framework.

### The class structure

We structure the code with an abstract class that contains all of the necessary dash components and functionality to be a fully functional module, and then create classes that inherit from it and adds a specific implementation. This structure allows the module to be reused in different ways.

#### Base class

When creating a new module, start by creating the base class as shown in the example below.

```python
from abc import ABC, abstractmethod

class MyModule(ABC):

    _id_number = 0 # This is used to give each module a unique id in callbacks, so that you can have multiple instances of the same module in the same app.

    def __init__(self):

        self._mymodule_n = MyModule._id_number
        MyModule._id_number += 1
        # Make sure the instance has a name as well, this is used to make callbacks easier to troubleshoot when you implement it as a window.
        self.module_name = self.__class__.__name__
        # Some of your stuff here
        self.module_layout = self._create_layout()
        self.module_callbacks()


    def _create_layout(self) -> html.Div:
        return html.Div(
            # create your layout here
        )

    def module_callbacks(self) -> None:
        """Generates the callbacks for MyModule
        """
        # create your callbacks here
        # @callback() # Include {self._mymodule_n} in the callback id string
        # def callback_func():


    @abstractmethod
    def layout(self) -> html.Div: # You need to include this as an abstract method, so that the inheriting classes can implement it.
        """Generate the layout for the MyModule module.

        Returns:
            html.Div: A Div element containing...
        """
        pass
```

During the init you at a minimum need to:
- set the module id number.
- set the module name.
- create the module layout.
- register the module callbacks.

In order to keep it consistent between modules, it is a good idea to name the function that creates the layout for your module "_create_layout".

The base class also needs to have a function that defines and registers its callbacks, and that function needs to run during the init of the class. This is to ensure that the callbacks are registered.

#### Implementing as tab

The tab variant of your module is pretty simple to implement. First create the file

    src/ssb_sirius_dash/tabs/mymodule_tab.py

And then adapt the code below to your module.

```python
class MyModuleTab(MyModule):
    def __init__(self): # Remember to pass the arguments your base class requires
        super().__init__() # Into this

    def layout(self) -> html.Div:
        """Generate the layout for the FrisokTab.

        Returns:
            html.Div: A Div element containing the text area for SQL queries,
                      input for partitions, a button to run the query,
                      and a Dash AgGrid table for displaying results.
        """
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
```

#### Implementing as window

Making your module available as a window involves a bit more work, as you need to include a mixin class that handles the window functionality. Using this mixin class allows you to create a modal window for your module without having to implement all the functionality from scratch.

In order to add your module as a window, start by creating the file

    src/ssb_sirius_dash/window/mymodule_window.py

And then adapt the code below to your module.

```python
from .modules import MyModule
from ..utils import WindowImplementation

class MyModuleWindow(MyModule, WindowImplementation):
    def __init__(self, *args):
        MyModule.__init__(self, *args) # Put in your arguments here
        WindowImplementation.__init__(self)

    def layout(self) -> html.Div:
        """Generate the layout for the modal window using the WindowImplementation method."""
        layout = WindowImplementation.layout(self)
        return layout
```

##### What does the WindowImplementation do?

The `WindowImplementation` class is a mixin that provides the necessary functionality to create a modal window for your module. It handles the layout and callbacks for opening and closing the window, as well as managing the state of the window.
The `WindowImplementation` class is designed to be used in conjunction with your module's base class. It provides a consistent way to create modal windows for different modules, ensuring that the window behaves similarly across the application.
It also allows you to change how it implements your layout by overrriding the get_module_layout method in WindowImplementation.

### VariableSelector

The `VariableSelector` is a centralized component designed to manage shared inputs and states across different modules in the application. It ensures that updates to a variable (e.g., the year) are reflected consistently across all modules, promoting synchronization and modularity.

This flexibility allows the framework to adapt to different implementations and variable requirements.

#### The two parts

1. **`VariableSelectorOption`**: Each variable is represented as a `VariableSelectorOption`, which defines its name, type, and unique ID. These options are registered globally and can be used by any `VariableSelector`.

2. **`VariableSelector`**: This class manages the selected variables (inputs and states) for a module. It validates the variables, provides Dash components (e.g., `Input`, `State`, `Output`), and provides methods to retrieve Dash components for interacting with the variables.

#### Connecting your module to the VariableSelector

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

### Tests for your module

Your module needs to have a unit test making sure the top level import works as intended. In order to keep the code flexible and reduce the amount of breaking changes, we strongly encourage users to import from the top level. Because of this we need a unit test to ensure this functionality remains intact.

```python
from ssb_dash_framework import MyModule
```

Therefore, your test should look something like this:

```python
def test_import():
    from ssb_dash_framework import MyModule
    assert MyModule is not None
```

## Our design choices

Throughout development we have made some conscious choices regarding the structure of the code, data and how to solve certain issues.

Here we shall explain ourselves as well as memory permits. Hopefully that keeps us from repeating mistakes and makes the overall structure of the code easier to understand.

### Modules do not directly communicate

All communication between modules should go through the VariableSelector. This is to ensure that modules are truly modular, and to avoid making too complex systems.

### We assume a long data format

The reason for this is simple. Different users will have different amounts of observations, variables and aggregation levels.

Using a few different files/tables and the long format makes it simple to keep track of observations, characteristics about the observations and data about/from the observatins. With a long format we can simplify the data structure so that adapting modules to different data is simpler.

With a long format containing columns identifying the observation, the variable and the variable value it is a lot simpler to make something that fits all data with minimal adjustments to the module itself.

### Use @callback

In order for this code structure to work you need to use @callback and not @app.callback. This is to make the callback code more modular and simplifying imports.

More information: https://community.plotly.com/t/dash-2-0-prerelease-candidate-available/55861#from-dash-import-callback-clientside_callback-5

### The user should modify data to fit the requirements of your module

In order to keep the code easier to work with, describe how the required data should look instead of creating functionality to handle different formats. If a user wants to use your module, they need to do the legwork to make their data fit (within reason).

### User defined functions

If you need the user to define a function for some use case in your module you can include user-created functions in the class by adding a parameter to the __init__:

    class Module:
        def __init__(self, custom_function):
            self.custom_function = custom_function

An example of a use-case for this is a function to get/transform data to adhere to a specific format, that might be different from the data connected to the application (transforming long data to wide data is an example of this).

## Tips and tricks

### Fix mypy complaining about callbacks

Add "# type: ignore[misc]" to decorator to avoid mypy reporting it as an error.

    @callback(
        Input(),
        Output()
    )

### Common annotations for callbacks to make mypy happy

- rowData: list[dict[str, Any]]
- columnDefs: list[dict[str, str]]
- clickData: dict[str, list[dict[str, Any]]]
- error_log: list[dict[str, Any]]

### Raise PreventUpdate early when possible

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


## How to set up your development environment

You need Python 3.10+ and the following tools:

- [Poetry]
- [Nox]
- [nox-poetry]

Install [pipx]:

```console
python -m pip install --user pipx
python -m pipx ensurepath
```

Install [Poetry]:

```console
pipx install poetry
```

Install [Nox] and [nox-poetry]:

```console
pipx install nox
pipx inject nox nox-poetry
```

Install the pre-commit hooks

```console
nox --session=pre-commit -- install
```

Install the package with development requirements:

```console
poetry install
```

You can now run an interactive Python session, or your app:

```console
poetry run python
poetry run ssb-dash-framework
```

## How to test the project

Run the full test suite:

```console
nox
```

List the available Nox sessions:

```console
nox --list-sessions
```

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

```console
nox --session=tests
```

Unit tests are located in the _tests_ directory,
and are written using the [pytest] testing framework.

## How to submit changes

Open a [pull request] to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
nox --session=pre-commit -- install
```

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.

## How to report a bug

Report bugs on the [Issue Tracker].

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

## How to request a feature

Request features on the [Issue Tracker].

[GNU license]: https://opensource.org/license/gpl-3-0
[source code]: https://github.com/statisticsnorway/ssb-dash-framework
[documentation]: https://statisticsnorway.github.io/ssb-dash-framework
[issue tracker]: https://github.com/statisticsnorway/ssb-dash-framework/issues
[pipx]: https://pipx.pypa.io/
[poetry]: https://python-poetry.org/
[nox]: https://nox.thea.codes/
[nox-poetry]: https://nox-poetry.readthedocs.io/
[pytest]: https://pytest.readthedocs.io/
[pull request]: https://github.com/statisticsnorway/ssb-dash-framework/pulls

<!-- github-only -->

[code of conduct]: CODE_OF_CONDUCT.md
