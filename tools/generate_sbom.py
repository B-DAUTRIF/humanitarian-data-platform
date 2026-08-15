#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def component(name: str, version: str, component_type: str, purl: str) -> dict[str, object]:
    return {
        "type": component_type,
        "name": name,
        "version": version,
        "purl": purl,
        "bom-ref": purl,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    components: list[dict[str, object]] = []
    for requirement_file in sorted((ROOT / "source" / "payload").glob("*/requirements.txt")):
        for raw in requirement_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(
                r"([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([A-Za-z0-9_.+-]+)",
                line,
            )
            if not match:
                raise ValueError(f"Dépendance Python non épinglée : {line}")
            name, version = match.groups()
            components.append(component(name, version, "library", f"pkg:pypi/{name.casefold()}@{version}"))
    compose = (ROOT / "source" / "payload" / "compose.yaml").read_text(encoding="utf-8")
    for image in sorted(set(re.findall(r"^\s*image:\s*([^\s#]+)", compose, re.MULTILINE))):
        name, _, version = image.rpartition(":")
        if not name or not version:
            raise ValueError(f"Image Docker non épinglée : {image}")
        components.append(component(name, version, "container", f"pkg:docker/{name}@{version}"))
    components.append(component("leaflet", "1.9.4", "library", "pkg:npm/leaflet@1.9.4"))
    components.sort(key=lambda item: str(item["bom-ref"]))
    serial_seed = hashlib.sha256(
        "\n".join(str(item["bom-ref"]) for item in components).encode("utf-8")
    ).hexdigest()
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial_seed[:8]}-{serial_seed[8:12]}-4{serial_seed[13:16]}-a{serial_seed[17:20]}-{serial_seed[20:32]}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "Humanitarian Data Platform",
                "version": "4.0.0",
            }
        },
        "components": components,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
