# E2E smoke tests for the demos

Every demo in `demo/` is started as a subprocess (`python demo/<name>/app.py`, cwd = repo root)
and opened in Chromium. A single generic test checks that it loads cleanly:

1. the page renders (`#react-entry-point` is not empty),
2. nothing is stuck loading and there is no "Error loading layout",
3. no console errors, uncaught page errors or failing `/_dash-*` requests.

Run it with:

```console
uvx nox --session=e2e
```

or, with the `e2e` group installed (`uv sync --group e2e && uv run playwright install chromium`):

```console
uv run pytest tests/e2e
```

A plain `pytest` only runs the unit tests in `tests/unittests`.

On failure the report includes the tail of the server log and every browser problem seen so
far. The nox session also keeps a Playwright trace and screenshot in `test-results/e2e/`
(open a trace with `uv run playwright show-trace <trace.zip>`). CI uploads that folder when
the job fails.

Demo ports are hard-coded, so the suite must not run in parallel: `pytest-xdist` and two
simultaneous runs are not supported.

## Watching the browser

The tests run headless by default. To see what happens, open a visible browser window and
slow every Playwright action down (milliseconds per action):

```console
uv run pytest tests/e2e --headed --slowmo 500 -k hello_world
```

`-k` picks a single demo by its id. Through nox, pass the test path too, because arguments
after `--` replace the session defaults:

```console
uvx nox --session=e2e -- tests/e2e --headed --slowmo 500 -k hello_world
```

To step through a test one action at a time in the Playwright Inspector, set `PWDEBUG=1`:

```console
PWDEBUG=1 uv run pytest tests/e2e -k hello_world
```

Notes:

- Headed mode needs a display, such as a Linux desktop or WSL2 with WSLg. Remote terminals
  like JupyterLab usually have none; use the trace viewer on a failing run there instead.
- The per-demo time budget (`STARTUP_TIMEOUT + TEST_TIMEOUT`) still applies, so a long
  Inspector session or a very large `--slowmo` will be aborted. Raise `TEST_TIMEOUT` in the
  demo's hook temporarily if you need more time.

## Adding a new demo

Create `demo/my_demo/app.py` and call `app.run(..., debug=False)`. Nothing else is needed: the
demo is discovered and gets the default smoke test.

The entry point must be named exactly `app.py`, and there must be exactly one per demo folder,
directly at `demo/<name>/app.py`. Anything else fails collection rather than being ignored.

## Adding demo-specific behaviour

Create `tests/e2e/hooks/my_demo.py`, named after the demo folder. Add only what you need;
everything is optional and the default smoke test always runs.

```python
from playwright.sync_api import Page, expect

from e2e.harness import Ctx

SKIP = "Needs /buckets access"          # skip the demo entirely
ENV = {"SOME_SETTING": "value"}         # extra environment variables for the app
STARTUP_TIMEOUT = 120                   # seconds to wait for Dash to start (default 60)
TEST_TIMEOUT = 300                      # seconds for the browser part (default 120)
KNOWN_ERRORS = [
    # docs/known_bugs.md: 3. handle_field_value_change returns None
    r"500 .*_dash-update-component",
]


def before_load(page: Page, ctx: Ctx) -> None:
    """Runs before navigation: routes, cookies, tracing."""
    page.context.add_cookies([...])


def customize(page: Page, ctx: Ctx) -> None:
    """Runs after the page has loaded: demo-specific clicks and assertions."""
    page.get_by_role("button", name="Vis variabler").click()
    expect(page.locator('[id$="-message-holder"]')).to_have_value("Hello world!")
```

Rules:

- Each demo gets `STARTUP_TIMEOUT + TEST_TIMEOUT` (+30 s for teardown) in total. If that is
  exceeded, the run prints the server log, browser problems and thread stacks, stops the
  demo and aborts, so a hung demo cannot stall CI.
- A hook whose name does not match a demo folder fails collection, so typos and hooks left
  behind after a rename are caught. Unknown settings or public functions also fail; prefix
  helpers with `_`.
- `KNOWN_ERRORS` is for errors you have actually seen that are documented in
  `docs/known_bugs.md`. Put a comment naming the entry above each pattern. A pattern that never
  matches raises a `StaleKnownErrorWarning`, which means the bug is probably fixed and the
  pattern should be removed.
- Prefer role and text locators. For ids built from `module_id`, match the stable suffix with
  `[id$="-suffix"]`. Use `expect(...)` instead of sleeps.
