# AGENTS.md

Guidance for AI coding agents working in this repository.

## Start here

Before changing any code, read these two files in order:

1. [`docs/architecture.md`](docs/architecture.md): how the framework is structured and how the pieces fit together.
2. [`CONTRIBUTING.md`](CONTRIBUTING.md): dev environment setup, testing, and PR requirements.

If your task conflicts with something in either file, stop and ask rather than guessing. Do not duplicate their content here; they are the source of truth.

## What this project is

`ssb-dash-framework` is a production Python library for building Dash apps for data editing; preserve downstream compatibility. See README.md for the project overview and user installation.

- Source: `src/ssb_dash_framework/`
- Tests: `tests/`
- Demo apps: `demo/`
- Docs: `docs/` (published at https://statisticsnorway.github.io/ssb-dash-framework/)

## Commands

Requires Python 3.12+. See `CONTRIBUTING.md` for full setup.

```bash
uv sync                                     # install with dev dependencies
uvx nox                                     # run the full suite (tests, linting, etc.)
uvx nox --list-sessions                     # list available sessions
uvx nox --session=tests                     # unit tests only
uvx nox --session=pre-commit -- install     # install pre-commit hooks
```

Always run `uvx nox --sessions=tests` before declaring a task done. The suite must pass **without errors or warnings**.

## Rules

- **Test suite is described in docs/architecture.md.** Attempt to follow the recommended test suite. Add tests to `tests/` (pytest).
- **Update docs** in `docs/` when you add or change functionality, except `docs/architecture.md`.
- **Never edit `docs/architecture.md`** unless explicitly instructed. If your change makes it inaccurate, say so in your final summary instead.
- **Keep demos working.** If you change a public API or module, check that the apps in `demo/` still run and update them if needed.
- **Follow existing conventions.** Formatting and linting are enforced by pre-commit (Ruff, Black, and others in `.pre-commit-config.yaml`). Don't fight the configured tooling or edit its config to make a check pass.
- **Treat public API changes carefully.** Downstream apps depend on this library. Avoid breaking changes; if one is unavoidable, flag it clearly in your summary so it can go into the release's migration notes.
- **Don't add dependencies** without asking. If one is needed, explain why.
- **Keep changes focused.** Don't refactor unrelated code or reformat files you aren't otherwise changing.
- **Don't bump versions.** Version bumps is done by humans only.
- **preserve existing user changes**; never revert unrelated work.

## Git workflow

`main` is the only long-lived branch, used for both development and releases.

- When creating a branch or PR, target `main`.
- Do not create branches, commit, push, or open PRs unless requested.
- Contributors are asked to open an issue before starting significant work.

## When you're unsure

Ask rather than assume if:

- Ask before public API or behavior changes not explicitly requested by the user.
- `docs/architecture.md` doesn't cover the area you're touching.
- requirements are ambiguous or tests would need to be removed or weakened.
- If documentation contradicts executable configuration or observed behavior, report the discrepancy and ask before making consequential assumptions.

In your final summary, state what you changed, briefly which `nox` sessions you ran and their results, and anything you were unable to verify.
