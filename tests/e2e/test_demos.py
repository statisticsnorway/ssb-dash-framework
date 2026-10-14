import warnings

from playwright.sync_api import Page
from playwright.sync_api import expect

from .harness import BrowserProblems
from .harness import Ctx
from .harness import Demo
from .harness import DemoServer


class StaleKnownErrorWarning(UserWarning):
    """A KNOWN_ERRORS pattern did not match anything; the bug may be fixed."""


def test_demo_loads_cleanly(
    page: Page, demo: Demo, server: DemoServer, browser_problems: BrowserProblems
) -> None:
    hooks = demo.hooks
    ctx = Ctx(demo_id=demo.id, base_url=server.url, server_log=server.tail)
    browser_problems.attach(page)

    if hooks.before_load:
        hooks.before_load(page, ctx)

    page.goto(ctx.base_url)
    expect(page.locator("#react-entry-point")).not_to_be_empty()
    page.wait_for_load_state("networkidle")
    expect(page.locator("._dash-loading")).to_have_count(0)
    expect(page.get_by_text("Error loading layout")).to_have_count(0)

    if hooks.customize:
        hooks.customize(page, ctx)
    page.wait_for_load_state("networkidle")

    unexpected, matched = browser_problems.split(hooks.known_errors)
    assert not unexpected, "Browser problems:\n" + "\n".join(unexpected)
    for pattern in hooks.known_errors:
        if pattern not in matched:
            warnings.warn(
                f"{demo.id}: KNOWN_ERRORS pattern {pattern.pattern!r} never matched; "
                "remove it if the bug in docs/known_bugs.md is fixed.",
                StaleKnownErrorWarning,
                stacklevel=1,
            )
