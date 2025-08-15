# What is the framework?

The overarching goal of this framework is to streamline the creation of custom data analysis and editing apps based on Dash and facilitate sharing good ideas with other users.

Considering the modular code and how most functionality is optional, exactly what the framework is might be a bit difficult to pin down.

The simplest way to understand what we call the framework would be to look at the shared core components. We have worked towards creating a foundation for creating your own custom app while still having easy access to pre-built components. And to make sure it is simple to add new functionality later if a new module is created that you want to use.

## Modules

An essential part of how we structure the core functionality is to ensure it is possible to create independent modules that can be shared across applications. We cannot solve every problem forever, and for that reason we have structured our code towards enabling modular code. This makes it so that we can create modules that address common needs (like checking an entry in the BoF registry), while enabling the user to create their own modules to solve their more specific needs.

## The different parts of the framework

### VariableSelector

Simply put, the variable selector enables communication between modules without creating a dependency between modules. It is designed to be plug and play, so that you can freely pick and choose what modules to include in your own app. For a more thorough explanation, see the variableselector explanation.

### app_setup()

This function configures the Dash application, enables logging and sets the theme of the application.

It creates a shared starting point for all apps using this library and handles some of the boilerplate code necessary for the styling to work. It ensures that you can start the app in vscode or jupyter and not need to change anything in your code between the two.

The app_setup function also enables logging for the application so that debugging is easier.

### main_layout()

Creating the layout for the app in a clever way is essential for it to be expandable and user friendly. This function creates the main view that will contain core functionality for the application to work and modules.

This function creates the layout for the app, which contains a few different parts.
- A notifications container to display alerts
- A collapsible panel on the right containing the variable selector panel.
- A sidebar on the left with buttons to open modals containing modules
    - Here the AlertHandler (more about this later) module also gets added to the layout.
- A row of tabs at the top that contain modules

This ensures all apps using this library have the same general look and layout, which makes it easier to create reusable components and modules. As long as a module is structured in a few particular ways, it will fit into an existing app. How to structure the module code is explained in its own document.

### Implementations

Inside the library you can also find some helpful classes that aid in implementing a module as a window/modal or a tab, or both. More details about this can be found in the module code explanation.

Having consistent ways to display modules simplifies reuse and makes it simpler to create your own custom module and integrate it with the rest of the framework.

### AlertHandler

During development we realized that a user would need feedback about what is going on when there is no direct visual feedback. If you change a value in the variableselector through a module, getting a message letting you know what was changed might be convenient. If you try to update a value, getting a confirmation of what was changed is also important to ensure that you know the app is working. And if something goes wrong, it is useful to get a visible error message to let you know something went wrong.

The AlertHandler can sort messages by type and modules can send messages to it so that the user gets feedback about what's going on inside the module if necessary.
