#!/usr/bin/env python3

# Introduce new keys to info.yaml

import pathlib

import yaml

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
DEVICES_DIR = ROOT_DIR / "devices"

NEW_KEYS = {
    "same_as": None,
}


def update():
    for integration in DEVICES_DIR.iterdir():
        for manufacturer in integration.iterdir():
            for model in manufacturer.iterdir():
                info_path = model / "info.yaml"
                info = yaml.safe_load(info_path.read_text())
                for new_key, default_value in NEW_KEYS.items():
                    info.setdefault(new_key, default_value)
                info_path.write_text(yaml.dump(info))


if __name__ == "__main__":
    update()
