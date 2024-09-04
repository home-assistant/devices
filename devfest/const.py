"""Processing constants."""

import pathlib
from enum import StrEnum

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
DATABASE_DIR = ROOT_DIR / "database"
BUILD_DIR = ROOT_DIR / "build"


class DataSource(StrEnum):
    HOME_ASSISTANT = "home-assistant"
