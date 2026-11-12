# AGENTS.md

Temporary working guidance for the HB implementation.

## Scope

- Work only on the active task in `plan.md`; do not start later tasks without direction.
- Use `docs/architecture.md`, `docs/framework_overview.md`, and `CONTRIBUTING.md` when relevant.
- Preserve user changes, keep changes focused, and maintain downstream compatibility.
- Update relevant architecture and implementation-plan documents when approved behavior changes.
- Do not add dependencies, bump versions, commit, or push unless requested.
- Ask before making consequential assumptions about scope or public behavior.

## Tests
- Do not run the full nox suite unless explicitly scheduled in `plan.md`.
- Limit tests to fit the current scope and active task in `plan.md`.
- Add unit tests under `tests/unittests/` using pytest.
- Focused test command: `uv run pytest <test-file-or-test-name> -q`.
- In PowerShell, pass each pytest file path explicitly; wildcard paths such as `tests\unittests\module_tests\test_hb_*.py` are passed literally to pytest. If pytest reports a missing file or collects no tests, correct the command and rerun before reporting a test result.
- Unit suite command: `uvx nox --session=tests`.
- Demo browser tests: `uvx nox --session=e2e` (Linux).
- List available Nox sessions with `uvx nox --list-sessions`.
- Run tests only when the active task in `plan.md` explicitly schedules them.
- List tests in `Implementation order list.md` and run them after the related task is complete.
- Do not run broad or full test suites unless they are explicitly scheduled in `plan.md`.

## When unsure

- Ask before making consequential assumptions about scope, public behavior, or test scope.

The user will restore the original `AGENTS.md` content before pulling to `main`.
