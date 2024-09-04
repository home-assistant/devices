"""Company model."""

from __future__ import annotations

import dataclasses
import pathlib
from functools import cached_property

import yaml

from ..const import DATABASE_DIR


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
