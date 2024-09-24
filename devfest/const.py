"""Processing constants."""

import pathlib

try:
    from enum import StrEnum
except ImportError:
    # StrEnum is not available in Python 3.8
    from enum import Enum
    
    class StrEnum(str, Enum):
        
        def __str__(self):
            return str(self.value)

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
DATABASE_DIR = ROOT_DIR / "database"
BUILD_DIR = ROOT_DIR / "build"


class DataSource(StrEnum):
    HOME_ASSISTANT = "home-assistant"
