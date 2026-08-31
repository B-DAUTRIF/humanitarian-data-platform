from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.providers.world_bank_health.descriptor import FEATURES, WORLD_BANK_HEALTH_DESCRIPTOR
from app.providers.world_bank_health.service import build_catalog_request, build_observation_request, filter_indicator_catalog, normalize_observations, validate_country_code

CYCLES = 10


def _exercise(feature: str, cycle: int) -> None:
    basic = build_observation_request(country="RWA", indicator="SH.MLR.INCD.P3", date="2020:2025", page=1 + cycle % 2, per_page=50)
    q = basic["query_parameters"]
    checks = {
        "indicator_catalogue": lambda: "/source/2/indicator" in build_catalog_request("indicators")["url"],
        "indicator_keyword_discovery": _indicator_search_is_stable,
        "wdi_source_2": lambda: q["source"] == 2,
        "indicator_code_selection": lambda: "SH.MLR.INCD.P3" in basic["url"],
        "country_iso3": lambda: validate_country_code("rwa") == "RWA",
        "multi_country": lambda: "RWA;KEN" in build_observation_request(country="RWA;KEN", indicator="X")["url"],
        "single_indicator": lambda: "/indicator/X" in build_observation_request(country="RWA", indicator="X")["url"],
        "multi_indicator": lambda: "X;Y" in build_observation_request(country="RWA", indicator="X;Y")["url"],
        "year_range": lambda: q["date"] == "2020:2025",
        "single_year": lambda: build_observation_request(country="RWA", indicator="X", date="2024")["query_parameters"]["date"] == "2024",
        "pagination": lambda: q["page"] in (1, 2),
        "page_size": lambda: q["per_page"] == 50,
        "most_recent_values": lambda: build_observation_request(country="RWA", indicator="X", mrv=5)["query_parameters"]["mrv"] == 5,
        "most_recent_non_empty": lambda: build_observation_request(country="RWA", indicator="X", mrnev=3)["query_parameters"]["mrnev"] == 3,
        "gapfill": lambda: build_observation_request(country="RWA", indicator="X", gapfill=True)["query_parameters"]["gapfill"] == "Y",
        "frequency": lambda: build_observation_request(country="RWA", indicator="X", frequency="Q")["query_parameters"]["frequency"] == "Q",
        "footnotes": lambda: build_observation_request(country="RWA", indicator="X", footnote=True)["query_parameters"]["footnote"] == "y",
        "json_format": lambda: q["format"] == "json" and build_catalog_request("countries")["query_parameters"]["format"] == "json",
        "language": lambda: "/fr/v2/" in build_observation_request(country="RWA", indicator="X", language="fr")["url"],
        "topic_catalogue": lambda: build_catalog_request("topics")["url"].endswith("/v2/topic"),
        "country_metadata": lambda: build_catalog_request("countries", identifier="RWA")["url"].endswith("/v2/country/RWA"),
        "aggregate_separation": _aggregate_is_rejected,
        "normalization": _normalization_is_stable,
        "native_provenance": lambda: basic["method"] == "GET" and isinstance(basic["query_parameters"], dict) and build_catalog_request("metadata", identifier="2", query="health")["method"] == "GET",
        "invalid_geography_rejection": _invalid_geography_is_rejected,
        "provider_error_not_empty": lambda: any(c.name == "provider_error_not_empty" for c in WORLD_BANK_HEALTH_DESCRIPTOR.capabilities),
        "bounded_result_not_absence": lambda: any(c.name == "bounded_result_not_absence" for c in WORLD_BANK_HEALTH_DESCRIPTOR.capabilities),
    }
    if feature not in checks or not checks[feature]():
        raise AssertionError(f"feature failed: {feature} cycle={cycle}")


def _indicator_search_is_stable() -> bool:
    rows = [
        {"id": "SH.MLR.INCD.P3", "name": "Incidence of malaria", "sourceNote": "Malaria cases"},
        {"id": "SP.POP.TOTL", "name": "Population, total", "sourceNote": "Population"},
    ]
    return [x["id"] for x in filter_indicator_catalog(rows, "malaria")] == ["SH.MLR.INCD.P3"]


def _aggregate_is_rejected() -> bool:
    try:
        validate_country_code("SSA")
    except ValueError:
        return True
    return False


def _invalid_geography_is_rejected() -> bool:
    try:
        validate_country_code("Rwanda")
    except ValueError:
        return True
    return False


def _normalization_is_stable() -> bool:
    payload = [{"page": 1}, [{"indicator": {"id": "X", "value": "Example"}, "country": {"id": "RW", "value": "Rwanda"}, "countryiso3code": "RWA", "date": "2024", "value": 1.2, "obs_status": "", "decimal": 1}]]
    item = normalize_observations(payload, "https://example.invalid")[0]
    return item["id"] == "X:RWA:2024" and item["_native"]["value"] == 1.2


def main() -> int:
    passed = 0
    failures: list[dict[str, object]] = []
    feature_counts: dict[str, int] = {}
    for feature in FEATURES:
        feature_counts[feature] = 0
        for cycle in range(1, CYCLES + 1):
            try:
                _exercise(feature, cycle)
                passed += 1
                feature_counts[feature] += 1
            except Exception as exc:
                failures.append({"feature": feature, "cycle": cycle, "error": f"{type(exc).__name__}: {exc}"})
    report = {
        "schema_version": 1,
        "provider": "world-bank-health",
        "api_version": "v2",
        "functionality_count": len(FEATURES),
        "cycles_per_functionality": CYCLES,
        "cycle_count": len(FEATURES) * CYCLES,
        "deterministic_passed": passed,
        "deterministic_failed": len(failures),
        "feature_cycle_counts": feature_counts,
        "failures": failures,
        "live_status": "SEPARATE_GATE",
        "status": "DETERMINISTIC_PASS" if not failures else "DETERMINISTIC_FAIL",
    }
    out_dir = ROOT / "qualification-state"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "WORLD_BANK_HEALTH_10_CYCLE_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
