"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """SSB Dash Framework."""


if __name__ == "__main__":
    main(prog_name="ssb-dash-framework")  # pragma: no cover
