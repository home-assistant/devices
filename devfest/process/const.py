"""Process const."""

import pathlib

from ..const import ROOT_DIR

PROCESS_DIR = pathlib.Path(__file__).parent.resolve()

TEMPLATE_DIR = PROCESS_DIR / "templates"
PROCESS_DIR = ROOT_DIR / "to_process"
