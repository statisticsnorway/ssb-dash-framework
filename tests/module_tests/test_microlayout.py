from contextvars import copy_context

import dash_bootstrap_components as dbc
import pytest
from dash import html
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash.exceptions import PreventUpdate

from ssb_dash_framework import MicroLayoutAIO
from ssb_dash_framework import set_variables
from ssb_dash_framework.setup.variableselector import VariableSelector


def test_import_freesearch() -> None:
    assert MicroLayoutAIO is not None, "MicroLayoutAIO is not importable"


def test_instantiation(ibis_polars_conn) -> None:
    component = MicroLayoutAIO(
        layout=[],
        getter_func=lambda x: (x,),
        update_func=lambda x: (x,),
        inputs=[],
        states=[],
    )
    assert issubclass(MicroLayoutAIO, html.Div)
    assert isinstance(component, MicroLayoutAIO)


def test_integration():
    variable_list = ["orgnr", "aar", "kvartal"]

    set_variables(variable_list)

    actual = VariableSelector(
        selected_inputs=variable_list, selected_states=[]
    ).get_all_inputs()

    component = MicroLayoutAIO(
        layout=[
            {"type": "textarea", "label": "area", "value": ""},
        ],
        getter_func=lambda x, y, z: ("textareaval",),
        update_func=lambda val, x, y, z: ("textareaval",),
        inputs=actual,
        states=[],
    )

    # checking initialization
    assert len(component.children) == 1  # pyright: ignore
    assert isinstance(
        component.children[0].children[1], dbc.Textarea
    )  # pyright: ignore

    # checking if update and getter functions distribute arguments correctly
    def run_callback():
        context_value.set(
            AttributeDict(
                **{
                    "triggered_inputs": [
                        {
                            "prop_id": f"{component._html_inputs[0].component_id_str()}.value"
                        }
                    ]
                }
            )
        )
        return component._callback_func("textareavalue", "orgnr", "aar", "kvartal")

    ctx = copy_context()
    # the update callback should not update the ui and therefore raises a PreventUpdate exception
    with pytest.raises(PreventUpdate):
        ctx.run(run_callback)

    def run_getter_callback():
        context_value.set(
            AttributeDict(
                **{
                    "triggered_inputs": [
                        {"prop_id": f"{actual[0].component_id_str()}.value"}
                    ]
                }
            )
        )
        return component._callback_func("", "orgnr", "aar", "kvartal")

    ctx = copy_context()
    output = ctx.run(run_getter_callback)
    assert output[0] == "textareaval"
