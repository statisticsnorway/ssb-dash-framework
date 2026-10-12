# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [MIT license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Docs folder]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

## Table of contents

1. [How to Set Up Your Development Environment](#how-to-set-up-your-development-environment)

2. [How to Test the Project](#how-to-test-the-project)

3. [How to Submit Changes](#how-to-submit-changes)

4. [How to Report a Bug](#how-to-report-a-bug)

5. [How to Request a Feature](#how-to-request-a-feature)


## How to set up your development environment

You need Python 3.12+ and the following tools:

- [Poetry]
- [Nox]
- [nox-poetry]

Install [pipx]:

```console
python -m pip install --user pipx
python -m pipx ensurepath
```

Install [Poetry]:

```console
pipx install poetry
```

Install [Nox] and [nox-poetry]:

```console
pipx install nox
pipx inject nox nox-poetry
```

Install the pre-commit hooks

```console
nox --session=pre-commit -- install
```

Install the package with development requirements:

```console
poetry install
```

You can now run an interactive Python session, or your app:

```console
poetry run python
poetry run ssb-dash-framework
```

## How to test the project

Run the full test suite:

```console
nox
```

List the available Nox sessions:

```console
nox --list-sessions
```

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

```console
nox --session=tests
```

Unit tests are located in the _tests/unittests_ directory,
and are written using the [pytest] testing framework.
A bare `pytest` only collects these.

### End-to-end tests for the demos

The E2E suite in _tests/e2e_ starts every demo app and checks in a real browser
(Playwright/Chromium) that it loads without errors. It runs on Linux and is not part
of the default `nox` run:

```console
uvx nox --session=e2e
```

Every demo must live at `demo/<demo_name>/app.py` (exactly that file name, one per
folder) and call `app.run(..., debug=False)`. A new demo that follows this layout is
tested automatically; no harness changes are needed.

Demo-specific steps, skips or tolerated known bugs go in an optional hook file,
`tests/e2e/hooks/<demo_name>.py`. A hook whose name does not match a demo fails
collection. See [tests/e2e/README.md](tests/e2e/README.md) for the hook reference.

Demo ports are fixed, so do not run the E2E suite in parallel (no `pytest-xdist`,
no two simultaneous runs).

## How to submit changes

Start be reading `docs/architecture.md`.

Open a [pull request] to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
nox --session=pre-commit -- install
```

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.

Make sure all demos are up to date and working before merging a pull request.

### Breaking changes

If you are introducing breaking changes, make a summary of what they are and a guide for updating existing code in the description of your [pull request]. Make sure to label the pull request as 'Breaking'.

## Versioning

This project follows [Semantic Versioning](https://semver.org/), written in
[PEP 440](https://peps.python.org/pep-0440/) format:

- MAJOR: breaking changes to the public API
- MINOR: backwards-compatible new features
- PATCH: backwards-compatible bug fixes

Pre-releases add an `a` suffix and a counter, e.g. `0.2.0a1`, `0.2.0a2`.
TestPyPI is updated continuously from `main` for early testing.

## How to report a bug

Report bugs on the [Issue Tracker].

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

## How to request a feature

Request features on the [Issue Tracker].

[mit license]: https://opensource.org/licenses/MIT
[source code]: https://github.com/statisticsnorway/ssb-dash-framework
[Docs folder]: https://github.com/statisticsnorway/ssb-dash-framework/tree/main/docs
[documentation]: https://statisticsnorway.github.io/ssb-dash-framework
[issue tracker]: https://github.com/statisticsnorway/ssb-dash-framework/issues
[pipx]: https://pipx.pypa.io/
[poetry]: https://python-poetry.org/
[nox]: https://nox.thea.codes/
[nox-poetry]: https://nox-poetry.readthedocs.io/
[pytest]: https://pytest.readthedocs.io/
[pull request]: https://github.com/statisticsnorway/ssb-dash-framework/pulls

<!-- github-only -->

[code of conduct]: CODE_OF_CONDUCT.md
