#!/usr/bin/env python3

from collections import defaultdict
import pathlib
import shutil
import json

import httpx
import yaml
import humanmark

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
DEVICES_DIR = ROOT_DIR / "devices"
BUILD_DIR = ROOT_DIR / "build/website"
WEBSITE_BASE_PATH = "https://home-assistant.github.io/devices-experiment/"

INTEGRATIONS_INFO = httpx.get("https://www.home-assistant.io/integrations.json").json()


def build():
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.copytree(DEVICES_DIR, BUILD_DIR)

    integrations = []

    for integration in BUILD_DIR.iterdir():
        integrations.append(integration.name)
        build_integration(integration)

    (BUILD_DIR / "integrations.json").write_text(json.dumps(integrations, indent=2))


def build_integration(integration_path):
    """Process an integration."""
    index = defaultdict(dict)

    for manufacturer in integration_path.iterdir():
        for model in manufacturer.iterdir():
            build_device(model, index)

    (integration_path / "index.json").write_text(json.dumps(index, indent=2))


def build_device(device_path, integration_index):
    """Process a device."""
    rel_path = device_path.relative_to(BUILD_DIR)
    device_url = f"{WEBSITE_BASE_PATH}{rel_path}"
    info = yaml.safe_load((device_path / "info.yaml").read_text())

    model_index = {}

    for doc, filename in (
        ("readme", "readme.md"),
        ("commission", "commission.md"),
        ("factory_reset", "factory_reset.md"),
    ):
        content = (device_path / filename).read_text()

        if not content:
            model_index[f"docs_{doc}"] = None
            continue

        model_index[f"docs_{doc}"] = f"{device_url}/{filename}"
        (device_path / filename).write_text(rewrite_markdown(content, f"{device_url}/"))

    info.update(model_index)

    (device_path / "info.json").write_text(json.dumps(info, indent=2))

    integration_index[info["manufacturer_raw"]][info["model_raw"]] = model_index


def rewrite_markdown(text, prefix):
    doc = humanmark.loads(text)

    images = doc.find(
        # Only find image nodes
        humanmark.ast.Image,
        # A negative value means to search the entire tree.
        depth=-1,
    )

    for image in images:
        image.url = f"{prefix}{image.url}"

    return humanmark.dumps(doc)


if __name__ == "__main__":
    build()
