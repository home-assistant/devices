"""Processing CLI."""
from __future__ import annotations
import click

from ..models.base import Company, load_companies
from . import home_assistant
from .base import create_company_entry, create_device_entry


@click.group()
def process():
    """Process files."""
    pass


@click.command()
@click.option("--company-name", required=True, help="The company name.")
@click.option("--model-id", required=True, help="The model ID.")
@click.option("--model-name", help="The model name.")
def base(company_name: str, model_id: str, model_name: str | None):
    """Process a file from the command line."""
    companies = load_companies()
    found: Company | None = None
    lower_company_name = company_name.lower()

    for company in companies:
        if company.name.lower() == lower_company_name:
            found = company
            break

    if not found:
        found = create_company_entry(company_name)

    for device in found.devices:
        if device.info["model_id"] == model_id:
            print(f"Device {model_id} already exists for {company_name}")
            return

    create_device_entry(found, model_id, model_name or model_id)


process.add_command(base)
process.add_command(click.command(home_assistant.process), "home-assistant")
