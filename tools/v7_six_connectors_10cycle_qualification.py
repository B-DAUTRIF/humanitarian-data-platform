from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source" / "payload" / "api"))

from app.provider_semantic_adapters import translate
from app.providers.dhs.service import DHSService
from app.providers.gdacs.service import GDACSService
from app.providers.un_sdg.service import UNSDGService
from app.providers.unhcr.service import UNHCRService
from app.providers.unicef_sdmx.service import UNICEFSDMXService
from app.providers.who_gho.service import WHOGHOService
from app.semantic_router import build_semantic_intent

SETTINGS = {"timeout_seconds":10, "connect_timeout_seconds":5, "retry_count":0, "backoff_seconds":0, "max_response_bytes":1_000_000, "user_agent":"HDP-V7-six-audit", "accept_language":"en"}
PROVIDERS = {
    "dhs": (DHSService, "list_indicators"),
    "gdacs": (GDACSService, "search_events"),
    "un-sdg": (UNSDGService, "list_indicators"),
    "unhcr": (UNHCRService, "population"),
    "unicef-sdmx": (UNICEFSDMXService, "list_dataflows"),
    "who-gho": (WHOGHOService, "list_indicators"),
}


def cycle(provider: str) -> dict[str, object]:
    cls, operation = PROVIDERS[provider]
    service = cls(SETTINGS)
    checks: list[tuple[str, bool]] = []
    descriptor = service.descriptor
    checks.append(("official_evidence", bool(descriptor.evidence)))
    contracts = descriptor.metadata.get("parameter_contracts") or {}
    checks.append(("operation_contract_declared", operation in contracts))
    if operation in contracts:
        service.operation_contract(operation)
    try:
        service.validate_parameters(operation, {"project_id":"rwanda"})
        unknown_rejected = False
    except ValueError:
        unknown_rejected = True
    checks.append(("unknown_parameter_rejected", unknown_rejected))
    checks.append(("scope_debt_explicit", isinstance(descriptor.metadata.get("known_documented_not_yet_qualified"), list)))

    intent = build_semantic_intent(query="malaria", location="Rwanda", date_from="2020-01-01", date_to="2024-12-31")
    route = translate(provider, intent, result_limit=10)
    checks.append(("semantic_route_has_evidence", bool(route.get("evidence"))))
    checks.append(("bounded_completeness", route.get("completeness") == "bounded"))
    checks.append(("project_id_not_native", "project_id" not in route.get("native_parameters", {})))

    if provider == "dhs":
        checks.append(("dhs_iso3_dynamic_resolution", route.get("native_parameters", {}).get("iso3_lookup") == "RWA" and "countryIds" not in route.get("native_parameters", {})))
    elif provider == "un-sdg":
        checks.append(("sdg_m49_translation", route.get("native_parameters", {}).get("areaCode") == 646))
    elif provider == "unhcr":
        checks.append(("unhcr_role_separation", route.get("native_parameters", {}).get("country_roles") == ["origin", "asylum"]))
    elif provider == "unicef-sdmx":
        checks.append(("unicef_no_guessed_dsd", route.get("criteria", {}).get("geography") == "blocked_missing_mapping" and not route.get("executable")))
    elif provider == "who-gho":
        checks.append(("who_observation_drift_blocked", route.get("criteria", {}).get("geography") == "unsupported" and not route.get("executable")))
    elif provider == "gdacs":
        checks.append(("gdacs_no_guessed_country_filter", route.get("criteria", {}).get("geography") == "blocked_missing_mapping" and not route.get("executable")))

    failures = [name for name, passed in checks if not passed]
    return {"provider":provider, "checks":len(checks), "passed":len(checks)-len(failures), "failed":len(failures), "failures":failures, "status":"PASS" if not failures else "FAIL"}


def main() -> int:
    cycles: list[dict[str, object]] = []
    for number in range(1, 11):
        results = [cycle(provider) for provider in PROVIDERS]
        cycles.append({"cycle":number, "providers":results, "status":"PASS" if all(row["status"] == "PASS" for row in results) else "FAIL"})
    failures = [row for row in cycles if row["status"] != "PASS"]
    report = {
        "protocol":"dev_connecteurs v1.0 / HDP V7",
        "providers":list(PROVIDERS),
        "cycles_required":10,
        "cycles_executed":len(cycles),
        "cycles":cycles,
        "anti_false_zero":"bounded responses cannot prove global absence",
        "status":"PASS" if not failures else "FAIL",
    }
    out = ROOT / "qualification-state"
    out.mkdir(exist_ok=True)
    (out / "V7_SIX_CONNECTORS_10CYCLE_QUALIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"providers":report["providers"], "cycles":len(cycles), "status":report["status"]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
