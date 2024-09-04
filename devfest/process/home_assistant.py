import base64
import csv
import json
import pathlib
import shutil
from pprint import pprint

import voluptuous as vol
import yaml

from ..const import INTEGRATIONS_INFO, PROCESS_DIR, DataSource, TEMPLATE_DIR
from ..models.home_assistant import HADeviceIndex, HADevice, HACompany
from ..models.update_record import UpdateRecord
from ..validation import bool, str_or_none

APPROVED_INTEGRATIONS = set(
    domain
    for domain, info in INTEGRATIONS_INFO.items()
    # Manual filter to remove integrations with
    # user-defined/incorrect device data
    if domain
    not in (
        "wled",  # Hardcoded to single value
    )
)


VIA_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("integration"): str,
        vol.Required("manufacturer"): str,
        vol.Required("model"): str,
        vol.Required("sw_version"): str_or_none,
        vol.Required("hw_version"): str_or_none,
    }
)


def via_device_schema(value):
    if value == "bnVsbA==":
        return None
    return VIA_DEVICE_SCHEMA(json.loads(base64.b64decode(value).decode()))


DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("integration"): str,
        vol.Required("manufacturer"): str,
        vol.Required("model"): str,
        vol.Required("sw_version"): str_or_none,
        vol.Required("hw_version"): str_or_none,
        # vol.Required("via_device"): via_device_schema,
        vol.Required("has_suggested_area"): bool,
        vol.Required("has_configuration_url"): bool,
        vol.Required("has_via_device"): bool,
        vol.Required("entry_type"): str_or_none,
        vol.Required("is_via_device"): bool,
    }
)


def process():
    """Process all files."""
    total = UpdateRecord()

    for path in PROCESS_DIR.glob("*.csv"):
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

    rows = []

    with path.open("r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                rows.append(DEVICE_SCHEMA(row))
            except vol.Invalid as err:
                print(f"Invalid row: {err}")
                pprint(row)
                raise

    index = HADeviceIndex()
    index.load()
    to_process = []

    # Ensure all companies and devices created
    for row in rows:
        # TEMP FIX FOR OLD DATA DURING DEV
        row["model_id"] = row["model"]
        row["model_name"] = row["model"]

        if row["integration"] not in APPROVED_INTEGRATIONS:
            total.devices_ignored = 1
            continue

        to_process.append(row)

        company_key = row["integration"], row["manufacturer"]
        company = index.companies.get(company_key)

        if company is None:
            company = create_company(index, row)
            total.company_created += 1

        device_key = (row["integration"], row["manufacturer"], row["model_id"])

        if device_key not in company.devices:
            create_device(company, row)
            total.device_created += 1

    # Process via devices first
    for row in sorted(to_process, key=lambda row: not row["is_via_device"]):
        company_key = row["integration"], row["manufacturer"]
        device_key = (row["integration"], row["manufacturer"], row["model_id"])
        total += update_device(index.companies[company_key].devices[device_key], row)

    return total


def create_company(index: HADeviceIndex, row: dict) -> HACompany:
    """Create a company and index it."""
    # TODO do we always just create a new one or should we ask
    # the user for an ID? Especially Matter can have duplicates.

    company = create_company(name=row["manufacturer"])

    # Copy Home Assistant specific data
    ha_path = company.path / DataSource.HOME_ASSISTANT
    shutil.copytree((TEMPLATE_DIR / f"company-{DataSource.HOME_ASSISTANT}"), ha_path)
    info_path = ha_path / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["integrations"].append(
        {
            "integration": row["integration"],
            "manufacturer": row["manufacturer"],
        }
    )
    info_path.write_text(yaml.dump(info))
    company_key = row["integration"], row["manufacturer"]
    ha_company = HACompany(company)
    index.companies[company_key] = ha_company
    return ha_company


def create_device(company: HACompany, row: dict) -> HADevice:
    """Create a device and index it."""
    # TODO do we always just create a new one or should we ask
    # the user for an ID? Especially Matter can have duplicates.

    device = company.company.create_device(row["model_id"], row["model_name"] or None)

    # Copy Home Assistant specific data
    ha_path = device.path / DataSource.HOME_ASSISTANT
    shutil.copytree((TEMPLATE_DIR / f"device-{DataSource.HOME_ASSISTANT}"), ha_path)
    info_path = ha_path / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["integrations"].append(
        {
            "integration": row["integration"],
            "manufacturer": row["manufacturer"],
            "model_id": row["model_id"],
        }
    )
    info_path.write_text(yaml.dump(info))
    device_key = row["integration"], row["manufacturer"], row["model_id"]
    ha_device = HADevice(device)
    company.devices[device_key] = ha_device
    return ha_device


def update_device(device: HADevice, row: dict) -> UpdateRecord:
    """Record the device data from a row."""
    update_record = UpdateRecord()

    info_changed = False

    row.setdefault("entry_type", "device")

    for row_key, info_key in (
        ("has_suggested_area", "has_suggested_area"),
        ("has_configuration_url", "has_configuration_url"),
        ("entry_type", "entry_type"),
    ):
        if not device.ha_info.get(info_key) and row[row_key]:
            device.ha_info[info_key] = row[row_key]
            info_changed = True

    if info_changed:
        device.ha_info_path.write_text(yaml.dump(device.ha_info))

    version_changed = False
    version = {}
    if row["sw_version"]:
        version["software"] = row["sw_version"]
    if row["hw_version"]:
        version["hardware"] = row["hw_version"]

    if version and version not in device.ha_versions["versions"]:
        device.ha_versions["versions"].append(version)
        device.ha_versions_path.write_text(yaml.dump(device.ha_versions))
        version_changed = True

    # TODO via_device to be included in versions

    if not device.device.is_new and (info_changed or version_changed):
        update_record.updated = 1

    return update_record
