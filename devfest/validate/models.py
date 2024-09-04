"""Validation models."""

import dataclasses
from collections import defaultdict

from ..models.base import Company, Device


@dataclasses.dataclass
class CompanyReport:
    company: Company

    company_errors: dict[str, list[str]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )

    device_errors: list["DeviceReport"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class DeviceReport:
    device: Device

    errors: dict[str, list[str]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )
