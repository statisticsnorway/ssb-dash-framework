from collections.abc import Generator
from pathlib import Path

import pytest

from ssb_dash_framework import VariableSelector
from ssb_dash_framework import config_parser_yaml

from .backends import BACKENDS


def pytest_addoption(parser: pytest.Parser) -> None:
    """Adds the --backend option for narrowing which database backends are used."""
    parser.addoption(
        "--backend",
        action="append",
        default=[],
        choices=sorted(BACKENDS),
        help="Run the suite against this backend only. Repeatable. Defaults to all.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrizes every test over the selected database backends."""
    if "db_backend" in metafunc.fixturenames:
        selected = metafunc.config.getoption("backend") or sorted(BACKENDS)
        metafunc.parametrize("db_backend", selected, indirect=True, scope="session")


@pytest.fixture(autouse=True, scope="session")
def db_backend(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Generator[str]:
    """Configures the framework's global connection for one backend.

    Session scoped, so pytest groups the run: every test against the first
    backend, then every test against the next.

    Args:
        request: The pytest fixture request.
        tmp_path_factory: The factory for creating temporary directories.

    Yields:
        str: The name of the active backend.
    """
    spec = BACKENDS[request.param]
    reason = spec.skip_reason()
    if reason:
        pytest.skip(f"{spec.name} backend unavailable: {reason}")
    with spec.setup(tmp_path_factory.mktemp(spec.name)):
        yield spec.name


@pytest.fixture
def config_yaml():
    yaml_file = Path(__file__).parent / "config" / "example_config.yaml"
    return config_parser_yaml(yaml_file)


@pytest.fixture(autouse=True)
def clear_VariableSelector_variableselectoroptions() -> Generator[None]:
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
