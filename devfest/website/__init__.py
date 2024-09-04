"""Generate a website."""

import shutil
from ..models.home_assistant import HADeviceIndex
from .output.works_with_ha import generate_works_with_ha

from .const import WEBSITE_DIR


def generate_website():
    """Generate the website."""
    shutil.rmtree(WEBSITE_DIR, ignore_errors=True)
    WEBSITE_DIR.mkdir(parents=True)

    ha_index = HADeviceIndex()
    ha_index.load()

    generate_works_with_ha(ha_index)
    print("Done!")
