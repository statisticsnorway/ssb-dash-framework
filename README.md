# SSB Dash Framework

[![PyPI](https://img.shields.io/pypi/v/ssb-dash-framework.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-dash-framework.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-dash-framework)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-dash-framework)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-dash-framework/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-dash-framework/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-dash-framework&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-dash-framework&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-dash-framework/
[documentation]: https://statisticsnorway.github.io/ssb-dash-framework
[tests]: https://github.com/statisticsnorway/ssb-dash-framework/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-dash-framework
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-dash-framework
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

## Documentation

The documentation for this project can be [found here](https://statisticsnorway.github.io/ssb-dash-framework/) or in the **docs** folder.

## Features
- Dashboard for editing data, includes modules for among other things:
    - Controls for the data
    - Visualizations to find outliers
    - Seeing micro-level information about observations

## Requirements

- TODO

## Installation

You can install _SSB Sirius Dash_ via [pip] from [PyPI]:

```console
pip install ssb-dash-framework
```
or using poetry:
```console
poetry add ssb-dash-framework
```

The above will install the latest stable release.

### Installing the pre-release version

This version contains new features and improvements that are heading to the stable release eventually, but is still subject to changes.

```console
poetry add ssb-dash-framework --allow-prereleases
```

### Installing the development version

This is the currently in-development version. Be aware that this is a very unstable version and is subject to rapid breaking changes.
- Primarily intended for testing of in-development features.

First make sure this is in your pyproject.toml:

> [[tool.poetry.source]]<br>
>name = "testpypi"<br>
>url = "https://test.pypi.org/simple"<br>
>priority = "supplemental"<br>

It can be added manually or using the command below.

```console
poetry source add --priority=supplemental testpypi https://test.pypi.org/simple
```

If it is in your pyproject.toml, run this command with --allow-prereleases to ensure you get the latest version.

```console
poetry add --source testpypi ssb-dash-framework --allow-prereleases
```

## Usage

Please see the [Reference Guide] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

We are following the gitflow workflow, meaning that the main branch is the release version, while development happens on the develop branch.
An explanation of how gitflow works can be found here: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow

## License

Distributed under the terms of the [GNU license][license],
_SSB Sirius Dash_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/ssb-dash-framework/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-dash-framework/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/ssb-dash-framework/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-dash-framework/reference.html
