# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [MIT license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

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

# Our design and making a new module

Pre-requisites for building a new module:
- basic understanding of how to create a class in python.
- knowledge of plotly dash
    - callbacks, input, output, state

In order to simplify reuse and maintenance, we wish to keep the code style similar across different modules. We appreciate if you take a look at how other modules are structured and try to follow that general style/logic as far as practically possible.

## The class structure



### Implementing as modal

### Implementing as tab


## Variableselector

See the docstrings for VariableSelector and VariableSelectorOption to get familiar with how they work.

The idea behind the Variableselector is that you have one module in the application keeping track of inputs and states for callbacks across modules. This means that updating one field in the Variable selector in your app, for an example the year, will make all modules in your app show the same year.

In order to account for different implementations of the framework requiring different variables, it has been built with flexibility in mind.

### Connecting your module to the variable selector

Note: You can use the ssb_dash_framework/utils/debugger_modal.py to get familiar with how this works in practice.

Use the module's VariableSelector to get the dynamic_states list.

    dynamic_states = [
        self.variableselector.get_inputs(),
        self.variableselector.get_states(),
    ]

This should be done inside the modules callbacks() function.

Now in each callback, make sure to include the dynamic_states object

    @callback(
        Output("your component", "your attribute"),
        *dynamic_states,
    )
    def your_callback_function(*dynamic_states):
        do some useful stuff

And that should be everything you need to have your module connected to the VariableSelector component in the main_layout. You can use *args in functions to access values from the

## Our design choices

Throughout development we have made some conscious choices regarding the structure of the code, data and how to solve certain issues.

Here we shall explain ourselves as well as memory permits. Hopefully that keeps us from repeating mistakes and makes the overall structure of the code easier to understand.

### We assume a long data format

The reason for this is simple. Different users will have different amounts of observations, variables and aggregation levels.

Using a few different files/tables and the long format makes it simple to keep track of observations, characteristics about the observations and data about/from the observatins. With a long format we can simplify the data structure so that adapting modules to different data is simpler.

With a long format containing columns identifying the observation, the variable and the variable value it is a lot simpler to make something that fits all data with minimal adjustments to the module itself.

### Include the layout as a method in the class

Oppdateres med ny arve logikk

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

### All in one (AiO) components

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

## Tips and tricks

#### Fix mypy complaining about callbacks

Add "# type: ignore[misc]" to decorator to avoid mypy reporting it as an error.

    @callback(  # type: ignore[misc]
        Input(),
        Output()
    )

#### Common annotations for callbacks to make mypy happy

- rowData: list[dict[str, Any]]
- columnDefs: list[dict[str, str]]
- clickData: dict[str, list[dict[str, Any]]]
- error_log: list[dict[str, Any]]

#### Raise PreventUpdate early when possible

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
poetry run ssb-sirius-dash
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

[mit license]: https://opensource.org/licenses/MIT
[source code]: https://github.com/statisticsnorway/ssb-sirius-dash
[documentation]: https://statisticsnorway.github.io/ssb-sirius-dash
[issue tracker]: https://github.com/statisticsnorway/ssb-sirius-dash/issues
[pipx]: https://pipx.pypa.io/
[poetry]: https://python-poetry.org/
[nox]: https://nox.thea.codes/
[nox-poetry]: https://nox-poetry.readthedocs.io/
[pytest]: https://pytest.readthedocs.io/
[pull request]: https://github.com/statisticsnorway/ssb-sirius-dash/pulls

<!-- github-only -->

[code of conduct]: CODE_OF_CONDUCT.md
