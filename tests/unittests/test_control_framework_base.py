import pytest

from ssb_dash_framework import register_control


def test_register_control_basic():
    @register_control(
        kontrollid="001_test",
        kontrolltype="H",
        beskrivelse="A hard control test",
        kontrollerte_variabler=["var1", "var2"],
    )
    def dummy():
        pass

    meta = dummy._control_meta
    assert meta["kontrollid"] == "001_test"
    assert meta["type"] == "H"
    assert meta["beskrivelse"] == "A hard control test"
    assert meta["kontrollvars"] == ["var1", "var2"]
    assert meta["sorting_var"] == ""
    assert meta["sorting_order"] == "DESC"


def test_register_control_with_sorting():
    @register_control(
        kontrollid="002_test",
        kontrolltype="S",
        beskrivelse="Soft control test",
        kontrollerte_variabler=["var3"],
        sorteringsvariabel="var3",
        sortering="ASC",
    )
    def dummy2():
        pass

    meta = dummy2._control_meta
    assert meta["sorting_var"] == "var3"
    assert meta["sorting_order"] == "ASC"


def test_register_control_additional_kwargs():
    @register_control(
        kontrollid="003_test",
        kontrolltype="I",
        beskrivelse="Informative control",
        kontrollerte_variabler=["varX"],
        extra_field="extra_value",
    )
    def dummy3():
        pass

    meta = dummy3._control_meta
    assert meta["extra_field"] == "extra_value"


def test_register_control_invalid_kontrollerte_variabler_type():
    with pytest.raises(TypeError):

        @register_control(
            kontrollid="004_test",
            kontrolltype="H",
            beskrivelse="Invalid variable type",
            kontrollerte_variabler="not_a_list",
        )
        def dummy4():
            pass


def test_register_control_invalid_kontrolltype():
    with pytest.raises(ValueError):

        @register_control(
            kontrollid="005_test",
            kontrolltype="X",
            beskrivelse="Invalid control type",
            kontrollerte_variabler=["var1"],
        )
        def dummy5():
            pass


def test_register_control_invalid_sortering():
    with pytest.raises(ValueError):

        @register_control(
            kontrollid="006_test",
            kontrolltype="H",
            beskrivelse="Invalid sorting order",
            kontrollerte_variabler=["var1"],
            sortering="INVALID",
        )
        def dummy6():
            pass
