"""Demo discovery, hook loading and server lifecycle for the E2E smoke tests."""

import importlib.util
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Protocol
from typing import runtime_checkable
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

from playwright.sync_api import ConsoleMessage
from playwright.sync_api import Error
from playwright.sync_api import Page
from playwright.sync_api import Response

REPO = Path(__file__).resolve().parents[2]
HOOKS = Path(__file__).parent / "hooks"
DEMOS = REPO / "demo"

ENTRY_POINT = "app.py"
DEFAULT_STARTUP_TIMEOUT = 60
DEFAULT_TEST_TIMEOUT = 120
LOG_TAIL_LINES = 40

_BANNER = re.compile(r"Dash is running on (\S+)")
_SETTINGS = ("SKIP", "ENV", "STARTUP_TIMEOUT", "TEST_TIMEOUT", "KNOWN_ERRORS")
_FUNCTIONS = ("before_load", "customize")


class DemoLayoutError(Exception):
    """The demo/ or hooks/ layout is ambiguous or inconsistent."""


class DemoStartupError(Exception):
    """A demo server did not start and report its URL."""


@dataclass(frozen=True)
class Ctx:
    """What a hook gets to know about the running demo."""

    demo_id: str
    base_url: str
    server_log: Callable[[], str]


@runtime_checkable
class HookFn(Protocol):
    """Signature of `before_load` and `customize`."""

    def __call__(self, page: Page, ctx: Ctx) -> None:
        """Run demo-specific browser steps."""


class DemoHooks(Protocol):
    """Typed view of a hook module, with defaults for everything it leaves out."""

    @property
    def skip(self) -> str | None:
        """Reason to skip the demo, if any."""

    @property
    def env(self) -> dict[str, str]:
        """Extra environment variables for the demo process."""

    @property
    def startup_timeout(self) -> int:
        """Seconds to wait for the Dash startup banner."""

    @property
    def test_timeout(self) -> int:
        """Seconds allowed for the browser part of the test."""

    @property
    def known_errors(self) -> tuple[re.Pattern[str], ...]:
        """Browser problems that are tolerated because they are documented bugs."""

    @property
    def before_load(self) -> HookFn | None:
        """Runs before navigation."""

    @property
    def customize(self) -> HookFn | None:
        """Runs after the common load checks."""


@dataclass(frozen=True)
class LoadedHooks:
    """The `DemoHooks` implementation produced by `load_hooks`."""

    skip: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    startup_timeout: int = DEFAULT_STARTUP_TIMEOUT
    test_timeout: int = DEFAULT_TEST_TIMEOUT
    known_errors: tuple[re.Pattern[str], ...] = ()
    before_load: HookFn | None = None
    customize: HookFn | None = None


@dataclass(frozen=True)
class Demo:
    """A discovered demo app."""

    id: str
    script_path: Path
    demo_dir: Path
    hooks: DemoHooks
    hook_path: Path | None = None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _get[T](
    namespace: dict[str, object], name: str, kind: type[T], default: T, path: Path
) -> T:
    value = namespace.get(name, default)
    if not isinstance(value, kind):
        raise DemoLayoutError(
            f"{_rel(path)}: {name} must be {kind.__name__}, got {type(value).__name__}"
        )
    return value


def _get_skip(namespace: dict[str, object], path: Path) -> str | None:
    skip = namespace.get("SKIP")
    if skip is not None and not isinstance(skip, str):
        raise DemoLayoutError(f"{_rel(path)}: SKIP must be str")
    return skip


def _get_str_dict(namespace: dict[str, object], path: Path) -> dict[str, str]:
    env = _get(namespace, "ENV", dict, {}, path)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
        raise DemoLayoutError(f"{_rel(path)}: ENV must be dict[str, str]")
    return {str(k): str(v) for k, v in env.items()}


def _get_patterns(
    namespace: dict[str, object], path: Path
) -> tuple[re.Pattern[str], ...]:
    patterns = _get(namespace, "KNOWN_ERRORS", list, [], path)
    if not all(isinstance(p, str) for p in patterns):
        raise DemoLayoutError(f"{_rel(path)}: KNOWN_ERRORS must be list[str]")
    return tuple(re.compile(str(p)) for p in patterns)


def _get_fn(namespace: dict[str, object], name: str, path: Path) -> HookFn | None:
    value = namespace.get(name)
    if value is None:
        return None
    if not isinstance(value, HookFn):
        raise DemoLayoutError(f"{_rel(path)}: {name} must be a function")
    return value


def load_hooks(path: Path) -> LoadedHooks:
    """Imports a hook module by path and validates it against `DemoHooks`.

    Args:
        path: The hook file, `tests/e2e/hooks/<demo_id>.py`.

    Returns:
        The hook settings, with defaults for anything the module does not define.

    Raises:
        DemoLayoutError: If the module cannot be loaded or defines invalid settings.
    """
    spec = importlib.util.spec_from_file_location(f"e2e_hooks_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise DemoLayoutError(f"{_rel(path)}: cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    namespace: dict[str, object] = vars(module)

    unknown = sorted(
        name
        for name, value in namespace.items()
        if (name.isupper() and name not in _SETTINGS)
        or (
            callable(value)
            and getattr(value, "__module__", None) == module.__name__
            and not name.startswith("_")
            and name not in _FUNCTIONS
        )
    )
    if unknown:
        raise DemoLayoutError(
            f"{_rel(path)}: unknown hook name(s) {unknown}. "
            f"Allowed: {', '.join(_SETTINGS + _FUNCTIONS)}; prefix helpers with '_'."
        )

    return LoadedHooks(
        skip=_get_skip(namespace, path),
        env=_get_str_dict(namespace, path),
        startup_timeout=_get(
            namespace, "STARTUP_TIMEOUT", int, DEFAULT_STARTUP_TIMEOUT, path
        ),
        test_timeout=_get(namespace, "TEST_TIMEOUT", int, DEFAULT_TEST_TIMEOUT, path),
        known_errors=_get_patterns(namespace, path),
        before_load=_get_fn(namespace, "before_load", path),
        customize=_get_fn(namespace, "customize", path),
    )


def discover_demos(demo_root: Path = DEMOS, hooks_dir: Path = HOOKS) -> list[Demo]:
    """Finds every `demo/<name>/app.py` and pairs it with its optional hook.

    Args:
        demo_root: The folder holding one subfolder per demo.
        hooks_dir: The folder holding `<demo_id>.py` hook modules.

    Returns:
        The demos, sorted by id.

    Raises:
        DemoLayoutError: If any entry point or hook file would otherwise be
            ignored, ambiguous or misspelled.
    """
    problems: list[str] = []
    scripts: dict[str, list[Path]] = {}
    for script in sorted(demo_root.glob(f"**/{ENTRY_POINT}")):
        parts = script.relative_to(demo_root).parts
        if len(parts) != 2:
            problems.append(
                f"{_rel(script)}: demo entry points must be at "
                f"demo/<name>/{ENTRY_POINT}, one per demo folder."
            )
        if len(parts) >= 2:
            scripts.setdefault(parts[0], []).append(script)

    for demo_id, paths in scripts.items():
        if len(paths) > 1:
            listed = ", ".join(_rel(p) for p in paths)
            problems.append(
                f"demo id {demo_id!r} has {len(paths)} {ENTRY_POINT} files: {listed}"
            )

    hook_files: dict[str, Path] = {}
    if hooks_dir.is_dir():
        for path in sorted(hooks_dir.iterdir()):
            if path.name == "__pycache__":
                continue
            if not path.is_file() or path.suffix != ".py":
                problems.append(
                    f"{_rel(path)}: only <demo_id>.py hook files belong in {_rel(hooks_dir)}"
                )
            elif path.stem not in scripts:
                problems.append(
                    f"{_rel(path)}: orphan hook. Its name must match a demo folder "
                    f"containing {ENTRY_POINT}; discovered demos: {sorted(scripts)}"
                )
            else:
                hook_files[path.stem] = path

    if not scripts and not problems:
        problems.append(f"no demo/<name>/{ENTRY_POINT} found under {_rel(demo_root)}")
    if problems:
        raise DemoLayoutError("\n".join(problems))

    demos: list[Demo] = []
    for demo_id, (script,) in sorted(scripts.items()):
        hook_path = hook_files.get(demo_id)
        demos.append(
            Demo(
                id=demo_id,
                script_path=script,
                demo_dir=script.parent,
                hooks=load_hooks(hook_path) if hook_path else LoadedHooks(),
                hook_path=hook_path,
            )
        )
    return demos


def normalize_url(url: str) -> str:
    """Points wildcard and localhost banners at 127.0.0.1 for the browser.

    Args:
        url: The URL printed by Dash.

    Returns:
        The URL with `0.0.0.0` or `localhost` replaced by `127.0.0.1`.
    """
    parts = urlsplit(url)
    if parts.hostname not in ("0.0.0.0", "localhost"):
        return url
    netloc = f"127.0.0.1:{parts.port}" if parts.port else "127.0.0.1"
    return urlunsplit(parts._replace(netloc=netloc))


class DemoServer:
    """Runs one demo as a subprocess and captures its output."""

    def __init__(self, demo: Demo) -> None:
        """Prepares, but does not start, the server.

        Args:
            demo: The demo to run.
        """
        self.demo = demo
        self.url = ""
        self._lines: deque[str] = deque(maxlen=5000)
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None

    def start(self) -> str:
        """Starts the demo and waits for Dash to report its URL.

        Returns:
            The URL to open in the browser.

        Raises:
            DemoStartupError: If the process exits or times out before the banner.
        """
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(self.demo.demo_dir), env.get("PYTHONPATH")) if p
        )
        env.update(self.demo.hooks.env)
        self._proc = subprocess.Popen(
            [sys.executable, "-u", str(self.demo.script_path)],
            cwd=REPO,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._reader = threading.Thread(
            target=self._read, name=f"e2e-log-{self.demo.id}", daemon=True
        )
        self._reader.start()

        timeout = self.demo.hooks.startup_timeout
        deadline = time.monotonic() + timeout
        while not self._ready.wait(0.2):
            code = self._proc.poll()
            if code is not None:
                self._reader.join(timeout=5)
                raise DemoStartupError(
                    f"{_rel(self.demo.script_path)} exited with code {code} before "
                    f"printing its URL.\n{self.tail()}"
                )
            if time.monotonic() > deadline:
                raise DemoStartupError(
                    f"{_rel(self.demo.script_path)} did not print 'Dash is running on' "
                    f"within {timeout}s.\n{self.tail()}"
                )
        return self.url

    def _read(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for raw in self._proc.stdout:
            line = raw.rstrip("\n")
            with self._lock:
                self._lines.append(line)
            if not self._ready.is_set():
                match = _BANNER.search(line)
                if match:
                    self.url = normalize_url(match.group(1))
                    self._ready.set()

    def tail(self, lines: int = LOG_TAIL_LINES) -> str:
        """Returns the last lines of server output.

        Args:
            lines: How many lines to return.

        Returns:
            The newest `lines` lines of stdout/stderr.
        """
        with self._lock:
            return "\n".join(list(self._lines)[-lines:])

    def stop(self) -> None:
        """Terminates the demo, escalating to kill if it does not exit."""
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=10)
        if self._reader is not None:
            self._reader.join(timeout=5)


@dataclass
class BrowserProblems:
    """Browser errors collected while a demo is tested."""

    entries: list[str] = field(default_factory=list)

    def attach(self, page: Page) -> None:
        """Starts listening for console errors, page errors and failing callbacks.

        Args:
            page: The page to listen on.
        """
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)
        page.on("response", self._on_response)

    def _on_console(self, message: ConsoleMessage) -> None:
        if message.type == "error":
            self.entries.append(f"console: {message.text}")

    def _on_pageerror(self, error: Error) -> None:
        self.entries.append(f"pageerror: {error}")

    def _on_response(self, response: Response) -> None:
        if response.status >= 400 and "/_dash-" in response.url:
            self.entries.append(
                f"http {response.status}: {response.request.method} {response.url}"
            )

    def split(
        self, known: tuple[re.Pattern[str], ...]
    ) -> tuple[list[str], set[re.Pattern[str]]]:
        """Separates tolerated problems from unexpected ones.

        Args:
            known: The demo's KNOWN_ERRORS patterns.

        Returns:
            The unexpected problems, and the patterns that matched at least once.
        """
        unexpected: list[str] = []
        matched: set[re.Pattern[str]] = set()
        for entry in self.entries:
            hits = {p for p in known if p.search(entry)}
            matched |= hits
            if not hits:
                unexpected.append(entry)
        return unexpected, matched

    def render(self) -> str:
        """Formats the collected problems for a report.

        Returns:
            One problem per line, or a placeholder if there are none.
        """
        return "\n".join(self.entries) or "(none)"
