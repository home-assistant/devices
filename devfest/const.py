"""Processing constants."""

import json
import pathlib
from enum import StrEnum

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
DATABASE_DIR = ROOT_DIR / "database"
PROCESS_DIR = ROOT_DIR / "to_process"
TEMPLATE_DIR = SCRIPT_DIR / "templates"

# INTEGRATIONS_INFO = httpx.get("https://www.home-assistant.io/integrations.json").json()
INTEGRATIONS_INFO = json.loads((ROOT_DIR / "integrations.json").read_text())


class DataSource(StrEnum):
    HOME_ASSISTANT = "home-assistant"
