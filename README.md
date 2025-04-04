# SSB Dash Framework

[![PyPI](https://img.shields.io/pypi/v/ssb-sirius-dash.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-sirius-dash.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-sirius-dash)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-sirius-dash)][license]

[![Documentation](https://github.com/statisticsnorway/ssb-sirius-dash/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/ssb-sirius-dash/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-sirius-dash&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_ssb-sirius-dash&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/ssb-sirius-dash/
[documentation]: https://statisticsnorway.github.io/ssb-sirius-dash
[tests]: https://github.com/statisticsnorway/ssb-sirius-dash/actions?workflow=Tests

[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-sirius-dash
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_ssb-sirius-dash
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/

## Vennligst se [komme i gang] for brukerveiledning

The getting started guide is in norwegian and intended for Statistics Norway internal use.

More technical and in-depth information can be found in the [Contributor Guide].

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

First add this to your pyproject.toml:

> [[tool.poetry.source]]<br>
> name = "testpypi"<br>
> url = "https://test.pypi.org/simple"<br>
> default = false<br>

Then run this command, optionally with --allow-prereleases to ensure you get the latest version.

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
[file an issue]: https://github.com/statisticsnorway/ssb-sirius-dash/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-sirius-dash/blob/main/LICENSE
[komme i gang]: https://github.com/statisticsnorway/ssb-sirius-dash/blob/main/KOMME_I_GANG.md
[contributor guide]: https://github.com/statisticsnorway/ssb-sirius-dash/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/ssb-sirius-dash/reference.html
