#!/usr/bin/env python3

import base64
import csv
import dataclasses
import json
import pathlib
import shutil
from pprint import pprint

import httpx
import voluptuous as vol
import yaml
from slugify import slugify

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
DEVICES_DIR = ROOT_DIR / "devices"
PROCESS_DIR = ROOT_DIR / "to_process"
TEMPLATE_DIR = ROOT_DIR / "template"

INTEGRATIONS_INFO = httpx.get("https://www.home-assistant.io/integrations.json").json()

APPROVED_INTEGRATIONS = set(
    domain
    for domain, info in INTEGRATIONS_INFO.items()
    # Manual filter to remove integrations with
    # user-defined/incorrect device data
    if domain
    not in (
        "wled",  # Hardcoded to single value
        "fritz",  # user chosen manufacturer
    )
)


@dataclasses.dataclass
class UpdateRecord:
    created: int = 0
    updated: int = 0
    ignored: int = 0

    def __add__(self, other):
        return UpdateRecord(
            created=self.created + other.created,
            updated=self.updated + other.updated,
            ignored=self.ignored + other.ignored,
        )


def str_or_none(value):
    if value == "None":
        return None
    return value


def bool(value):
    return value == "True"


VIA_DEVICE_SCHEMA = vol.Schema({
        vol.Required("integration"): str,
        vol.Required("manufacturer"): str,
        vol.Required("model"): str,
        vol.Required("sw_version"): str_or_none,
        vol.Required("hw_version"): str_or_none,
})



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
        vol.Required("via_device"): via_device_schema,
        vol.Required("has_suggested_area"): bool,
        vol.Required("has_configuration_url"): bool,
        vol.Required("entry_type"): str_or_none,
        vol.Required("is_via_device"): bool,
    }
)


def process():
    total = UpdateRecord()

    for path in PROCESS_DIR.glob("*.csv"):
        print(f"{path}: ", end="")
        try:
            total += process_file(path)
        except Exception as err:
            print(f"Error; {err}")
        else:
            print("Done")

    print()
    print(f"Processed: {total}")


def process_file(path: pathlib.Path):
    total = UpdateRecord()

    with path.open("r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                row = DEVICE_SCHEMA(row)
            except vol.Invalid as err:
                print(f"Invalid row: {err}")
                pprint(row)
                raise

            total += process_row(row)

    return total


def process_row(row):
    update_record = UpdateRecord()
    model_dir = (
        DEVICES_DIR
        / row["integration"]
        / slugify(row["manufacturer"])
        / slugify(row["model"])
    )

    if row['via_device']:
        print(row['via_device'])

    if row["integration"] not in APPROVED_INTEGRATIONS:
        update_record.ignored = 1
        return update_record

    if not model_dir.exists():
        shutil.copytree(TEMPLATE_DIR, model_dir)
        update_record.created = 1

    info_path = model_dir / "info.yaml"

    info = yaml.safe_load((info_path).read_text())
    changed = False

    if not row["entry_type"]:
        row["entry_type"] = "device"

    for row_key, info_key in (
        ("manufacturer", "manufacturer_raw"),
        ("model", "model_raw"),
        ("manufacturer", "manufacturer_name"),
        ("model", "model_name"),
        ("has_suggested_area", "has_suggested_area"),
        ("has_configuration_url", "has_configuration_url"),
        ("entry_type", "entry_type"),
    ):
        if not info.get(info_key) and row[row_key]:
            info[info_key] = row[row_key]
            changed = True

    version = {}
    if row["sw_version"]:
        version["software"] = row["sw_version"]
    if row["hw_version"]:
        version["hardware"] = row["hw_version"]

    if version not in info["versions"]:
        info["versions"].append(version)
        changed = True

    if row["via_device"]:
        if not info["via_devices"]:
            info["via_devices"] = []

        if row["via_device"] not in info["via_devices"]:
            info["via_devices"].append(row["via_device"])
            changed = True

    if changed:
        info_path.write_text(yaml.dump(info))

        if not update_record.created:
            update_record.updated = 1

    return update_record


if __name__ == "__main__":
    process()
