# YAML configuration reference

An app can be configured with a yaml file instead of Python code. This page lists
every class that can be created from yaml, and which arguments each class accepts.

## Key concepts

**Yaml maps 1-to-1 onto Python arguments.** Every key in a yaml block is passed as a
keyword argument with the same name to the class constructor (`__init__`). If you
know how to create a class in Python, you know how to configure it in yaml, and the
other way around. These two are equivalent:

```python
FreeSearch(conn=None)
```

```yaml
- type: FreeSearch
  conn: null
```

**`type` selects the class.** The value of `type` must match the class name exactly.
All other keys in the block become arguments. Unknown keys are rejected with an
error listing the valid arguments.

**The app config file.** The root of an app config has two sections:

```yaml
app_settings:          # Arguments to app_setup(), and the variable selector config
  port: 8070
  variableselector:
    ident: ident
modules:
  tabs:                # Modules shown as tabs
    - type: SomeModule
  windows:             # Modules shown as windows (modals) opened from the sidebar
    - type: OtherModule
```

Whether a module is a tab or a window is decided by which list it is placed in, so
`as_type` should not be set in yaml.

**Nested classes.** Some arguments expect other configurable classes. These are
written as nested blocks with their own `type` key, following the same rules.

**Splitting files.** Use `!include path/to/file.yaml` to insert the content of another
yaml file. Relative paths are resolved from the folder of the including file.

**Custom `from_yaml`.** Most classes use the default loader, which passes the yaml
keys straight to the constructor. Some classes need to build objects from the yaml
before calling the constructor, and define their own `from_yaml`. This is noted in
the class section below, and the expected structure may differ from the
constructor arguments listed.

<!-- Auto-generated. Do not edit, regenerate with `python -m ssb_dash_framework.config.docgen`. -->

## Contents

- [Aarsregnskap](#aarsregnskap)
- [ControlView](#controlview)
- [BofInformation](#bofinformation)
- [Canvas](#canvas)
- [FigureDisplay](#figuredisplay)
- [MapDisplay](#mapdisplay)
- [MultiModule](#multimodule)
- [EditingTable](#editingtable)
- [StandardDataHandler](#standarddatahandler)
- [DataEditor](#dataeditor)
- [ContextABC](#contextabc)
- [DataViewCustom](#dataviewcustom)
- [DataEditorTable](#dataeditortable)
- [DataEditorContactInfo](#dataeditorcontactinfo)
- [DataEditorHelperButton](#dataeditorhelperbutton)
- [DataEditorHistory](#dataeditorhistory)
- [DataEditorSupportTables](#dataeditorsupporttables)
- [DataEditorInfoRow](#dataeditorinforow)
- [DataEditorSidebarComment](#dataeditorsidebarcomment)
- [DataEditorSidebarEditingStatus](#dataeditorsidebareditingstatus)
- [DataEditorTableSelector](#dataeditortableselector)
- [ParquetEditor](#parqueteditor)
- [ParquetEditorChangelog](#parqueteditorchangelog)
- [SkjemapdfViewer](#skjemapdfviewer)
- [VariableSelectorConfig](#variableselectorconfig)

## Aarsregnskap

Import path: `ssb_dash_framework.modules.aarsregnskap.Aarsregnskap`

Module for displaying annual financial statements (Årsregnskap).

Takes no arguments.

```yaml
- type: Aarsregnskap
```

## ControlView

Import path: `ssb_dash_framework.modules.altinn_control_view.ControlView`

Provides a layout and functionality for a modal that offers a tabular view of the controls.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `control_dict` | `dict[str, Any]` | required | A dictionary with one control class per skjema. |
| `outputs` | `list[str] \| None` | `None` | Variable selector fields to output to. Defaults to ['ident'] |

```yaml
- type: ControlView
  control_dict: <control_dict>
```

## BofInformation

Import path: `ssb_dash_framework.modules.bofregistry.BofInformation`

Module for displaying and managing information from BoF.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str \| None` | `None` | The label for the tab, displayed as "BoF Foretak". |
| `variableselector_foretak_name` | `str` | `'foretak'` | The name of the variable selector that holds the foretak number, default is "foretak". |

```yaml
- type: BofInformation
```

## Canvas

Import path: `ssb_dash_framework.modules.building_blocks.canvas.Canvas`

The Canvas module is a base class that simplifies adding your own unique view to the framework.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str` | required | The label for the canvas, used in the UI. |
| `content` | `Div` | required | A Dash layout that will be displayed in the canvas. Can contain other building block modules. |

```yaml
- type: Canvas
  label: <label>
  content: <content>
```

## FigureDisplay

Import path: `ssb_dash_framework.modules.building_blocks.figuredisplay.FigureDisplay`

This module is used to display a plotly figure in the editing framework.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str` | required | The label for the module. |
| `figure_func` | `Callable[..., Any]` | required | A function that returns a plotly figure. It should accept the dynamic states as arguments. |
| `inputs` | `list[str]` | required | A list of input variable names to be used in the figure function. |
| `states` | `list[str] \| None` | `None` | A list of state variable names to be used in the figure function. Defaults to None. |
| `output` | `str \| None` | `None` | The name of the output variable to which the click data will be sent. If provided, the click data will be processed and sent to this variable. If None, no click data will be processed. Defaults to None. |
| `clickdata_func` | `Callable[..., Any] \| None` | `None` | A function to process the click data. It should accept the click data as an argument and return a value to be sent to the output variable. If None, no click data will be processed. Defaults to None. |

Additional keyword arguments are accepted.

```yaml
- type: FigureDisplay
  label: <label>
  figure_func: <figure_func>
  inputs: <inputs>
```

## MapDisplay

Import path: `ssb_dash_framework.modules.building_blocks.map_display.MapDisplay`

Module used for creating a map visualization.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `map_type` | `str` | required | The kind of map to be made, currently supports kommune and fylke. |
| `inputs` | `list[str]` | required | List the variables from the variable selector that should trigger an update to the map |
| `states` | `list[str]` | required | List the variables from the variable selector that should be used in the get_data_func, but not trigger an update to the map |
| `get_data_func` | `Callable[..., Any]` | required | Function that when given aar_var, *inputs and *states as arguments returns a dataframe with a column with the same name as the map type and 'value' for the value. |
| `clickdata_func` | `Callable[..., Any] \| None` | `None` | A function to process the click data. It should accept the click data as an argument and return a value to be sent to the output variable. If None, no click data will be processed. Defaults to None. |
| `output_var` | `str \| None` | `None` | Variable selector output for clickdata. Defaults to the same value as map_type. |
| `label` | `str \| None` | `None` | Label for the button / tab for the module. Defaults to 'Kart {map_type}' |
| `colorscale` | `str` | `'YlGn'` | Can be used to select another colorscale. See plotly documentation for options. |

```yaml
- type: MapDisplay
  map_type: <map_type>
  inputs: <inputs>
  states: <states>
  get_data_func: <get_data_func>
```

## MultiModule

Import path: `ssb_dash_framework.modules.building_blocks.multimodule.MultiModule`

Generic class for switching between modules with a label and module_layout.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str` | required | The label for the MultiModule. |
| `module_list` | `list[Any]` | required | A list of modules to switch between. Each module should have a `label` and `module_layout` attribute. |

```yaml
- type: MultiModule
  label: <label>
  module_list: <module_list>
```

## EditingTable

Import path: `ssb_dash_framework.modules.building_blocks.tables.EditingTable`

A reusable and flexible Dash component for editing tabular data.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str` | required | The label for the tab or component, used for display purposes. |
| `inputs` | `list[str]` | required | A list of input variable names that will trigger callbacks. |
| `states` | `list[str]` | required | A list of state variable names used that will not trigger callbacks, but can be provided as args. |
| `get_data_func` | `Callable[..., Any]` | required | A function that returns a pandas dataframe. |
| `update_table_func` | `Callable[..., Any] \| None` | `None` | A function for updating data based on edits in the AgGrid. Note, the update_table_func is provided with the dict from cellValueChanged[0] from the Dash AgGrid in addition the inputs and states values. |
| `output` | `str \| list[str] \| None` | `None` | Identifier for the table, used for callbacks. Defaults to None. |
| `output_varselector_name` | `str \| list[str] \| None` | `None` | Identifier for the variable selector. If list, make sure it is in the same order as output. Defaults to None. If `output` is provided but `output_varselector_name` is not, it will default to the value of `output`. |
| `number_format` | `str \| None` | `None` | A d3 format string for formatting numeric values in the table. Defaults to None. If None, it will default to "d3.format(',.1f')(params.value).replace(/,/g, ' ')". |

Additional keyword arguments are accepted.

```yaml
- type: EditingTable
  label: <label>
  inputs: <inputs>
  states: <states>
  get_data_func: <get_data_func>
```

## StandardDataHandler

Import path: `ssb_dash_framework.modules.data_editor.default_getter.getter.StandardDataHandler`

Takes no arguments.

```yaml
- type: StandardDataHandler
```

## DataEditor

Import path: `ssb_dash_framework.modules.data_editor.editor.DataEditor`

The main micro-editing module that orchestrates layout, sidebars, and custom forms.

**Custom loader:** `from_yaml(*args: Any, **kwargs: dict | list | str | int)`.

Configures and instantiates the DataEditor module dynamically from a configuration dict/yaml.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `settings` | `EditorSettings` | required | Central configuration for columns, tables, and form options. |
| `data_handler` | `FetcherMeta` | required | Query and persistence handler implementing FetcherMeta. |
| `inforow` | `dict \| None` | `None` | Variable mapping configuration for the metadata display row. |
| `buttons` | `list[ModuleABC \| ContextABC] \| None` | `None` | List of helper buttons/modals shown above the main content view. |
| `sidebar` | `list[ModuleABC \| ContextABC] \| None` | `None` | List of interactive sidebar widgets shown in the left column. |
| `dataview` | `list[ModuleABC] \| None` | `None` | List of views (e.g. DataEditorTable or DataViewCustom) for standard or customized forms. |
| `enable_table_selector` | `bool` | `True` | Optional flag to toggle the data source selector. |

```yaml
- type: DataEditor
  settings: <settings>
  data_handler: <data_handler>
```

## ContextABC

Import path: `ssb_dash_framework.modules.data_editor.meta.ContextABC`

Base class for defining a module operating within a specific database and layout context.

Takes no arguments.

Additional keyword arguments are accepted.

```yaml
- type: ContextABC
```

## DataViewCustom

Import path: `ssb_dash_framework.modules.data_editor.modules.data_view.custom_view.DataViewCustom`

DataView with a very flexible layout made to be tailored to specific needs.

**Custom loader:** `from_yaml(*args, **kwargs)`.

Configures and instantiates the custom view dynamically from configuration dictionary properties.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `layout` | `list` | required |  |

Additional keyword arguments are accepted.

```yaml
- type: DataViewCustom
  layout: <layout>
```

## DataEditorTable

Import path: `ssb_dash_framework.modules.data_editor.modules.data_view.table_view.DataEditorTable`

Requires table selector.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `settings` | `EditorSettings` | required | Central configurations defining data tables, fields, and options. |

```yaml
- type: DataEditorTable
  settings: <settings>
```

## DataEditorContactInfo

Import path: `ssb_dash_framework.modules.data_editor.modules.helper_buttons.contact_info.DataEditorContactInfo`

This module provides supporting tables for the DataEditor.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `applies_to_tables` | `list[str] \| None` | `None` |  |
| `applies_to_forms` | `list[str] \| None` | `None` |  |

```yaml
- type: DataEditorContactInfo
```

## DataEditorHelperButton

Import path: `ssb_dash_framework.modules.data_editor.modules.helper_buttons.editor_helper_button.DataEditorHelperButton`

Base class for defining a helper button component.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `label` | `str` | required | The label to put on the button. |

```yaml
- type: DataEditorHelperButton
  label: <label>
```

## DataEditorHistory

Import path: `ssb_dash_framework.modules.data_editor.modules.helper_buttons.history.DataEditorHistory`

This module provides supporting tables for the DataEditor.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `applies_to_tables` | `list[str] \| None` | `None` | Optional override listing applicable database tables. |
| `applies_to_forms` | `list[str] \| None` | `None` | Optional override listing applicable questionnaire forms. |

```yaml
- type: DataEditorHistory
```

## DataEditorSupportTables

Import path: `ssb_dash_framework.modules.data_editor.modules.helper_buttons.supporting_table.DataEditorSupportTables`

Module providing a collection of supporting reference tables inside a modal.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `applies_to_tables` | `list[str] \| None` | `None` | Optional override listing applicable database tables. |
| `applies_to_forms` | `list[str] \| None` | `None` | Optional override listing applicable questionnaire forms. |

```yaml
- type: DataEditorSupportTables
```

## DataEditorInfoRow

Import path: `ssb_dash_framework.modules.data_editor.modules.inforow.info_row.DataEditorInfoRow`

Creates a row of cards at top of DataEditor showing key variables for selected form.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `variables` | `dict[str, Any] \| list[InfoRowField]` | required | A list of InfoRowField objects or a dict where the key is the label for the variable. In a dict the values must be {source: "sourcetable", variable_name: "variable name in table"} |

```yaml
- type: DataEditorInfoRow
  variables: <variables>
```

## DataEditorSidebarComment

Import path: `ssb_dash_framework.modules.data_editor.modules.sidebar.editing_comment_view.DataEditorSidebarComment`

Sidebar component for showing a field comment.

Takes no arguments.

```yaml
- type: DataEditorSidebarComment
```

## DataEditorSidebarEditingStatus

Import path: `ssb_dash_framework.modules.data_editor.modules.sidebar.editing_status_view.DataEditorSidebarEditingStatus`

A sidebar module for inspecting and updating the status of the selected form by 'refnr'.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `status_options` | `list[dict[str, Any]] \| None` | `None` | What kinds of status codes can be set on a form. Defaults to: {"label": "Ubehandlet", "value": "UBEHANDLET"}, {"label": "Under arbeid", "value": "UNDER_ARBEID"}, {"label": "Ferdig", "value": "FERDIG"} |

```yaml
- type: DataEditorSidebarEditingStatus
```

## DataEditorTableSelector

Import path: `ssb_dash_framework.modules.data_editor.modules.sidebar.table_selector.DataEditorTableSelector`

Default module to select datasource table to show data for.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `form_data_tables` | `list[str]` | required | A list of tables in the database to select from. |
| `starting_table` | `str` | required | Sets the default table value to display first. |

```yaml
- type: DataEditorTableSelector
  form_data_tables: <form_data_tables>
  starting_table: <starting_table>
```

## ParquetEditor

Import path: `ssb_dash_framework.modules.parquet_editor.ParquetEditor`

Simple module with the sole purpose of editing a parquet file.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `statistics_name` | `str` | required | The name of the statistic being edited. |
| `id_vars` | `list[str]` | required | A list of columns that together form a unique identifier for a single row in your data. |
| `data_source` | `str` | required | The path to the parquet file you want to edit. |
| `data_period` | `str` | required | The period being edited. Data period controlled - eg. year, date, date-time. |
| `varselector_filtering` | `bool` | `False` | Decides if the table automatically filters based on updates in the variable selector. Defaults to False. |
| `output` | `str \| list[str] \| None` | `None` | Columns in your dataframe that should be clickable to output to the variable selector panel. |
| `output_varselector_name` | `str \| list[str] \| None` | `None` | If your dataframe column names do not match the names in the variable selector, this can be used to map columns names to variable selector names. See examples. |
| `allow_risky_column_names` | `bool` | `False` | Controls whether or not ParquetEditor allows potentially bug-inducing column names. Defaults to False. |
| `height` | `str` | `'400px'` | AgGrid defaults to 400px height. This argument allows us to specify other params for height. |

Additional keyword arguments are accepted.

```yaml
- type: ParquetEditor
  statistics_name: <statistics_name>
  id_vars: <id_vars>
  data_source: <data_source>
  data_period: <data_period>
```

## ParquetEditorChangelog

Import path: `ssb_dash_framework.modules.parquet_editor.ParquetEditorChangelog`

Simple module with the sole purpose of showing the changes made using ParquetEditor.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `id_vars` | `list[str]` | required | A list of columns that together form a unique identifier for a single row in your data. |
| `data_source` | `str` | required | The path to the parquet file you want to find the changelog for. |

```yaml
- type: ParquetEditorChangelog
  id_vars: <id_vars>
  data_source: <data_source>
```

## SkjemapdfViewer

Import path: `ssb_dash_framework.modules.skjemapdfviewer.SkjemapdfViewer`

Module for displaying PDF forms in a tab.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `form_identifier` | `str` | required | The identifier for the form. This should match the VariableSelector value. |
| `pdf_folder_path` | `str` | required | The path to the folder containing the PDF files. |

```yaml
- type: SkjemapdfViewer
  form_identifier: <form_identifier>
  pdf_folder_path: <pdf_folder_path>
```

## VariableSelectorConfig

Import path: `ssb_dash_framework.setup.variableselector.set_variables.VariableSelectorConfig`

Configuration for the variable selector.

Not selected with `type`. Created with `VariableSelectorConfig.from_yaml(...)` or from the matching section of the app config.

**Custom loader:** `from_yaml(yaml_path: str) -> 'VariableSelectorConfig'`.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `refnr` | `str \| None` | `None` | Column containing reference number or similar unique identifier for observation. |
| `ident` | `str \| None` | `None` | Primary identifier column |
| `secondary_idents` | `list[str] \| None` | `None` | Additional identifier columns |
| `time_units` | `TimeUnit \| None` | `None` | Mapping of variable name to time unit type |
| `grouping_variables` | `list[str] \| None` | `None` | Variables used for grouping operations |
