from ssb_dash_framework.config import docgen


def test_yaml_reference_contains_known_classes() -> None:
    content = docgen.render()
    assert "## DataEditor\n" in content
    assert "## VariableSelectorConfig\n" in content
    assert "## ModuleBase\n" not in content


def test_yaml_reference_is_up_to_date() -> None:
    output = docgen.default_output_path()
    assert output.exists(), f"Missing {output}. Run `{docgen.REGENERATE_COMMAND}`."
    assert (
        output.read_text(encoding="utf-8") == docgen.render()
    ), f"{output} is outdated. Run `{docgen.REGENERATE_COMMAND}`."
