from __future__ import annotations
import dataclasses
import pathlib

import yaml

from ..const import DataSource
from .base import Company, Device, load_companies


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
    def id(self) -> str:
        """Return ID of the device."""
        return self.device.id

    @property
    def model_name(self) -> str:
        """Return name of the device."""
        return self.device.model_name

    @property
    def ha_info_path(self) -> pathlib.Path:
        """Return path to HA info."""
        return self.device.path / DataSource.HOME_ASSISTANT / "info.yaml"

    @property
    def ha_versions_path(self) -> pathlib.Path:
        """Return path to HA versions."""
        return self.device.path / DataSource.HOME_ASSISTANT / "versions.yaml"


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
    def id(self) -> str:
        """Return ID of the company."""
        return self.company.id

    @property
    def name(self) -> str:
        """Return name of the company."""
        return self.company.name

    @property
    def ha_info_path(self) -> pathlib.Path:
        """Return path to HA info."""
        return self.company.path / DataSource.HOME_ASSISTANT / "info.yaml"


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
