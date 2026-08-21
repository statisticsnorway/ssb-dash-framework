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

## All code a user is expected to interact with should be a top-level import

In order to reduce chances of breaking changes all classes, functions and so on that a user is expected to interact with should be a top-level import.

This makes sure that the package structure can be re-arranged later without requiring 

## Modules must not depend on other modules

- Each module should have its own folder in modules/.
- Each module must be able to be instantiated on its own, as the sole module in the app.

Enforcement in test.

## Modules communicate through the variable selector

The only way modules should communicate with eachother is the variable selector. It ensures that the application has a shared list of variables that can be relied on to keep every module on the same page.

## Modules must be configurable through yaml files

### Example test
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

## In-development features and modules exists in experimental/



## Experimental features and modules should only be imported using 'from ssb_dash_framework.experimental import ExpModule'

In order to make sure a user understands when something is in-development or experimental, it should not be importable as a top-level import.

## Modules should have tests to prevent breaking changes in the api

```python
from ssb_dash_framework import MyModule
from ssb_dash_framework import MyModuleTab
from ssb_dash_framework import MyModuleWindow


def test_import_MyModule() -> None:
    assert MyModule is not None, "MyModule is not importable"
    assert MyModuleTab is not None, "MyModuleTab is not importable"
    assert MyModuleWindow is not None, "MyModuleWindow is not importable"


def test_instantiation() -> None:
    MyModuleTab()
    MyModuleWindow()
```

## Modules in the package should be as simple as possible to configure



## Modules in the package should be accessible to all users with a similar use case, not statistic specific



### How to add custom modules

See explanation in...

## Read operations should be database/backend agnostic



## Updates to data source should go through models from utils/core_models.py

