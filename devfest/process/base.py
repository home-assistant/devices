"""Base functions for processing."""

from __future__ import annotations

import shutil

import yaml
from slugify import slugify

from ..const import DATABASE_DIR
from .const import TEMPLATE_DIR
from ..models.base import Company, Device


def create_company_entry(name: str) -> Company:
    company_dir = DATABASE_DIR / slugify(name)
    if company_dir.exists():
        raise ValueError(f"A company already exists at {company_dir.name}")

    shutil.copytree((TEMPLATE_DIR / "company"), company_dir)

    info_path = company_dir / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["name"] = name
    info_path.write_text(yaml.dump(info))

    return Company(
        path=company_dir,
        info=info,
    )


def create_device_entry(
    company: Company, model_id: str, model_name: str | None
) -> Device:
    """Create a device."""
    device_dir = company.devices_dir / slugify(model_id)
    if device_dir.exists():
        raise ValueError(f"A device already exists at {device_dir.name}")

    shutil.copytree((TEMPLATE_DIR / "device"), device_dir)

    info_path = device_dir / "info.yaml"
    info = yaml.safe_load(info_path.read_text())
    info["model_id"] = model_id
    info["model_name"] = model_name
    info_path.write_text(yaml.dump(info))

    device = Device(
        path=device_dir,
        info=info,
    )
    company.devices.append(device)

    return device
