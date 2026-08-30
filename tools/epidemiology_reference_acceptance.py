#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.epidemiology import (  # noqa: E402
    harmonize_observations,
    merge_observations,
    observations_geojson,
    threshold_alert,
    weekly_series,
)

VERSION = "6.0.0"
REPORT = ROOT / "docs" / "versions" / VERSION / "EPIDEMIOLOGY_REFERENCE_ACCEPTANCE.json"
POPULATION = 2_000_000
RETRIEVED = "2026-03-31T12:00:00Z"


def obs(external_id: str, day: str, cases: int, source: str, lat: float, lon: float) -> dict:
    return {
        "external_id": external_id,
        "date": day,
        "location": "Mozambique",
        "cases": cases,
        "population": POPULATION,
        "source": source,
        "source_url": f"https://example.invalid/{source}/{external_id}",
        "retrieved_at": RETRIEVED,
        "latitude": lat,
        "longitude": lon,
    }


def main() -> None:
    first = [
        obs("who-001", "2026-03-02", 10, "who-gho", -25.97, 32.58),
        obs("hapi-001", "2026-03-05", 15, "hdx-hapi", -25.97, 32.58),
        obs("who-002", "2026-03-09", 80, "who-gho", -15.12, 39.26),
    ]
    refresh = [
        obs("who-002", "2026-03-09", 90, "who-gho", -15.12, 39.26),
        obs("rw-001", "2026-03-12", 30, "reliefweb", -15.12, 39.26),
    ]

    normalized = harmonize_observations(first)
    updated = merge_observations(normalized, refresh)
    weekly = weekly_series(updated)
    alerts = threshold_alert(weekly, incidence_threshold=5.0)
    geojson = observations_geojson(updated)

    expected_weekly = [
        ("2026-03-02", 25, 1.25),
        ("2026-03-09", 120, 6.0),
    ]
    actual_weekly = [
        (row["week_start"], row["cases"], row["incidence_per_100k"])
        for row in weekly
    ]
    if actual_weekly != expected_weekly:
        raise SystemExit(f"Série hebdomadaire incorrecte: {actual_weekly!r}")
    if len(updated) != 4:
        raise SystemExit("Le rafraîchissement n'a pas dédoublonné l'observation WHO")
    if len(alerts) != 1 or alerts[0]["week_start"] != "2026-03-09":
        raise SystemExit(f"Alerte de référence incorrecte: {alerts!r}")
    if geojson.get("type") != "FeatureCollection" or len(geojson.get("features", [])) != 4:
        raise SystemExit("GeoJSON de surveillance invalide")
    if {row["source"] for row in updated} != {"who-gho", "hdx-hapi", "reliefweb"}:
        raise SystemExit("Provenance multisource perdue")

    with tempfile.TemporaryDirectory(prefix="hdp-epi-reference-") as tmp:
        root = Path(tmp)
        observations_path = root / "observations.json"
        weekly_path = root / "weekly.json"
        geojson_path = root / "surveillance.geojson"
        observations_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        weekly_path.write_text(json.dumps(weekly, ensure_ascii=False, indent=2), encoding="utf-8")
        geojson_path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
        hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (observations_path, weekly_path, geojson_path)
        }

    report = {
        "version": VERSION,
        "status": "passed",
        "scenario": {
            "disease": "cholera",
            "location": "Mozambique",
            "period": ["2026-03-01", "2026-03-31"],
            "population_denominator": POPULATION,
            "incidence_threshold_per_100k": 5.0,
        },
        "checks": {
            "harmonized_records_initial": len(normalized),
            "records_after_refresh_and_deduplication": len(updated),
            "weekly_rows": len(weekly),
            "geojson_features": len(geojson["features"]),
            "alerts": len(alerts),
            "provenance_sources": sorted({row["source"] for row in updated}),
        },
        "weekly": weekly,
        "alerts": alerts,
        "artifact_sha256": hashes,
        "limitations": [
            "La recette utilise des observations synthétiques déterministes afin d'éviter une dépendance CI aux API publiques.",
            "Les requêtes fournisseurs et leurs paramètres sont qualifiés séparément par tools/epidemiology_acceptance.py.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "weekly": expected_weekly, "alerts": 1, "records": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
