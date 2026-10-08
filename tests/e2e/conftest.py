import sys
import threading
from collections.abc import Generator
from typing import Any

import pytest
from pytest_timeout import timeout_timer

from .harness import BrowserProblems
from .harness import Demo
from .harness import DemoLayoutError
from .harness import DemoServer
from .harness import discover_demos

TEARDOWN_MARGIN = 30

_PROBLEMS = pytest.StashKey[BrowserProblems]()
_TIMER = pytest.StashKey[threading.Timer]()
_servers: dict[str, DemoServer] = {}


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrizes `demo` over every discovered demo app."""
    if "demo" not in metafunc.fixturenames:
        return

    try:
        demos = discover_demos()
    except DemoLayoutError as exc:
        error = str(exc)
    else:
        error = ""
    if error:
        pytest.fail(f"E2E demo discovery failed:\n{error}", pytrace=False)

    params = []
    for demo in demos:
        budget = demo.hooks.startup_timeout + demo.hooks.test_timeout
        marks = [pytest.mark.timeout(budget + TEARDOWN_MARGIN)]
        if demo.hooks.skip:
            marks.append(pytest.mark.skip(reason=demo.hooks.skip))
        params.append(pytest.param(demo, id=demo.id, marks=marks))
    metafunc.parametrize("demo", params, indirect=True, scope="session")


@pytest.fixture(scope="session")
def demo(request: pytest.FixtureRequest) -> Demo:
    """The demo under test."""
    value: Demo = request.param
    return value


@pytest.fixture(scope="session")
def server(demo: Demo) -> Generator[DemoServer]:
    """Runs the demo for the duration of its test."""
    srv = DemoServer(demo)
    _servers[demo.id] = srv
    try:
        srv.start()
        yield srv
    finally:
        srv.stop()


@pytest.fixture
def browser_problems(request: pytest.FixtureRequest) -> BrowserProblems:
    """Collects browser errors and exposes them to failure reports."""
    problems = BrowserProblems()
    request.node.stash[_PROBLEMS] = problems
    return problems


def _demo_of(item: pytest.Item) -> Demo | None:
    callspec = getattr(item, "callspec", None)
    demo = callspec.params.get("demo") if callspec else None
    return demo if isinstance(demo, Demo) else None


def _diagnostics(item: pytest.Item) -> list[tuple[str, str]]:
    sections = []
    demo = _demo_of(item)
    if demo is not None and demo.id in _servers:
        sections.append(("server log tail", _servers[demo.id].tail()))
    problems = item.stash.get(_PROBLEMS, None)
    if problems is not None:
        sections.append(("browser problems", problems.render()))
    return sections


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Attaches the server log and browser problems to every failing E2E test."""
    report = yield
    if report.failed:
        report.sections.extend(_diagnostics(item))
    return report


def pytest_timeout_set_timer(item: pytest.Item, settings: Any) -> bool | None:
    """Enforces a demo's time budget with a thread timer instead of SIGALRM.

    A signal raised inside Playwright's sync event loop leaves it hung, so on expiry
    this prints the diagnostics, stops the server and lets pytest-timeout exit.
    """
    demo = _demo_of(item)
    if demo is None:
        return None

    def expire() -> None:
        for title, content in _diagnostics(item):
            print(f"{'~' * 20} {title} {'~' * 20}\n{content}", file=sys.stderr)
        sys.stderr.flush()
        if demo.id in _servers:
            _servers[demo.id].stop()
        timeout_timer(item, settings)

    timer = threading.Timer(settings.timeout, expire)
    timer.daemon = True
    item.stash[_TIMER] = timer
    timer.start()
    return True


def pytest_timeout_cancel_timer(item: pytest.Item) -> bool | None:
    """Cancels the timer started by `pytest_timeout_set_timer`."""
    timer = item.stash.get(_TIMER, None)
    if timer is None:
        return None
    timer.cancel()
    return True
