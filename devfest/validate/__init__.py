#!/usr/bin/env python3
from pprint import pprint

from ..models.base import load_companies
from .data.base_company import validate_company
from .data.base_device import validate_device
from .data.home_assistant_company import validate_home_assistant
from .models import CompanyReport


def validate():
    """Validate everything."""
    errors: list[CompanyReport] = []
    for company in load_companies():
        report = validate_company(company)

        if report.company_errors:
            errors.append(report)
            continue

        for device in company.devices:
            device_report = validate_device(report, device)
            if device_report.errors:
                report.device_errors.append(device_report)

        validate_home_assistant(report)

        if report.device_errors:
            errors.append(report)

    if not errors:
        print("No errors found")
        return 0

    print("Errors found:")
    print()

    for report in errors:
        print(f"{report.company.name} ({report.company.path.name}):")
        if report.company_errors:
            print("  Company:")
            pprint(dict(report.company_errors), indent=2)
            print()

        for device_report in report.device_errors:
            print(
                f"  {device_report.device.model_name} ({device_report.device.path.name}):"
            )
            pprint(dict(device_report.errors))
            print()

        print()

    return 1
