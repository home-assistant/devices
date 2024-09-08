"""Validate Home Assistant device."""

import voluptuous as vol

from ...models.home_assistant import HADevice
from ...validation import has_at_least_one_key
from ..models import DeviceReport

# info.yaml
INFO_SCHEMA = vol.Schema(
    {
        vol.Required("has_configuration_url"): bool,
        vol.Required("has_suggested_area"): bool,
        vol.Required("integrations"): [
            {
                vol.Required("integration"): str,
                vol.Required("manufacturer"): str,
                vol.Required("model_id"): str,
            }
        ],
        vol.Required("is_works_with_ha"): bool,
    }
)


# versions.yaml
VERSIONS_SCHEMA = vol.Schema(
    {
        vol.Required("versions"): [
            vol.All(
                vol.Schema(
                    {
                        vol.Optional("hardware"): str,
                        vol.Optional("software"): str,
                    }
                ),
                has_at_least_one_key("hardware", "software"),
            )
        ]
    }
)


def validate_device(device: HADevice) -> DeviceReport:
    """Validate a company."""
    report = DeviceReport(device.device)
    for schema, key, file in (
        (INFO_SCHEMA, "ha_info", "info.yaml"),
        (VERSIONS_SCHEMA, "ha_versions", "versions.yaml"),
    ):
        try:
            schema(getattr(device, key))
        except vol.Invalid as err:
            report.errors[f"home-assistant/{file}"].append(str(err))

    return report
