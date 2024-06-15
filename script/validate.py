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
        vol.Required("has_via_device"): bool,
        vol.Required("manufacturer_raw"): str,
        vol.Required("manufacturer_name"): str,
        vol.Required("model_raw"): str,
        vol.Required("model_name"): str,
        vol.Required("versions"): [
            {
                vol.Optional("hardware"): str,
                vol.Optional("software"): str,
            }
        ],
    }
)


@dataclasses.dataclass
class DeviceReport:
    path: pathlib.Path
    integration: str
    manufacturer: str
    model: str

    errors: dict[str, list[str]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )


def validate():
    errors = []
    for integration in DEVICES_DIR.iterdir():
        for manufacturer in integration.iterdir():
            for model in manufacturer.iterdir():
                report = validate_device(model)
                if report.errors:
                    errors.append(report)

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
    integration, manufacturer, model = rel_path.parts
    report = DeviceReport(
        path=rel_path,
        integration=integration,
        manufacturer=manufacturer,
        model=model,
    )

    info = yaml.safe_load((path / "info.yaml").read_text())

    try:
        INFO_YAML(info)
    except vol.Invalid as err:
        report.errors["info.yaml"].append(str(err))
    except FileNotFoundError:
        report.errors["info.yaml"].append("File not found")

    return report


if __name__ == "__main__":
    sys.exit(validate())
