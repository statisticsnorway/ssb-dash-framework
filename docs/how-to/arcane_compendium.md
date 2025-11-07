# What can you find here?

As the name implies, here you can find a non exhaustive collection of tips, tricks and workarounds to increase functionality. 

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