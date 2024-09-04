"""Validate company data."""

import voluptuous as vol

from ...models.base import Company
from ..models import CompanyReport

INFO_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
    }
)


def validate_company(company: Company) -> CompanyReport:
    """Validate a company."""
    report = CompanyReport(company)

    try:
        INFO_SCHEMA(company.info)
    except vol.Invalid as err:
        report.errors["info.yaml"].append(str(err))

    return report
