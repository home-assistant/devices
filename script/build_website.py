#!/usr/bin/env python3

import json
import pathlib
import shutil
from collections import defaultdict
from urllib.parse import quote

import httpx
import humanmark
import mistune
import yaml

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
DEVICES_DIR = ROOT_DIR / "devices"
BUILD_DIR = ROOT_DIR / "build/website"
WEBSITE_BASE_PATH = "https://home-assistant.github.io/devices/"

INTEGRATIONS_INFO = httpx.get("https://www.home-assistant.io/integrations.json").json()


def build():
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.copytree(DEVICES_DIR, BUILD_DIR)

    device_count = 0
    index_json = []
    index_markdown = []

    for integration in sorted(
        BUILD_DIR.iterdir(), key=lambda x: INTEGRATIONS_INFO[x.name]["title"].lower()
    ):
        device_count += build_integration(integration)
        index_json.append(integration.name)
        title = INTEGRATIONS_INFO[integration.name]["title"]
        index_markdown.append(f"- [{title}]({WEBSITE_BASE_PATH}{integration.name}/)")

    (BUILD_DIR / "integrations.json").write_text(json.dumps(index_json, indent=2))
    (BUILD_DIR / "index.html").write_text(
        mistune.html(f"""
# Integrations

_Total devices: {device_count}_

[_Access this data as JSON_]({WEBSITE_BASE_PATH}integrations.json)

[_Contribute devices_](https://github.com/home-assistant/devices?tab=readme-ov-file#adding-new-devices)

{"\n".join(index_markdown)}
""")
    )


def build_integration(integration_path):
    """Process an integration."""
    index_json = defaultdict(dict)
    index_markdown = []
    device_count = 0

    for manufacturer in sorted(integration_path.iterdir()):
        for model in sorted(manufacturer.iterdir()):
            build_device(model, index_json, index_markdown)
            device_count += 1

    (integration_path / "index.json").write_text(json.dumps(index_json, indent=2))
    (integration_path / "index.html").write_text(
        mistune.html(f"""
# {INTEGRATIONS_INFO[integration_path.name]["title"]}

[_Access this data as JSON_]({WEBSITE_BASE_PATH}/{integration_path.name}/index.json)

{"\n".join(index_markdown)}
""")
    )

    return device_count


def build_device(device_path, integration_index_json, integration_index_markdown):
    """Process a device."""
    rel_path = device_path.relative_to(BUILD_DIR)
    device_url = (
        f"{WEBSITE_BASE_PATH}{'/'.join(quote(part) for part in rel_path.parts)}"
    )
    info = yaml.safe_load((device_path / "info.yaml").read_text())

    model_index = {
        "info": f"{device_url}/info.json",
    }

    device_index_extra_content = []
    readme = ""

    for doc, heading, filename in (
        ("readme", "", "readme.md"),
        ("commission", "Commissioning", "commission.md"),
        ("factory_reset", "Factory Reset", "factory_reset.md"),
    ):
        content = (device_path / filename).read_text()

        if not content:
            model_index[f"docs_{doc}"] = None
            continue

        model_index[f"docs_{doc}"] = f"{device_url}/{filename}"
        markdown = rewrite_markdown(content, f"{device_url}/")
        (device_path / filename).write_text(markdown)

        if doc == "readme":
            readme = markdown
        else:
            device_index_extra_content.append(f"""
## {heading}

{markdown}
""")

    (device_path / "index.html").write_text(
        mistune.html(f"""
# {info["manufacturer_name"]} {info["model_name"]}

[_Access this data as JSON_]({device_url}/info.json)

{readme}

```yaml
{yaml.dump(info, indent=2).strip()}
```

{'\n'.join(device_index_extra_content)}
""")
    )

    info.update(model_index)

    (device_path / "info.json").write_text(json.dumps(info, indent=2))

    integration_index_json[info["manufacturer_raw"]][info["model_raw"]] = model_index
    integration_index_markdown.append(
        f"- [{info["manufacturer_name"]} {info["model_name"]}]({device_url})"
    )


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
