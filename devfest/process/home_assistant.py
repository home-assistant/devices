import base64
import csv
import dataclasses
import json
import pathlib
import shutil
from pprint import pprint

import voluptuous as vol
import yaml

from ..const import INTEGRATIONS_INFO, PROCESS_DIR, TEMPLATE_DIR, DataSource
from ..models.company import Company, create_company, load_companies
from ..models.device import Device
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


@dataclasses.dataclass
class HADevice:
    device: Device
    ha_info: dict = dataclasses.field(init=False)
    ha_versions: dict = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        """Post initialization."""
        self.ha_info = yaml.safe_load(self.ha_info_path.read_text())
        self.ha_versions = yaml.safe_load(self.ha_versions_path.read_text())

    @property
    def ha_info_path(self) -> pathlib.Path:
        """Return path to HA info."""
        return self.device.path / DataSource.HOME_ASSISTANT / "info.yaml"

    @property
    def ha_versions_path(self) -> pathlib.Path:
        """Return path to HA versions."""
        return self.device.path / DataSource.HOME_ASSISTANT / "versions.yaml"

    def process_row(self, row: dict) -> UpdateRecord:
        """Record the data in a row."""
        update_record = UpdateRecord()

        info_changed = False

        row.setdefault("entry_type", "device")

        for row_key, info_key in (
            ("has_suggested_area", "has_suggested_area"),
            ("has_configuration_url", "has_configuration_url"),
            ("entry_type", "entry_type"),
        ):
            if not self.ha_info.get(info_key) and row[row_key]:
                self.ha_info[info_key] = row[row_key]
                info_changed = True

        if info_changed:
            self.ha_info_path.write_text(yaml.dump(self.ha_info))

        version_changed = False
        version = {}
        if row["sw_version"]:
            version["software"] = row["sw_version"]
        if row["hw_version"]:
            version["hardware"] = row["hw_version"]

        if version and version not in self.ha_versions["versions"]:
            self.ha_versions["versions"].append(version)
            self.ha_versions_path.write_text(yaml.dump(self.ha_versions))
            version_changed = True

        # TODO via_device to be included in versions

        if not self.device.is_new and (info_changed or version_changed):
            update_record.updated = 1

        return update_record


@dataclasses.dataclass
class HACompany:
    company: Company
    ha_info: dict = dataclasses.field(init=False)
    devices_no_ha_data: list[Device] = dataclasses.field(
        init=False, default_factory=list
    )
    devices: dict[tuple[str, str, str], HADevice] = dataclasses.field(
        init=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        """Post init the HA Company."""
        self.ha_info = yaml.safe_load(self.ha_info_path.read_text())

        # Index devices
        for device in self.company.devices:
            if DataSource.HOME_ASSISTANT not in device.subdirs:
                self.devices_no_ha_data.append(device)
                continue

            ha_device = HADevice(device)

            # Index the device
            for integration in ha_device.ha_info["integrations"]:
                self.devices[
                    (
                        integration["integration"],
                        integration["manufacturer"],
                        integration["model_id"],
                    )
                ] = ha_device

    @property
    def ha_info_path(self) -> pathlib.Path:
        """Return path to HA info."""
        return self.company.path / DataSource.HOME_ASSISTANT / "info.yaml"

    def create_device(self, row: dict) -> HADevice:
        """Create a device and index it."""
        # TODO do we always just create a new one or should we ask
        # the user for an ID? Especially Matter can have duplicates.

        device = self.company.create_device(row["model_id"], row["model_name"] or None)

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
        self.devices[device_key] = ha_device
        return ha_device


class HADeviceIndex:
    def __init__(self) -> None:
        self.no_ha_data: list[Company] = []
        self.companies: dict[tuple[str, str], HACompany] = {}

    def load(self) -> None:
        """Load the index."""
        companies = load_companies()

        for company in companies:
            if DataSource.HOME_ASSISTANT not in company.subdirs:
                self.no_ha_data.append(company)
                continue

            ha_company = HACompany(company)

            # Index the company
            for integration in ha_company.ha_info["integrations"]:
                self.companies[
                    (integration["integration"], integration["manufacturer"])
                ] = ha_company

        print(
            f"Loaded {len(companies)} companies with {len(self.companies)} links to HA. {len(self.no_ha_data)} have no links."
        )

    def create_company(self, row: dict) -> HACompany:
        """Create a company and index it."""
        # TODO do we always just create a new one or should we ask
        # the user for an ID? Especially Matter can have duplicates.

        company = create_company(name=row["manufacturer"])

        # Copy Home Assistant specific data
        ha_path = company.path / DataSource.HOME_ASSISTANT
        shutil.copytree(
            (TEMPLATE_DIR / f"company-{DataSource.HOME_ASSISTANT}"), ha_path
        )
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
        self.companies[company_key] = ha_company
        return ha_company


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
            company = index.create_company(row)
            total.company_created += 1

        device_key = (row["integration"], row["manufacturer"], row["model_id"])

        if device_key not in company.devices:
            company.create_device(row)
            total.device_created += 1

    # Process via devices first
    for row in sorted(to_process, key=lambda row: not row["is_via_device"]):
        company_key = row["integration"], row["manufacturer"]
        device_key = (row["integration"], row["manufacturer"], row["model_id"])
        total += index.companies[company_key].devices[device_key].process_row(row)

    return total
