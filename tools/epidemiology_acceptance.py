#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"
os.environ.setdefault("DATABASE_URL", "postgresql://hdp:hdp@127.0.0.1:5432/hdp")
os.environ.setdefault("SQL_READER_URL", os.environ["DATABASE_URL"])
os.environ.setdefault("HDP_LOCAL_TOKEN", "acceptance-token")
sys.path.insert(0, str(API_ROOT))

from app.api_inventory import NATIVE_JS, inventory, source_schema, sources  # noqa: E402
from app.source_registry import CONNECTORS, connector_definition, request_preview  # noqa: E402

CHECKS: list[dict[str, object]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append({"name": name, "ok": bool(ok), "detail": detail})
    if not ok:
        raise AssertionError(f"{name}: {detail}")


def project_values(source_id: str) -> dict[str, object]:
    values = connector_definition(source_id)["project_defaults"]
    values.update({"query": "cholera", "date_from": "2025-01-01", "date_to": "2026-08-30", "location": "France", "result_limit": 25, "auto_download": False})
    if source_id == "hdx-hapi":
        values.update({"endpoint": "affected-people/idps", "location_code": "FRA", "admin_level": 0, "offset": 0})
    elif source_id == "dhs":
        values.update({"country_ids": ["FR"], "indicator_ids": [], "survey_years": [2020], "breakdown": ""})
    elif source_id == "unhcr":
        values.update({"country_of_origin": "", "country_of_asylum": "FRA", "year_from": 2025, "year_to": 2026})
    elif source_id == "gdacs":
        values.update({"event_types": ["FL"], "alert_levels": ["Green", "Orange", "Red"]})
    return values


def main() -> None:
    rows = inventory()
    summary = sources()
    check("inventory non-empty", len(rows) > 0, str(len(rows)))
    check("ten searchable sources", summary["sources"] == len(CONNECTORS) == 10, str(summary["sources"]))
    check("all sources represented", {r["source_slug"] for r in rows} == set(CONNECTORS), "inventory/registry mismatch")

    for source_id in CONNECTORS:
        definition = connector_definition(source_id)
        schema_fields = set(definition["global_settings_schema"]["properties"]) | set(definition["project_schema"]["properties"])
        source_items = [r for r in rows if r["source_slug"] == source_id]
        visible = {str(r["Paramètre"]) for r in source_items}
        missing = sorted(schema_fields - visible)
        check(f"{source_id}: configurable fields visible", not missing, ", ".join(missing))

        editable = {str(r["Paramètre"]) for r in source_items if r.get("ui_editable")}
        orphan_editable = sorted(editable - schema_fields)
        check(f"{source_id}: editable fields are canonical HDP fields", not orphan_editable, ", ".join(orphan_editable))
        check(f"{source_id}: provider parameters are never fake editable", all(not r.get("ui_editable") for r in source_items if not str(r.get("origin", "")).startswith("source_registry:")), "provider-native row marked editable")

        schema = source_schema(source_id)
        check(f"{source_id}: provenance visible", bool(schema["origins"]), str(schema["origins"]))
        check(f"{source_id}: official documentation visible", bool(schema["documentation_urls"]), "no documentation URL")

        preview = request_preview(source_id, project_values(source_id))
        parsed = urlparse(preview["url"])
        check(f"{source_id}: HTTPS request", parsed.scheme == "https", preview["url"])
        check(f"{source_id}: approved host", parsed.hostname in set(definition["allowed_hosts"]), str(parsed.hostname))
        check(f"{source_id}: reproducible Python example", "python" in preview["code_examples"], "missing Python example")
        check(f"{source_id}: reproducible R example", "r" in preview["code_examples"], "missing R example")

    hdx = request_preview("hdx", project_values("hdx"))
    check("HDX keyword reaches provider request", hdx["query_parameters"].get("q") == "cholera", str(hdx["query_parameters"]))
    check("HDX result limit reaches provider request", hdx["query_parameters"].get("rows") == 25, str(hdx["query_parameters"]))

    hapi = request_preview("hdx-hapi", project_values("hdx-hapi"))
    check("HAPI location reaches provider request", hapi["query_parameters"].get("location_code") == "FRA", str(hapi["query_parameters"]))
    check("HAPI result limit reaches provider request", hapi["query_parameters"].get("limit") == 25, str(hapi["query_parameters"]))

    gdacs = request_preview("gdacs", project_values("gdacs"))
    check("GDACS period reaches provider request", gdacs["query_parameters"].get("fromDate") == "2025-01-01" and gdacs["query_parameters"].get("toDate") == "2026-08-30", str(gdacs["query_parameters"]))
    check("GDACS event type reaches provider request", gdacs["query_parameters"].get("eventlist") == "FL", str(gdacs["query_parameters"]))

    unhcr = request_preview("unhcr", project_values("unhcr"))
    check("UNHCR period reaches provider request", unhcr["query_parameters"].get("yearFrom") == 2025 and unhcr["query_parameters"].get("yearTo") == 2026, str(unhcr["query_parameters"]))
    check("UNHCR asylum country reaches provider request", unhcr["query_parameters"].get("coa") == "FRA", str(unhcr["query_parameters"]))

    dhs = request_preview("dhs", project_values("dhs"))
    check("DHS country reaches provider request", dhs["query_parameters"].get("countryIds") == "FR", str(dhs["query_parameters"]))
    check("DHS survey year reaches provider request", dhs["query_parameters"].get("surveyYears") == "2020", str(dhs["query_parameters"]))

    who = request_preview("who-gho", project_values("who-gho"))
    check("WHO keyword reaches provider request", "cholera" in str(who["query_parameters"].get("$filter", "")).casefold(), str(who["query_parameters"]))

    for marker in ("native-api-inventory-panel", "view-source-settings", "data-api-param", "data-api-endpoint", "data-api-location", "machine_verified", "Documentation officielle", "mapping_mode", "Configurer ce paramètre"):
        check(f"native UI marker: {marker}", marker in NATIVE_JS, marker)
    check("provider-native controls are display-only", "const editable=!!p.ui_editable" in NATIVE_JS and " disabled`" in NATIVE_JS, "native inventory must not create unbound executable controls")

    main_v6 = (API_ROOT / "app" / "main_v6.py").read_text(encoding="utf-8")
    check("main UI injects native inventory script", "/api-inventory/native.js" in main_v6 and "INDEX_PATH.read_text" in main_v6, "server-side injection missing")

    passed = sum(1 for c in CHECKS if c["ok"])
    report = {
        "scenario": "epidemiology-user-acceptance",
        "version": "6.0.0",
        "inventory_entries": len(rows),
        "sources": summary["sources"],
        "operations": summary["operations"],
        "checks": CHECKS,
        "summary": {"checks": len(CHECKS), "passed": passed, "failed": len(CHECKS) - passed},
        "limitations": [
            "Deterministic acceptance verifies source-selection, parameter visibility, registry validation and provider request construction without downloading live datasets.",
            "A hosted CI runner is not a persistent interactive Windows desktop and does not replace hands-on visual usability testing.",
        ],
    }
    out = ROOT / "docs" / "versions" / "6.0.0" / "EPIDEMIOLOGY_ACCEPTANCE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
