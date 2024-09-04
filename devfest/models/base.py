"""Company model."""

from __future__ import annotations

import dataclasses
import pathlib
import shutil
from functools import cached_property

import yaml
from slugify import slugify

from ..const import DATABASE_DIR, TEMPLATE_DIR
from .update_record import UpdateRecord


def load_companies() -> list[Company]:
    """Load companies indexed by source identifier."""
    companies = []
    for company_dir in DATABASE_DIR.iterdir():
        companies.append(
            Company(
                path=company_dir,
                info=yaml.safe_load((company_dir / "info.yaml").read_text()),
                is_new=False,
            )
        )

    return companies


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


@dataclasses.dataclass
class Company:
    path: pathlib.Path
    info: dict
    subdirs: list[str] = dataclasses.field(init=False)
    is_new: bool = dataclasses.field(default=True)

    def __post_init__(self) -> None:
        self.subdirs = [entry.name for entry in self.path.iterdir() if entry.is_dir()]

    @property
    def name(self) -> str:
        """Name of the company."""
        return self.info["name"]

    @property
    def devices_dir(self) -> pathlib.Path:
        return self.path / "devices"

    @cached_property
    def devices(self) -> list[Device]:
        """Return the devices of this company."""
        devices = []
        for device_dir in self.devices_dir.iterdir():
            devices.append(
                Device(
                    path=device_dir,
                    info=yaml.safe_load((device_dir / "info.yaml").read_text()),
                    is_new=False,
                )
            )

        return devices

    def create_device(self, model_id: str, model_name: str | None) -> Device:
        """Create a device."""
        update_record = UpdateRecord()

        device_dir = self.devices_dir / slugify(model_id)
        if device_dir.exists():
            raise ValueError(f"A device already exists at {device_dir.name}")

        shutil.copytree((TEMPLATE_DIR / "device"), device_dir)

        info_path = device_dir / "info.yaml"
        info = yaml.safe_load(info_path.read_text())
        info["model_id"] = model_id
        info["model_name"] = model_name
        info_path.write_text(yaml.dump(info))
        update_record.device_created += 1

        device = Device(
            path=device_dir,
            info=info,
        )
        self.devices.append(device)

        return device


@dataclasses.dataclass
class Device:
    path: pathlib.Path
    info: dict
    subdirs: list[str] = dataclasses.field(init=False)
    is_new: bool = dataclasses.field(default=True)

    def __post_init__(self) -> None:
        self.subdirs = [entry.name for entry in self.path.iterdir() if entry.is_dir()]

    @property
    def model_name(self) -> str:
        """Name of the device."""
        return self.info["model_name"]

    @property
    def model_id(self) -> str:
        """Name of the device."""
        return self.info["model_name"]
