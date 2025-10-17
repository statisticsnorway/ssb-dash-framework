from dash import Input
from dash import State

from ssb_dash_framework import set_variables
from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.setup.variableselector import VariableSelectorOption


def test_empty_variableselectoroptions_at_start() -> None:
    """Tests that the VariableSelector registry is empty at the beginning.

    Verifies that the autouse fixture has cleared the registry so we have
    no codes at the start of this test.
    """
    assert len(VariableSelector._variableselectoroptions) == 0

    # We create a VariableSelector instance.
    # It should see 0 codes because none have been created.
    variableselector = VariableSelector([], [])
    assert len(variableselector.options) == 0


def test_add_one_code() -> None:
    """Tests that adding one code populates the registry.

    After adding a single VariableSelector, this test checks:
    1) The code is actually in the registry.
    2) VariableSelector sees exactly one code.
    """
    code = VariableSelectorOption("foretak")
    assert len(VariableSelector._variableselectoroptions) == 1
    assert code in VariableSelector._variableselectoroptions

    variableselector = VariableSelector([], [])
    assert len(variableselector.options) == 1
    assert variableselector.options[0] == "foretak"


def test_no_codes_again() -> None:
    """Tests that a subsequent test sees an empty registry again.

    Verifies that after the previous test which added codes, the autouse fixture
    clears the registry so we start this test with zero codes.
    """
    assert len(VariableSelector._variableselectoroptions) == 0
    variableselector = VariableSelector([], [])
    assert len(variableselector.options) == 0


def test_get_all_inputs_states_options_order() -> None:
    """Tests that the order inputs and states are requested in is the order they are returned."""
    set_variables(["orgnr", "aar", "kvartal"])

    test_orders = {
        "order_1": ["orgnr", "aar", "kvartal"],
        "order_2": ["aar", "kvartal", "orgnr"],
        "order_3": ["kvartal", "orgnr", "aar"],
    }

    for order in test_orders:
        test_order = test_orders[order]
        expected = [
            VariableSelector(
                selected_inputs=[value], selected_states=[]
            ).get_all_inputs()[0]
            for value in test_order
        ]
        actual = VariableSelector(
            selected_inputs=test_order, selected_states=[]
        ).get_all_inputs()
        assert (
            actual == expected
        ), f"Options are sorted in the wrong order when creating inputs for test order {order}. Expected order {expected} but returned actual order {actual}"

    for order in test_orders:
        test_order = test_orders[order]
        expected = [
            VariableSelector(
                selected_inputs=[], selected_states=[value]
            ).get_all_states()[0]
            for value in test_order
        ]
        actual = VariableSelector(
            selected_inputs=[], selected_states=test_order
        ).get_all_states()
        assert (
            actual == expected
        ), f"Options are sorted in the wrong order when creating states for test order {order}. Expected order {expected} but returned actual order {actual}"


def test_get_input_state() -> None:
    """Tests that retrieval of specific variableselectoroptions work as intended.

    Ensures that you can pick out a value by either title or id.
    """
    variables = ["orgnr", "aar", "kvartal"]
    set_variables(variables)

    varselector = VariableSelector([], [])
    for variable in variables:
        assert varselector.get_input(variable, "title") == Input(
            f"var-{variable}", "value"
        )
        assert varselector.get_input(f"var-{variable}", "id") == Input(
            f"var-{variable}", "value"
        )
        assert varselector.get_state(variable, "title") == State(
            f"var-{variable}", "value"
        )
        assert varselector.get_state(f"var-{variable}", "id") == State(
            f"var-{variable}", "value"
        )
