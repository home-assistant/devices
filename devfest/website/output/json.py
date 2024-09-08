"""Generate a JSON structure of all devices."""

import json
import pathlib
import shutil

import yaml

from ...const import DATABASE_DIR
from ...models.base import Device
from ...models.home_assistant import HADeviceIndex
from ..const import BASE_URL, WEBSITE_DIR
from ..markdown import prefix_images


def generate_json(index: HADeviceIndex):
    """Generate a JSON structure of all devices."""
    target = WEBSITE_DIR / "database"
    shutil.copytree(DATABASE_DIR, target)

    # Turn all YAML files into JSON
    for yaml_file in target.rglob("*.yaml"):
        json_file = yaml_file.with_suffix(".json")
        json_file.write_text(
            json.dumps(
                yaml.safe_load(yaml_file.read_text()),
                indent=2,
            ),
        )
        yaml_file.unlink()

    index_file = {
        "works_with_ha": f"{BASE_URL}/works_with_ha/index.json",
        "companies": {},
    }

    for company in index.companies.values():
        company_url = f"{BASE_URL}/database/{company.id}"
        index_file["companies"][company.id] = {
            "name": company.name,
            "url": f"{company_url}/info.json",
        }
        migrate_company(company, company_url, target / company.id)

    (WEBSITE_DIR / "index.json").write_text(
        json.dumps(index_file, indent=2),
    )


def migrate_company(company: Device, url_prefix: str, target: pathlib.Path) -> None:
    """Migrate a company."""
    devices = {}
    for device in company.company.devices:
        device_url = f"{url_prefix}/devices/{device.id}"
        devices[device.id] = {
            "model_name": device.model_name,
            "url": f"{device_url}/info.json",
        }
        migrate_device(
            device,
            device_url,
            target / "devices" / device.id,
        )

    # Update info.json with extra info
    index_file = target / "info.json"
    index = json.loads(index_file.read_text())
    index["devices"] = devices
    index_file.write_text(
        json.dumps(index, indent=2),
    )


def migrate_device(device: Device, url_prefix: str, target: pathlib.Path) -> None:
    """Migrate a device."""
    markdown_files = {}

    # Process all markdown files
    for md_file in target.rglob("*.md"):
        content = md_file.read_text().strip()
        if not content:
            continue
        md_file.write_text(
            prefix_images(
                content,
                f"{url_prefix}/",
            ),
        )
        markdown_files[md_file.name] = f"{url_prefix}/{md_file.name}"

    # Update info with extra info
    index_file = target / "info.json"
    index = json.loads(index_file.read_text())
    index["markdown_files"] = markdown_files
    index_file.write_text(
        json.dumps(index, indent=2),
    )
