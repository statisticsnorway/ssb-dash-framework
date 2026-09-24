from dash import Input
from dash import State

from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.setup.variableselector import VariableSelectorOption
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType


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


def test_get_all_states_options_order() -> None:
    """Tests that the order inputs and states are requested in is the order they are returned."""
    VariableSelectorConfig(
        refnr="refnr",
        ident="ident",
        time_units=TimeUnit(name="iso_period", frequency=TimeUnitType.MONTH),
        grouping_variables=["altinnskjema", "variabel"],
    )
    expected_order = VariableSelector.get_state(["iso_period", "ident", "refnr", "altinnskjema", "variabel"])

    actual = VariableSelector.get_all_states()
    assert (
        actual == expected_order
    ), f"Options are sorted in the wrong order when creating states for test order {actual}. Expected order {expected_order} but returned actual order {actual}"


def test_get_input_state() -> None:
    """Tests that retrieval of specific variableselectoroptions work as intended.

    Ensures that you can pick out a value by either title or id.
    """
    variables = ["orgnr", "aar", "kvartal"]

    VariableSelectorOption("orgnr")
    VariableSelectorOption("aar")
    VariableSelectorOption("kvartal")

    for variable in variables:
        assert VariableSelector.get_input(variable, "title") == [Input(
            f"var-{variable}", "value"
        )]
        assert VariableSelector.get_input(f"var-{variable}", "id") == [Input(
            f"var-{variable}", "value"
        )]
        assert VariableSelector.get_state(variable, "title") == [State(
            f"var-{variable}", "value"
        )]
        assert VariableSelector.get_state(f"var-{variable}", "id") == [State(
            f"var-{variable}", "value"
        )]


def test_custom_title() -> None:
    """With a custom title, the varselector should still work with the .id attribute."""
    VariableSelectorOption(variable_title="Organisasjonsnummer", variable_id="ident")

    expected = [Input("var-ident", "value")]

    actual = VariableSelector.get_input("Organisasjonsnummer")
    assert isinstance(actual[0], Input)
    assert actual == expected, f"Expected: {expected}. Actual: {actual}"

    expected = [State("var-ident", "value")]

    actual = VariableSelector(
        selected_inputs=[], selected_states=["Organisasjonsnummer"]
    ).get_all_states()

    assert isinstance(actual[0], State)
    assert actual == expected, f"Expected: {expected}. Actual: {actual}"


def test_time_units_implementation() -> None:
    VariableSelectorOption(
        variable_title="År",
        variable_id="aar",
    )

    time_units = ["År"]
    variableselector = VariableSelector(selected_inputs=time_units, selected_states=[])

    assert [
        variableselector.get_option(x).id.removeprefix("var-") for x in time_units
    ] == ["aar"], "Congratulations, you might have broken a couple of modules! "
