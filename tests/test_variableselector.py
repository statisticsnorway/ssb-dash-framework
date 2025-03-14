from collections.abc import Generator

import pytest
from ssb_sirius_dash.setup.variableselector import VariableSelector
from ssb_sirius_dash.setup.variableselector import VariableSelectorOption


@pytest.fixture(autouse=True)
def clear_VariableSelector_variableselectoroptions() -> Generator[None, None, None]:
    """Automatically clears the VariableSelector registry before each test.

    This ensures that each test starts with an empty codelist (so VariableSelector
    sees no codes unless the test explicitly creates some). After yielding to
    the test, it clears the registry again.

    Yields:
        None: Control is yielded to the test, after which the registry is cleared.
    """
    VariableSelector._variableselectoroptions.clear()
    yield
    VariableSelector._variableselectoroptions.clear()


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
    code = VariableSelectorOption(  # Note, "code =" can be removed without losing functionality, is only here to make sure it is added correctly.
        "foretak", "text"
    )
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
