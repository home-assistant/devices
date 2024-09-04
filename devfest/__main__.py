"""Processing module."""

import click

from .process.home_assistant import process
from .validate import validate


@click.group()
def cli():
    """Device Festival."""
    pass


cli.add_command(click.command(process))
cli.add_command(click.command(validate))


if __name__ == "__main__":
    cli()
