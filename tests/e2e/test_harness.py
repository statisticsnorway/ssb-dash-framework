import re
from pathlib import Path

import pytest

from .harness import BrowserProblems
from .harness import DemoLayoutError
from .harness import discover_demos
from .harness import load_hooks
from .harness import normalize_url


def _make(root: Path, *files: str) -> None:
    for rel in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")


def test_discovers_only_app_py(tmp_path: Path) -> None:
    _make(tmp_path, "demo/a/app.py", "demo/a/webapp.py", "demo/b/app.py", "demo/x.py")
    demos = discover_demos(tmp_path / "demo", tmp_path / "hooks")
    assert [d.id for d in demos] == ["a", "b"]


@pytest.mark.parametrize(
    ("files", "message"),
    [
        (["demo/a/app.py", "demo/a/sub/app.py"], "has 2 app.py files"),
        (["demo/a/sub/app.py"], "must be at demo/<name>/app.py"),
        (["demo/app.py"], "must be at demo/<name>/app.py"),
        (["demo/a/app.py", "hooks/b.py"], "orphan hook"),
        (["demo/a/app.py", "hooks/a/nested.py"], "only <demo_id>.py hook files"),
        (["demo/readme.md"], "no demo/<name>/app.py found"),
    ],
)
def test_ambiguous_layouts_fail(tmp_path: Path, files: list[str], message: str) -> None:
    _make(tmp_path, *files)
    with pytest.raises(DemoLayoutError, match=re.escape(message)):
        discover_demos(tmp_path / "demo", tmp_path / "hooks")


def test_hook_defaults_and_values(tmp_path: Path) -> None:
    hook = tmp_path / "a.py"
    hook.write_text(
        'SKIP = "why"\nENV = {"K": "V"}\nKNOWN_ERRORS = [r"boom"]\n'
        "def customize(page, ctx):\n    pass\n"
    )
    loaded = load_hooks(hook)
    assert loaded.skip == "why"
    assert loaded.env == {"K": "V"}
    assert loaded.startup_timeout == 60
    assert [p.pattern for p in loaded.known_errors] == ["boom"]
    assert loaded.customize is not None
    assert loaded.before_load is None


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('SKIPP = "typo"\n', "unknown hook name"),
        ("def custmize(page, ctx):\n    pass\n", "unknown hook name"),
        ('TEST_TIMEOUT = "60"\n', "TEST_TIMEOUT must be int"),
        ("ENV = {'K': 1}\n", "ENV must be"),
        ("customize = 1\n", "customize must be a function"),
    ],
)
def test_invalid_hooks_fail(tmp_path: Path, source: str, message: str) -> None:
    hook = tmp_path / "a.py"
    hook.write_text(source)
    with pytest.raises(DemoLayoutError, match=message):
        load_hooks(hook)


@pytest.mark.parametrize(
    ("banner", "expected"),
    [
        ("http://0.0.0.0:8050/", "http://127.0.0.1:8050/"),
        ("http://localhost:8050/proxy/8050/", "http://127.0.0.1:8050/proxy/8050/"),
        ("http://127.0.0.1:8050/", "http://127.0.0.1:8050/"),
    ],
)
def test_normalize_url(banner: str, expected: str) -> None:
    assert normalize_url(banner) == expected


def test_known_errors_split() -> None:
    known = (re.compile("500"), re.compile("never"))
    problems = BrowserProblems(["http 500: POST /_dash-update-component", "other"])
    unexpected, matched = problems.split(known)
    assert unexpected == ["other"]
    assert {p.pattern for p in matched} == {"500"}
