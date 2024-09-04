"""Validate device data."""

import voluptuous as vol

from ...models.base import Device
from ..models import CompanyReport, DeviceReport

INFO_SCHEMA = vol.Schema(
    {
        vol.Required("model_id"): vol.All(str, vol.Length(min=1)),
        vol.Required("model_name"): str,
    }
)


def validate_device(report: CompanyReport, device: Device):
    """Validate a device."""
    report = DeviceReport(device)

    try:
        INFO_SCHEMA(device.info)
    except vol.Invalid as err:
        report.errors["info.yaml"].append(str(err))

    return report
