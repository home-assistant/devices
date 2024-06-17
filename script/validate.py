#!/usr/bin/env python3
import dataclasses
import pathlib
import sys
from collections import defaultdict
from pprint import pprint

import voluptuous as vol
import yaml

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
DEVICES_DIR = ROOT_DIR / "devices"

INFO_YAML = vol.Schema(
    {
        vol.Required("entry_type"): str,
        vol.Required("has_configuration_url"): bool,
        vol.Required("has_suggested_area"): bool,
        vol.Optional("is_via_device"): bool,
        vol.Optional("is_works_with_ha_device"): bool,
        vol.Required("manufacturer_name"): str,
        vol.Required("manufacturer_raw"): str,
        vol.Required("model_name"): str,
        vol.Required("model_raw"): str,
        vol.Required("same_as"): vol.Any(None, [{
            vol.Required("integration"): str,
            vol.Required("manufacturer"): str,
            vol.Required("model"): str,
        }]),
        vol.Required("versions"): [
            {
                vol.Optional("hardware"): str,
                vol.Optional("software"): str,
            }
        ],
        vol.Required("via_devices"): vol.Any(None, [{
            vol.Required("integration"): str,
            vol.Required("manufacturer"): str,
            vol.Required("model"): str,
            vol.Required("hw_version"): vol.Any(str, None),
            vol.Required("sw_version"): vol.Any(str, None),
        }]),
    }
)


@dataclasses.dataclass
class DeviceReport:
    path: pathlib.Path
    integration: str
    manufacturer: str
    model: str
    info: dict

    errors: dict[str, list[str]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )


def validate():
    devices = []
    for integration in DEVICES_DIR.iterdir():
        for manufacturer in integration.iterdir():
            for model in manufacturer.iterdir():
                devices.append(validate_device(model))

    errors = []
    valid_device_keys = {
        (device.integration, device.manufacturer, device.model)
        for device in devices
    }

    for device in devices:
        for key in ('via_devices', 'same_as'):
            if not device.info[key]:
                continue

            for ref in device.info[key]:
                if (ref['integration'], ref['manufacturer'], ref['model']) not in valid_device_keys:
                    device.errors[key].append(f"Reference to unknown device: {ref}")

        if device.errors:
            errors.append(device)

    if not errors:
        print("No errors found")
        return 0

    print("Errors found:")
    print()

    for report in errors:
        print(f"{report.path}:")
        pprint(dict(report.errors))
        print()

    return 1


def validate_device(path):
    """Validate a device."""
    rel_path = path.relative_to(DEVICES_DIR)
    info = yaml.safe_load((path / "info.yaml").read_text())
    integration = rel_path.parts[0]
    manufacturer = info["manufacturer_raw"]
    model = info["model_raw"]
    report = DeviceReport(
        path=rel_path,
        integration=integration,
        manufacturer=manufacturer,
        model=model,
        info=info,
    )

    if list(info) != sorted(info):
        report.errors["info.yaml"].append("Keys are not sorted")

    try:
        INFO_YAML(info)
    except vol.Invalid as err:
        report.errors["info.yaml"].append(str(err))
    except FileNotFoundError:
        report.errors["info.yaml"].append("File not found")

    return report


if __name__ == "__main__":
    sys.exit(validate())
