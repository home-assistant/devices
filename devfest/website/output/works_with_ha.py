"""Generate Works with HA data."""

import json
from collections import defaultdict

from ...models.home_assistant import HADeviceIndex
from ..const import WEBSITE_DIR

TARGET = WEBSITE_DIR / "works_with_ha"


def generate_works_with_ha(index: HADeviceIndex) -> None:
    """Generate works with HA files."""
    TARGET.mkdir()

    # domain => devices
    works_with_ha: dict[str, list] = defaultdict(list)

    for company in index.companies.values():
        # Make it a dictionary so we de-duplicate
        devices = {
            device.id: device
            for device in company.devices.values()
            if device.ha_info["is_works_with_ha"]
        }

        if not devices:
            continue

        for device in devices.values():
            for badge_integration, badge in device.ha_info["is_works_with_ha"].items():
                for integration in device.ha_info["integrations"]:
                    if integration["integration"] != badge_integration:
                        continue
                    works_with_ha[badge_integration].append(
                        {
                            "manufacturer": integration["manufacturer"],
                            "model_id": integration["model_id"],
                            "model_name": device.device.model_name,
                            "badge": badge,
                        }
                    )

    index_file = TARGET / "index.json"
    index_file.write_text(
        json.dumps(
            {
                "integrations": sorted(works_with_ha),
            },
            indent=2,
        )
    )

    all_file = TARGET / "all.json"
    all_file.write_text(
        json.dumps(
            works_with_ha,
            indent=2,
        )
    )

    for integration, devices in works_with_ha.items():
        with open(TARGET / f"{integration}.json", "w") as fp:
            json.dump(
                {
                    "devices": devices,
                },
                fp,
                indent=2,
            )
