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

Quality and test-coverage expectations are lower for code in experimental. This gives contributors room to iterate on an API before committing to it, without holding up releases of stable modules.

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

This keeps modules loosely coupled and swappable: a user should be able to remove any single module from their app config without other modules breaking.

Note that this is enforced in a test.

### Modules communicate through the variable selector

The only way modules should communicate with each other is the variable selector.

This ensures that the application has a shared list of variables that can be relied on to keep every module on the same page. In practice this means a module declares the variables it needs via VariableSelector and VariableSelectorOption, rather than reading state directly from another module's callbacks or components.

There are methods defined in the VariableSelector to simplify configuration, refer to its documentation for information about how to use it.

### Modules in the package should be as simple as possible to configure

The goal is that a user copying an example from the docs should be able to add a module to their app with minimal edits, and any required configuration should fail loudly and early rather than causing confusing errors later.

Simple configuration in this context is multifaceted and needs to account for how complicated the module is. The point is having as few arguments as possible.

Concretely, a module's __init__ should ideally take no arguments at all — see Aarsregnskap, which takes none and instead reads whatever it needs (e.g. var-foretak, var-aar) from the shared VariableSelector, failing fast with a clear ValueError if a required variable hasn't been configured. When a module genuinely needs setup that can't come from the VariableSelector (e.g. a database connection, a folder path, or a mapping of control IDs), keep that to a small number of required arguments, and prefer sensible defaults for anything optional over exposing many knobs.

### Modules in the package should be accessible to all users with a similar use case, not statistic specific

Modules should be usable for any statistic that follows a proposed data model and not specific to one or very few users. This is to reduce the maintenance burden and noise in the package.

If you find a module that sounds helpful for your case, you should be able to implement it with a reasonable amount of effort.

As an example, a time series module should be based on a data model that is common for time series analysis so that anyone using this methodology can use the module with minimal effort.

### Read and write operations should be database/backend agnostic

Modules should implement a meta class that provides an interface that modules use for getting data required and updating if necessary.

Updates should also be through a MetaDataHandler. As the different backends SSB uses have different ways of handling these. A standard implementation should always be provided that uses ssb-parquedit as it is the most common backend

This mirrors the pattern shown in hello_module.py, where an abstract *MetaDataHandler class defines the data access contract (e.g. get_message/update_message) and concrete handlers implement it against a specific backend. A user can then swap the handler implementation to point at a different database or file format without changing the module itself.

#### Default handlers whenever possible for documented data models

There should be default datahandler implementations for datamodels documented in [docs/datamodels/README.md](datamodels.md).

### Modules must be configurable through yaml files

Being able to use yaml files for config makes configuration less verbose and more declarative. This lowers the bar for setting up and customizing an app, while also making the syntax look more similar between users simplifying sharing of configurations.

In addition, having yaml as the configuration source makes it easier to migrate configs if breaking changes can't be avoided.

Note: inheritance from the base class makes this simple to implement, and parsing is handled centrally by config_parser_yaml so modules don't need to write their own yaml-loading logic.
