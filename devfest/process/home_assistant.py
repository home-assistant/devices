import base64
import csv
import json
import pathlib
from pprint import pprint

from slugify import slugify
import voluptuous as vol
import yaml

from ..const import DataSource
from ..models.home_assistant import HACompany, HADevice, HADeviceIndex
from ..models.update_record import UpdateRecord
from ..validation import bool, str_or_none
from .base import create_company_entry, create_device_entry
from .const import PROCESS_DIR

IGNORED_INTEGRATIONS = {
    "wled",  # hardcoded to single value
}

VERSION_1_SCHEMA = vol.Schema(
    {
        vol.Required("version"): "home-assistant:1",
        vol.Required("no_model_id"): [str],
        vol.Required("devices"): [
            {
                vol.Required("integration"): str,
                vol.Required("manufacturer"): str,
                vol.Required("model_id"): str,
                vol.Required("model"): str,
                vol.Required("sw_version"): str_or_none,
                vol.Required("hw_version"): str_or_none,
                vol.Required("has_suggested_area"): bool,
                vol.Required("has_configuration_url"): bool,
                vol.Required("via_device"): vol.Any(None, int),
            }
        ],
    }
)


def process():
    """Process Home Assistant generated files."""
    total = UpdateRecord()

    for path in PROCESS_DIR.glob("*.json"):
        print(f"{path}: ", end="")
        try:
            total += process_file(path)
        except Exception as err:
            raise err
            print(f"Error; {err}")
        else:
            print("Done")

    print()
    print(f"Processed: {total}")


def process_file(path: pathlib.Path):
    """Process a single file."""
    total = UpdateRecord()
    data = VERSION_1_SCHEMA(json.loads(path.read_text()))

    index = HADeviceIndex()
    index.load()
    to_process = []

    # Ensure all companies and devices created
    for device_info in data["devices"]:
        pprint(device_info)
        if device_info["integration"] in IGNORED_INTEGRATIONS:
            total.devices_ignored = 1
            continue

        to_process.append(device_info)

        company_key = device_info["integration"], device_info["manufacturer"]
        company = index.companies.get(company_key)

        if company is None:
            company = create_company(index, device_info)
            total.company_created += 1

        device_key = (
            device_info["integration"],
            device_info["manufacturer"],
            device_info["model_id"],
        )

        if device_key not in company.devices:
            create_device(company, device_info)
            total.device_created += 1

    # Process via devices last
    for device_info in sorted(
        to_process, key=lambda info: info["via_device"] is not None
    ):
        company_key = device_info["integration"], device_info["manufacturer"]
        device_key = (
            device_info["integration"],
            device_info["manufacturer"],
            device_info["model_id"],
        )
        total += update_device(
            index.companies[company_key].devices[device_key], device_info
        )

    return total


def create_company(index: HADeviceIndex, device_info: dict) -> HACompany:
    """Create a company and index it."""
    # TODO do we always just create a new one or should we ask
    # the user for an ID? Especially Matter can have duplicates.

    # Company can already exist without HA link.
    company_id = slugify(device_info["manufacturer"])
    company = index.no_ha_data.pop(company_id, None)
    if company is None:
        company = create_company_entry(name=device_info["manufacturer"])

    # Set Home Assistant specific data
    ha_path = company.path / DataSource.HOME_ASSISTANT
    info_path = ha_path / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["integrations"].append(
        {
            "integration": device_info["integration"],
            "manufacturer": device_info["manufacturer"],
        }
    )
    info_path.write_text(yaml.dump(info))

    # Update index
    company_key = device_info["integration"], device_info["manufacturer"]
    ha_company = HACompany(company)
    index.companies[company_key] = ha_company
    return ha_company


def create_device(company: HACompany, device_info: dict) -> HADevice:
    """Create a device and index it."""
    # TODO do we always just create a new one or should we ask
    # the user for an ID? Especially Matter can have duplicates.

    device = create_device_entry(
        company.company, device_info["model_id"], device_info["model"] or None
    )

    # Set Home Assistant specific data
    ha_path = device.path / DataSource.HOME_ASSISTANT
    info_path = ha_path / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["integrations"].append(
        {
            "integration": device_info["integration"],
            "manufacturer": device_info["manufacturer"],
            "model_id": device_info["model_id"],
        }
    )
    info_path.write_text(yaml.dump(info))

    # Update index
    device_key = (
        device_info["integration"],
        device_info["manufacturer"],
        device_info["model_id"],
    )
    ha_device = HADevice(device)
    company.devices[device_key] = ha_device
    return ha_device


def update_device(device: HADevice, device_info: dict) -> UpdateRecord:
    """Record the device data from a device_info."""
    update_record = UpdateRecord()

    info_changed = False

    device_info.setdefault("entry_type", "device")

    for row_key, info_key in (
        ("has_suggested_area", "has_suggested_area"),
        ("has_configuration_url", "has_configuration_url"),
    ):
        if not device.ha_info.get(info_key) and device_info[row_key]:
            device.ha_info[info_key] = device_info[row_key]
            info_changed = True

    if info_changed:
        device.ha_info_path.write_text(yaml.dump(device.ha_info))

    version_changed = False
    version = {}
    if device_info["sw_version"]:
        version["software"] = device_info["sw_version"]
    if device_info["hw_version"]:
        version["hardware"] = device_info["hw_version"]

    if version and version not in device.ha_versions["versions"]:
        device.ha_versions["versions"].append(version)
        device.ha_versions_path.write_text(yaml.dump(device.ha_versions))
        version_changed = True

    # TODO via_device to be included in versions

    if not device.device.is_new and (info_changed or version_changed):
        update_record.updated = 1

    return update_record
