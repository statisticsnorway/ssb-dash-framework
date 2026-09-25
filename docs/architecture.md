# Architecture in the package

The goal of the package is to support creation and sharing of reusable modules for analyzing, reviewing and correcting potentially flawed data.

Folder structure in src

```
ssb_dash_framework/
├── assets/        # Assets to make the application pretty
├── config/        # Tools for configuration through yaml files
├── experimental/  # Experimental/in-development features/modules
├── modules/       # Modules that a user can add to their application
├── setup/         # Application layout and initialization
└── utils/         # Generic and reusable helpers
```

## General design

### All code a user is expected to interact with should be a top-level import

In order to reduce chances of breaking changes all classes, functions and so on that a user is expected to interact with should be a top-level import.

This makes sure that the package structure can be re-arranged later without requiring 

### In-development features and modules exists in experimental/

The experimental/ folder exists in order to be able to beta-test features and modules.

If a module or feature is in development and expected to have breaking changes, bugs, performance issues, etc. it can be kept here.

Quality and test-coverage expectations are lower for code in experimental.

### Experimental features and modules should only be imported using 'from ssb_dash_framework.experimental import ExpModule'

In order to make sure a user understands when something is in-development or experimental, it should not be importable as a top-level import.

This ensures that using an experimental feature/module requires an *explicit opt-in*.

### Custom plugin modules is supported

See explanation in docs/

## Module design

Example in [demo/hello_world/hello_module.py](demo/hello_world/hello_module.py).

### Modules inherit from the common base class

This sets up a lot of useful scaffolding for the module to be integrated into the app.

Not required for custom modules imported from outside of the library.

### Modules must not depend on other modules

- Each module should have its own folder in modules/.
- Each module must be able to be instantiated on its own, as the sole module in the app.

Enforcement in test.

### Modules communicate through the variable selector

The only way modules should communicate with each other is the variable selector.

This ensures that the application has a shared list of variables that can be relied on to keep every module on the same page.

### Modules in the package should be as simple as possible to configure

Simple configuration in this context is multifaceted and needs to account for how complicated the module is. The point is having as few arguments as possible. # TODO: write better

### Modules in the package should be accessible to all users with a similar use case, not statistic specific

Modules should be usable for any statistic that follows a proposed data model and not specific to one or very few users. This is to reduce the maintenance burden and noise in the package.

If you find a module that sounds helpful for your case, you should be able to implement it with a reasonable amount of effort.

As an example, a time series module should be based on a data model that is common for time series analysis so that anyone using this methodology can use the module with minimal effort.

### Read operations should be database/backend agnostic

In order to achieve this, modules should implement a meta class that provides an interface that modules use for getting data required.



### Updates to data source should go through TODO: Document



### Modules must be configurable through yaml files

Being able to use yaml files for config makes configuration less verbose and more declarative. This lowers the bar for setting up and customizing an app, while also making the syntax look more similar between users simplifying sharing of configurations.

In addition, having yaml as the configuration source makes it easier to migrate configs if breaking changes can't be avoided. 

Note: inheritance from the base class makes this simple to implement.

#### Example test
```yaml
app_settings:
  port: 8000
  # service_prefix: None
  # stylesheet: None
  enable_logging: false
  logging_level: warning
  log_to_file: false
  variableselector: 
    refnr: refnr
    ident: ident
    time_units:
      aar: 1
    grouping_variables:
      - altinnskjema
      - variabel
  connection:
    type: postgres
    database_url: test
modules:
  tabs:
    - type: MyModule
  windows:
    - type: MyModule
```

```python
from ssb_dash_framework import config_parser_yaml

def test_yaml_MyModule() -> None:
    config_parser_yaml(mymodule.yaml)
```



### Recommended tests for a module

In order to prevent accidentally introducing breaking changes, at a minimum modules should have tests to ensure that the public API does not change.







