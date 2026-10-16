import importlib
import inspect
import subprocess
import sys
from pathlib import Path

import ssb_dash_framework
from ssb_dash_framework.config import docgen
from ssb_dash_framework.config.models import YamlLoadable

PACKAGE_ROOT = Path(ssb_dash_framework.__file__).parent


def _run_in_fresh_process(code: str) -> str:
    # docgen reads sys.modules, so it must run where no other test has imported anything.
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=docgen.find_repo_root(),
    )
    return result.stdout


def _import_every_source_file() -> None:
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        parts = path.relative_to(PACKAGE_ROOT).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts and parts[-1] == "__main__":
            continue
        importlib.import_module(".".join((ssb_dash_framework.__name__, *parts)))


def _all_subclasses(cls: type) -> set[type]:
    found: set[type] = set()
    for subclass in cls.__subclasses__():
        found |= {subclass, *_all_subclasses(subclass)}
    return found


def test_yaml_reference_contains_known_classes() -> None:
    content = docgen.render()
    assert "## DataEditor\n" in content
    assert "## VariableSelectorConfig\n" in content
    assert "## ModuleBase\n" not in content


def test_yaml_reference_is_up_to_date() -> None:
    output = docgen.default_output_path()
    assert output.exists(), f"Missing {output}. Run `{docgen.REGENERATE_COMMAND}`."
    rendered = _run_in_fresh_process(
        "import sys\n"
        "from ssb_dash_framework.config import docgen\n"
        "sys.stdout.write(docgen.render())\n"
    )
    assert (
        output.read_text(encoding="utf-8") == rendered
    ), f"{output} is outdated. Run `{docgen.REGENERATE_COMMAND}`."


def test_all_source_directories_are_packages() -> None:
    missing = sorted(
        str(directory.relative_to(PACKAGE_ROOT))
        for directory in {path.parent for path in PACKAGE_ROOT.rglob("*.py")}
        if not (directory / "__init__.py").is_file()
    )
    assert not missing, (
        f"Directories without __init__.py are skipped by docgen: {missing}. "
        "Add an __init__.py to each."
    )


def test_collect_classes_finds_every_yaml_loadable() -> None:
    _import_every_source_file()
    expected = {
        f"{cls.__module__}.{cls.__qualname__}"
        for cls in _all_subclasses(YamlLoadable)
        if not inspect.isabstract(cls)
        and cls.__module__.startswith(f"{ssb_dash_framework.__name__}.")
    }
    found = set(
        _run_in_fresh_process(
            "from ssb_dash_framework.config import docgen\n"
            "for cls in docgen.collect_classes():\n"
            "    print(f'{cls.__module__}.{cls.__qualname__}')\n"
        ).split()
    )
    assert expected
    assert not expected - found, f"Not found by docgen: {sorted(expected - found)}"
