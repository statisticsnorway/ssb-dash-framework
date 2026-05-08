# What can you find here?

As the name implies, here you can find a non exhaustive collection of tips, tricks and workarounds to increase functionality.

> Arcane: known or knowable only to a few people. Arcane technical details.

> Compendium: a brief summary of a larger work or of a field of knowledge. A list of a number of items, a collection or compilation.

## Variable selector fields that react to other fields / update based on logic

While it is not supposed to work like this, it is possible to connect a callback between different variable selector fields and have them react to each other.

This can be achieved by creating your own custom callbacks to the variables added in the variable selector panel. The example below reacts to the ident field and updates either the foretak or bedrift field depending on whether or not ident exists as a orgnr_foretak in the data.

```python
from ssb_dash_framework import set_variables
from ssb_dash_framework import VariableSelector

set_variables(
    [
        *perioder,
        "ident",
        "foretak",
        "bedrift",
        "statistikkvariabel",
        "altinnskjema",
        "valgt_tabell",
        "refnr",
    ]
)

hacky_varselector = VariableSelector(
    selected_inputs = ["ident"],
    selected_states = ["foretak", "bedrift"]
)

@callback(
    hacky_varselector.get_output_object("foretak"),
    hacky_varselector.get_output_object("bedrift"),
    hacky_varselector.get_input("ident"),
    prevent_initial_call = True
)
def update_from_ident(ident):
    t = conn.table("foretak")
    foretak = list(t.to_pandas()["orgnr_foretak"].unique())
    if ident in foretak:
        return ident, no_update
    else:
        return no_update, ident
```

## Connect a custom callback to a module

If you want to connect to a html component contained inside a module, you can achieve this by using a small workaround.

When you have a module initialized like this:

```python
my_table = EditingTableTab(
    label="municipality table",
    inputs=["municipality"],
    states=["year"],
    get_data_func=my_get_data_func,
)
```

You can connect your callback directly to it by looking at the module source code or inspecting the elements in your browser, finding the name of the component you wish to connect a callback to and using the instance of the module class like this:

```python
@callback(
    Output("my-id", "children"),
    Input(f"{my_table.module_number}-tabelleditering-table1", "cellClicked"),
)
def my_callback_function(*args):
    ...
```
