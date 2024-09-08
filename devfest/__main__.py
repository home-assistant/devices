"""Processing module."""

import click

from .process import process
from .validate import validate
from .website import generate_website


@click.group()
def cli():
    """Device Festival."""
    pass


cli.add_command(process)
cli.add_command(click.command(validate))
cli.add_command(click.command(generate_website))


if __name__ == "__main__":
    cli()
