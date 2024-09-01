"""Device model."""

import dataclasses
import pathlib


@dataclasses.dataclass
class Device:
    path: pathlib.Path
    info: dict
    subdirs: list[str] = dataclasses.field(init=False)
    is_new: bool = dataclasses.field(default=True)

    def __post_init__(self) -> None:
        self.subdirs = [entry.name for entry in self.path.iterdir() if entry.is_dir()]
