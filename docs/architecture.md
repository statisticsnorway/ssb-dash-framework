# Architecture in the package

ssb_dash_framework/
├── assets/        # Assets to make the application pretty
├── config/        # Tools for configuration through yaml files
├── experimental/  # Experimental/in-development features/modules
├── modules/       # Modules that a user can add to their application
├── setup/         # Application layout and initialization
└── utils/         # Generic and reusable helpers

## All code a user is expected to interact with should be a top-level import

In order to reduce chances of breaking changes all classes, functions and so on that a user is expected to interact with should be a top-level import.

This makes sure that the package structure can be re-arranged later without requiring 

## Modules must not depend on other modules

- Each module should have its own folder in modules/.
- Each module must be able to be instantiated on its own, as the sole module in the app.

```python
from ssb_dash_framework import MyModule
from ssb_dash_framework import MyModuleTab
from ssb_dash_framework import MyModuleWindow


def test_import_MyModule() -> None:
    assert MyModule is not None, "MyModule is not importable"
    assert MyModuleTab is not None, "MyModuleTab is not importable"
    assert MyModuleWindow is not None, "MyModuleWindow is not importable"


def test_instantiation_default_connection() -> None:
    MyModuleTab()
    MyModuleWindow()


def test_instantiation_custom_conn(ibis_polars_conn) -> None:
    MyModuleTab(conn=ibis_polars_conn)
    MyModuleWindow(conn=ibis_polars_conn)
```

## Modules communicate through the variable selector



## Modules must be configurable through yaml files



## Read operations should be database/backend agnostic



## Updates to data source should go through models from utils/core_models.py



## In-development features exists in experimental/



## Experimental features should only be imported using 'from ssb_dash_framework.experimental.feature'

In order to make sure a user understands when something is in-development or experimental, it should not be importable as a top-level import.
