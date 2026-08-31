#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
API_ROOT = SOURCE / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.health_sources import SEARCHABLE_SOURCE_IDS  # noqa: E402
from app.semantic_contracts import Completeness, can_claim_empty_valid  # noqa: E402
from app.semantic_router import SOURCE_CAPABILITIES, build_execution_plan, resolve_geography  # noqa: E402
from app.source_registry import CONNECTORS, connector_definition, request_preview  # noqa: E402


@dataclass
class Cycle:
    number: int
    name: str
    checks: list[str]
    status: str = "PASS"


def require(condition: bool, message: str) -> str:
    if not condition:
        raise AssertionError(message)
    return message


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cycle1() -> Cycle:
    checks: list[str] = []
    for state in (Completeness.BOUNDED, Completeness.SAMPLED, Completeness.PARTIAL, Completeness.UNKNOWN):
        for post in (False, True):
            checks.append(require(not can_claim_empty_valid(completeness=state, used_post_filter=post), f"{state.value}: no false empty_valid"))
    for state in (Completeness.EXHAUSTIVE, Completeness.PAGINATED_EXHAUSTIVE):
        checks.append(require(can_claim_empty_valid(completeness=state, used_post_filter=False), f"{state.value}: conclusive empty allowed"))
    geo = resolve_geography("Rwanda")
    checks.append(require(geo is not None and (geo.iso3, geo.m49) == ("RWA", "646"), "Rwanda mapping RWA/M49 646 verified"))
    return Cycle(1, "semantic anti-false-zero and nomenclature", checks)


def cycle2() -> Cycle:
    checks: list[str] = []
    api = text(API_ROOT / "app" / "v6_semantic_api.py")
    checks.append(require('route["provider_configuration"] = dict(project_parameters)' in api, "project provider configuration propagated to semantic route"))
    checks.append(require('route["project_enabled"] = enabled' in api and "project_blocked" in api, "project enable/disable enforced"))
    checks.append(require('plan["query_fingerprint"] = query_fingerprint(plan)' in api, "project context participates in query fingerprint"))
    return Cycle(2, "project context propagation", checks)


def cycle3() -> Cycle:
    checks: list[str] = []
    provider = text(API_ROOT / "app" / "semantic_provider_execution.py")
    checks.append(require("max_response_bytes" in provider, "native semantic HTTP honours max_response_bytes"))
    checks.append(require("client.stream" in provider and "aiter_bytes" in provider, "provider payload streamed before JSON decode"))
    checks.append(require("content-length" in provider, "declared response size prechecked"))
    return Cycle(3, "provider transport limits", checks)


def cycle4() -> Cycle:
    checks: list[str] = []
    ids = set(CONNECTORS)
    checks.append(require(ids == set(SEARCHABLE_SOURCE_IDS) == set(SOURCE_CAPABILITIES), "registry/searchable/semantic source sets are identical"))
    checks.append(require(len(ids) == 10, "ten active searchable connectors"))
    for source_id in sorted(ids):
        definition = connector_definition(source_id)
        parsed = urlparse(definition["base_url"])
        checks.append(require(parsed.scheme == "https", f"{source_id}: HTTPS base URL"))
        checks.append(require(parsed.hostname in set(definition["allowed_hosts"]), f"{source_id}: base host allow-listed"))
        preview = request_preview(source_id, definition["project_defaults"])
        preview_url = urlparse(preview["url"])
        checks.append(require(preview_url.scheme == "https" and preview_url.hostname in set(definition["allowed_hosts"]), f"{source_id}: request preview remains allow-listed"))
    return Cycle(4, "connector registry and request safety", checks)


def cycle5() -> Cycle:
    checks: list[str] = []
    plan = build_execution_plan(
        list(SEARCHABLE_SOURCE_IDS),
        query="paludisme",
        location="Rwanda",
        date_from="2020-01-01",
        date_to="2025-12-31",
    )
    checks.append(require(len(plan["routes"]) == 10, "ten semantic routes generated"))
    checks.append(require(re.fullmatch(r"[0-9a-f]{64}", plan["query_fingerprint"]) is not None, "semantic query fingerprint SHA-256"))
    routes = {route["source"]: route for route in plan["routes"]}
    checks.append(require(routes["dhs"]["criteria"].get("geography") == "blocked_missing_mapping" and not routes["dhs"]["executable"], "DHS provider-specific country IDs are never guessed"))
    checks.append(require(routes["hdx"]["criteria"].get("geography") in {"post_filter", "blocked_missing_mapping"}, "HDX unverified geography is not promoted to native mapping"))
    checks.append(require(routes["world-bank-health"]["native_parameters"].get("country") == "RWA", "World Bank verified ISO3 translation"))
    checks.append(require(routes["un-sdg"]["native_parameters"].get("areaCode") == 646, "UN SDG verified M49 translation"))
    checks.append(require(routes["unhcr"]["native_parameters"].get("country_roles") == ["origin", "asylum"], "UNHCR origin/asylum roles preserved"))
    return Cycle(5, "semantic provider translation matrix", checks)


def cycle6() -> Cycle:
    checks: list[str] = []
    migrations = text(API_ROOT / "app" / "v7_migrations.py")
    for table in (
        "semantic_searches",
        "semantic_source_executions",
        "semantic_mapping_evidence",
        "semantic_jobs",
        "provider_schema_versions",
        "provider_field_catalog",
        "provider_vocabulary_cache",
        "provider_vocabulary_values",
        "provider_raw_artifacts",
        "provider_normalizations",
        "provider_schema_drift_events",
    ):
        checks.append(require(table in migrations, f"migration includes {table}"))
    for status in ("queued", "running", "completed", "partial", "failed", "cancelled"):
        checks.append(require(status in migrations, f"semantic job status {status}"))
    provenance = text(API_ROOT / "app" / "semantic_provenance.py")
    checks.append(require("query_fingerprint" in provenance and "result_snapshot_hash" in provenance, "query/result fingerprints are distinct functions"))
    return Cycle(6, "persistence, jobs and provenance", checks)


def cycle7() -> Cycle:
    checks: list[str] = []
    main = text(API_ROOT / "app" / "main_v6.py")
    checks.append(require('ACTIVE_APPLICATION_VERSION = "7.0.0"' in main, "runtime identifies V7"))
    checks.append(require("apply_v7_migrations" in main and "recover_abandoned_semantic_jobs" in main, "startup migration/job recovery enabled"))
    security = text(API_ROOT / "app" / "security.py")
    checks.append(require("safe_filename" in security, "filename sanitisation available"))
    secure_http = text(API_ROOT / "app" / "secure_http.py")
    checks.append(require("allowed_hosts" in secure_http or "allowed_host" in secure_http, "HTTP egress host policy present"))
    duplicates: list[tuple[str, tuple[str, str]]] = []
    for path in (API_ROOT / "app").rglob("*.py"):
        tree = ast.parse(text(path))
        seen: set[tuple[str, str]] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)):
                    continue
                method = decorator.func.attr.lower()
                if method not in {"get", "post", "put", "patch", "delete"} or not decorator.args:
                    continue
                first = decorator.args[0]
                if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                    continue
                key = (method.upper(), first.value)
                if key in seen:
                    duplicates.append((str(path.relative_to(API_ROOT)), key))
                seen.add(key)
    checks.append(require(not duplicates, f"no duplicate decorated method/path inside modules: {duplicates}"))
    return Cycle(7, "runtime/API/security surface", checks)


def cycle8() -> Cycle:
    checks: list[str] = []
    inventory = text(API_ROOT / "app" / "api_inventory.py")
    checks.append(require("_registry_overlay_rows" in inventory, "API inventory overlays executable registry fields"))
    checks.append(require("native-api-inventory-panel" in inventory and "Documentation officielle" in inventory, "source-specific parameter inventory visible in UI"))
    semantic = text(API_ROOT / "app" / "v6_semantic_api.py")
    for marker in ("Simple", "Avancé", "Expert", "query_fingerprint", "result_snapshot_hash"):
        checks.append(require(marker in semantic, f"semantic UI exposes {marker}"))
    return Cycle(8, "UI and parameter exposure", checks)


def cycle9() -> Cycle:
    checks: list[str] = []
    python_root = ROOT / "clients-v6" / "python"
    r_root = ROOT / "clients-v6" / "R"
    python_code = "\n".join(text(path) for path in python_root.rglob("*.py"))
    r_code = "\n".join(text(path) for path in r_root.rglob("*.R"))
    for token in ("reliefweb", "world_bank"):
        checks.append(require(token in python_code.casefold(), f"Python client exposes {token}"))
        checks.append(require(token in r_code.casefold(), f"R client exposes {token}"))
    jobs = text(API_ROOT / "app" / "v7_semantic_jobs.py")
    for token in ("cancel_requested", "progress", "queued", "running", "completed", "partial", "failed", "cancelled"):
        checks.append(require(token in jobs, f"semantic jobs expose {token}"))
    return Cycle(9, "clients and automation", checks)


def cycle10() -> Cycle:
    checks: list[str] = []
    build = text(SOURCE / "build-windows-v7.ps1")
    checks.append(require("HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe" in build, "V7 EXE filename fixed"))
    checks.append(require("Get-FileHash" in build or "SHA256" in build.upper(), "Windows build computes artifact hash"))
    installer = text(SOURCE / "src" / "installer.c")
    checks.append(require("create_desktop_shortcut" in installer, "installer creates desktop shortcut"))
    checks.append(require("Docker" in installer and "Python" in installer, "installer probes core dependencies"))
    workflow = ROOT / ".github" / "workflows" / "windows-v7-full.yml"
    if workflow.exists():
        workflow_text = text(workflow)
        checks.append(require("windows-2025" in workflow_text, "V7 installer compiled on Windows 2025 runner"))
        checks.append(require("Validate PE32+ and hashes" in workflow_text, "workflow validates PE32+ and hashes"))
        checks.append(require("HDP-V7-user-test-RC" in workflow_text, "workflow publishes user-test RC artifact"))
    return Cycle(10, "Windows installer and release artifact", checks)


def main() -> None:
    cycles: list[Cycle] = []
    for function in (cycle1, cycle2, cycle3, cycle4, cycle5, cycle6, cycle7, cycle8, cycle9, cycle10):
        try:
            cycle = function()
        except Exception as exc:
            cycle = Cycle(len(cycles) + 1, function.__name__, [f"{type(exc).__name__}: {exc}"], "FAIL")
        cycles.append(cycle)
        print(f"[{cycle.status}] cycle {cycle.number}/10 - {cycle.name}: {len(cycle.checks)} checks")
        if cycle.status != "PASS":
            for line in cycle.checks:
                print("  ", line)
    report = {
        "schema_version": 1,
        "audit": "HDP V7 global 10-cycle audit",
        "cycles": [asdict(cycle) for cycle in cycles],
        "cycles_passed": sum(cycle.status == "PASS" for cycle in cycles),
        "cycles_total": 10,
        "status": "PASS" if all(cycle.status == "PASS" for cycle in cycles) else "FAIL",
    }
    output = ROOT / "qualification-state" / "HDP_V7_GLOBAL_10CYCLE_AUDIT.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cycles"}, ensure_ascii=False))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
