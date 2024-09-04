"""Validate Home Assistant data."""

import voluptuous as vol

from ...models.home_assistant import HACompany
from ..models import CompanyReport
from .home_assistant_device import validate_device

COMPANY_INFO_SCHEMA = vol.Schema(
    {
        vol.Required("integations"): [
            {
                vol.Required("integration"): str,
                vol.Required("manufacturer"): str,
            }
        ]
    }
)


def validate_home_assistant(report: CompanyReport) -> None:
    """Run Home Assistant validation."""
    company = HACompany(report.company)
    validate_company(report, company)

    for device in company.devices.values():
        device_report = validate_device(device)
        if device_report.errors:
            report.device_errors.append(device_report)


def validate_company(report: CompanyReport, company: HACompany) -> CompanyReport:
    """Validate a company."""
    report = CompanyReport(company)

    try:
        COMPANY_INFO_SCHEMA(company.ha_info)
    except vol.Invalid as err:
        report.company_errors["home-assistant/info.yaml"].append(str(err))

    return report
