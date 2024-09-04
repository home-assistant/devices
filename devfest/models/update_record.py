"""Update Record models."""

import dataclasses


@dataclasses.dataclass
class UpdateRecord:
    company_created: int = 0
    company_updated: int = 0
    company_ignored: int = 0
    device_created: int = 0
    device_updated: int = 0
    device_ignored: int = 0

    def __add__(self, other):
        return UpdateRecord(
            company_created=self.company_created + other.company_created,
            company_updated=self.company_updated + other.company_updated,
            company_ignored=self.company_ignored + other.company_ignored,
            device_created=self.device_created + other.device_created,
            device_updated=self.device_updated + other.device_updated,
            device_ignored=self.device_ignored + other.device_ignored,
        )
