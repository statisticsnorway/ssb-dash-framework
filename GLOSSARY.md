# ssb-dash-framework

A library for building Dash apps that let statisticians inspect and edit data. Apps are put together from shared core components and reusable modules.

## Language

### The app

**Core components**:
The shared pieces every app is built on: the variable selector, `app_setup()`, `main_layout()` and the alert handler.
_Avoid_: Frame, framework, base

**App skeleton**:
The smallest working app file: the core components wired together and started, with no modules or only one.
_Avoid_: Frame, boilerplate, template

**App config**:
A YAML file that describes an app: its app settings, its variable selector and which modules it shows as tabs or windows.
_Avoid_: Config file, settings file

### Modules

**Module**:
A self-contained piece of functionality added to an app, such as a table, a figure or an editor.
_Avoid_: Component, plugin, widget

**Tab**:
A module shown in the row of tabs at the top of the app.

**Window**:
A module shown in a pop-up that is opened from a button in the left sidebar.
_Avoid_: Modal, popup

### Data

**Connection**:
The app's single shared link to where its data is stored. It is set once, and every module and function in the app reads through it.
_Avoid_: Database, engine, backend

**Data handler**:
The adapter between a module and the place its data is stored. Swapping the data handler lets a module work with other data without changing the module.
_Avoid_: Fetcher, getter, MetaDataHandler

**Form**:
One Altinn questionnaire (*skjema*), identified by its form name, such as RA-0745.
_Avoid_: Skjema, questionnaire, schema

**Data view**:
One layout inside the DataEditor that shows the data for a given set of forms and tables.
_Avoid_: Editing screen, form view

### Shared state

**Variable selector**:
The panel on the right that holds the values all modules share, such as the selected ident and period. It is the only way modules talk to each other.
_Avoid_: Varselector, filter panel
