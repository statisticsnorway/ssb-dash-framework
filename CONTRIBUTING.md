# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [GNU license] and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code]
- [Docs folder]
- [Documentation]
- [Issue Tracker]
- [Code of Conduct]

## Before-release checklist

In order to keep this library stable for production apps, follow these steps before releasing a new stable version.

- If breaking changes, make a list of them and a guide for updating.
- Ensure that all tests pass.
- Make sure all demos are up to date and working.
- Create a pre-release or stable version on the 'develop' branch and have it tested by several users to ensure compatibility.
  - Pre-release are made by adding 'a' to the version number like '0.2.0a1'
  - Testpypi is continously updated with the content from the develop 'branch' and can be used for early testing.

## Table of contents

1. [How to Set Up Your Development Environment](#how-to-set-up-your-development-environment)

2. [How to Test the Project](#how-to-test-the-project)

3. [How to Submit Changes](#how-to-submit-changes)

4. [How to Report a Bug](#how-to-report-a-bug)

5. [How to Request a Feature](#how-to-request-a-feature)


## How to set up your development environment

You need Python 3.10+ and the following tools:

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

Unit tests are located in the _tests_ directory,
and are written using the [pytest] testing framework.

## How to submit changes

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

[GNU license]: https://opensource.org/license/gpl-3-0
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
