#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.0.0"
PARTS_DIR = ROOT / "source" / "payload" / "api" / "app" / "api_inventory_parts"
DOC_DIR = ROOT / "docs" / "versions" / VERSION
REPORT_PATH = DOC_DIR / "FINALIZATION_SOURCE_CHECKS.json"

EXPECTED = {
    "entries": 1020,
    "sources": 10,
    "operations": 196,
    "supported": 228,
    "informational": 792,
}

REQUIRED_FIELDS = {
    "Source", "source_slug", "Opération", "Méthode", "Endpoint",
    "Paramètre", "Emplacement", "Type",
}


def load_inventory() -> list[dict[str, Any]]:
    files = sorted(PARTS_DIR.glob("part*.jsonl"))
    if not files:
        raise SystemExit("Inventaire V6 absent : exécuter tools/build_v6_inventory.py")
    rows: list[dict[str, Any]] = []
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"JSONL invalide {path.name}:{line_number}: {exc}") from exc
                if not isinstance(row, dict):
                    raise SystemExit(f"Ligne non objet {path.name}:{line_number}")
                missing = REQUIRED_FIELDS - set(row)
                if missing:
                    raise SystemExit(f"Champs absents {path.name}:{line_number}: {sorted(missing)}")
                rows.append(row)
    return rows


def inventory_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    operations = {
        (r.get("source_slug"), r.get("Opération"), r.get("Méthode"), r.get("Endpoint"))
        for r in rows
    }
    supported = sum(bool(r.get("supported")) for r in rows)
    return {
        "entries": len(rows),
        "sources": len({str(r.get("source_slug") or "") for r in rows}),
        "operations": len(operations),
        "supported": supported,
        "informational": len(rows) - supported,
    }


def assert_text(path: str, needles: list[str]) -> None:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"Fichier obligatoire absent: {path}")
    text = target.read_text(encoding="utf-8", errors="strict")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"Contrat V6 absent dans {path}: {missing}")


def main() -> None:
    rows = load_inventory()
    summary = inventory_summary(rows)
    if summary != EXPECTED:
        raise SystemExit(f"Inventaire V6 non canonique: {summary}; attendu: {EXPECTED}")

    # Le socle V6 embarqué reste exactement le JSONL canonique qualifié. À partir de
    # V7, le runtime peut lui superposer les nouveaux champs exécutables du registre
    # afin que l'interface ne masque jamais un paramètre nouvellement qualifié.
    # La compatibilité V6 porte donc sur le socle canonique et non sur un libellé UI.
    assert_text(
        "source/payload/api/app/api_inventory.py",
        ["part*.jsonl", "_registry_overlay_rows", "source_registry"],
    )
    assert_text("source/payload/api/app/main_v6.py", ["6.0.0", "api_inventory"])
    assert_text("source/payload/api/Dockerfile", ["app.main_v6:app"])
    assert_text("source/src/installer.c", ["APP_VERSION L\"6.0.0\"", "create_desktop_shortcut"])
    assert_text("docs/versions/6.0.0/API_INVENTORY.md", ["1020 entrées", "10 sources"])

    stale = sorted(PARTS_DIR.glob("part*.txt"))
    if stale:
        raise SystemExit(
            "Ancien inventaire compressé encore présent: " + ", ".join(p.name for p in stale)
        )

    source_counts = Counter(str(r.get("source_slug")) for r in rows)
    report = {
        "version": VERSION,
        "status": "source_checks_passed",
        "inventory": summary,
        "sources": dict(sorted(source_counts.items())),
        "runtime_entrypoint": "app.main_v6:app",
        "compatibility_model": "canonical_v6_jsonl_plus_additive_v7_registry_overlay",
        "notes": [
            "Le socle V6 canonique reste inchangé et vérifié à 1020 entrées.",
            "Le runtime V7 superpose uniquement les nouveaux champs de configuration du registre afin de préserver leur visibilité UI.",
            "Ce rapport valide la cohérence des sources et de l'inventaire embarqué.",
            "La qualification de release exige séparément les workflows CI Linux/PostgreSQL et Windows installateur verts sur le même commit.",
        ],
    }
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
