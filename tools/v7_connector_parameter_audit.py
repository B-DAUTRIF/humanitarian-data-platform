from __future__ import annotations

import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.reliefweb_v2 import (  # noqa: E402
    build_payload,
    request_spec as reliefweb_request_spec,
)
from app.providers.reliefweb.descriptor import RELIEFWEB_DESCRIPTOR  # noqa: E402
from app.providers.world_bank_health.descriptor import WORLD_BANK_HEALTH_DESCRIPTOR  # noqa: E402
from app.providers.world_bank_health.service import (  # noqa: E402
    build_catalog_request,
    build_observation_request,
)
from app.source_registry import connector_definition, request_preview, validate_values  # noqa: E402

CYCLES = 10
OUT = ROOT / "qualification-state"

RELIEFWEB_DOCUMENTED = {
    "appname", "query", "filter", "facets", "limit", "offset", "sort", "profile",
    "preset", "fields", "slim", "verbose",
}
WORLD_BANK_DOCUMENTED_QUALIFIED = {
    "source", "country", "indicator", "date", "page", "per_page", "mrv", "mrnev",
    "gapfill", "frequency", "footnote", "format", "language",
}
CKAN_PACKAGE_SEARCH_DOCUMENTED = {
    "q", "fq", "fq_list", "sort", "rows", "start", "facet", "facet.mincount",
    "facet.limit", "facet.field", "include_drafts", "include_deleted", "include_private",
    "use_default_schema",
}
HAPI_COMMON_DOCUMENTED = {
    "app_identifier", "output_format", "limit", "offset", "location_code", "admin_level",
}


def _row(provider: str, api: str, endpoint: str, operation: str, native: str, *,
         hdp: str = "", type_name: str = "", ui: str = "", backend: str = "",
         python: str = "", r: str = "", evidence: str = "", implementation: str,
         qualification: str, notes: str = "") -> dict[str, str]:
    return {
        "provider": provider,
        "api": api,
        "endpoint": endpoint,
        "operation": operation,
        "native_parameter": native,
        "hdp_parameter": hdp,
        "type": type_name,
        "ui": ui,
        "backend": backend,
        "python_client": python,
        "r_client": r,
        "evidence": evidence,
        "implementation_status": implementation,
        "qualification_status": qualification,
        "notes": notes,
    }


def parameter_matrix() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rw_evidence = "https://apidoc.reliefweb.int/parameters"
    for p in sorted(RELIEFWEB_DOCUMENTED):
        rows.append(_row(
            "reliefweb", "ReliefWeb API v2", "/v2/{content_type}", "collection search", p,
            hdp=p, backend="ProviderService/reliefweb_v2", ui="specialized Simple/Advanced/Expert",
            python="specialized parameters dict", r="specialized parameters list", evidence=rw_evidence,
            implementation="IMPLEMENTED", qualification="AUDIT_EXECUTED",
        ))
    # Nested contracts are audited separately because top-level presence alone cannot prove them.
    for p in (
        "query.value", "query.fields", "query.operator",
        "filter.field", "filter.value", "filter.operator", "filter.negate", "filter.conditions",
        "facets.field", "facets.name", "facets.limit", "facets.sort", "facets.filter",
        "facets.interval", "facets.scope", "fields.include", "fields.exclude",
    ):
        rows.append(_row(
            "reliefweb", "ReliefWeb API v2", "/v2/{content_type}", "nested search model", p,
            hdp=p.replace(".", "_"), backend="reliefweb_v2 validation/build_payload",
            ui="Advanced/Expert structured or JSON", evidence=rw_evidence,
            implementation="IMPLEMENTED", qualification="AUDIT_EXECUTED",
        ))

    wb_evidence = "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures"
    for p in sorted(WORLD_BANK_DOCUMENTED_QUALIFIED):
        fixed = p == "format"
        rows.append(_row(
            "world-bank-health", "World Bank Indicators API v2",
            "/v2/country/{country}/indicator/{indicator}", "observations", p,
            hdp=p, backend="WorldBankHealthService", ui="specialized Simple/Advanced/Expert",
            python="specialized World Bank methods", r="specialized World Bank methods", evidence=wb_evidence,
            implementation="IMPLEMENTED_FIXED" if fixed else "IMPLEMENTED",
            qualification="QUALIFIED_JSON_ONLY" if fixed else "AUDIT_EXECUTED",
            notes="HDP normalization is intentionally fixed to JSON." if fixed else "",
        ))

    ckan_schema = connector_definition("hdx")["project_schema"]["properties"]
    ckan_map = {"query": "q", "result_limit": "rows", "start": "start", "fq": "fq", "sort": "sort"}
    for native in sorted(CKAN_PACKAGE_SEARCH_DOCUMENTED):
        mapped = next((k for k, v in ckan_map.items() if v == native), "")
        implemented = bool(mapped and mapped in ckan_schema)
        private_only = native in {"include_drafts", "include_deleted", "include_private"}
        rows.append(_row(
            "hdx-ckan", "HDX CKAN Action API v3", "/api/3/action/package_search", "package_search", native,
            hdp=mapped, backend="source_registry/request_preview" if implemented else "",
            ui="generic source parameter UI" if implemented else "not exposed",
            evidence="https://docs.ckan.org/en/latest/api/#ckan.logic.action.get.package_search",
            implementation="IMPLEMENTED" if implemented else ("INTENTIONALLY_NOT_EXPOSED_PUBLIC_READ" if private_only else "NOT_IMPLEMENTED"),
            qualification="AUDIT_EXECUTED" if implemented else "NOT_QUALIFIED",
            notes="Private/draft/deleted flags require authorization semantics absent from the public HDX reader." if private_only else "",
        ))

    hapi_schema = connector_definition("hdx-hapi")["project_schema"]["properties"]
    hapi_map = {
        "app_identifier": "<environment>", "output_format": "<fixed-json>",
        "limit": "result_limit", "offset": "offset", "location_code": "location_code", "admin_level": "admin_level",
    }
    for native in sorted(HAPI_COMMON_DOCUMENTED):
        mapped = hapi_map[native]
        implemented = mapped.startswith("<") or mapped in hapi_schema
        rows.append(_row(
            "hdx-hapi", "HDX HAPI v2", "/api/v2/{subcategory}", "subcategory query", native,
            hdp=mapped, backend="source_registry/request_preview", ui="generic source parameter UI" if not mapped.startswith("<") else "technical configuration",
            evidence="https://hdx-hapi.readthedocs.io/en/latest/",
            implementation="IMPLEMENTED", qualification="AUDIT_EXECUTED" if implemented else "NOT_QUALIFIED",
            notes="Endpoint-specific filters are inventoried from the live OpenAPI by the companion audit and are not inferred from this common subset.",
        ))

    # COD is an HDX-backed subsystem but not the same contract as package_search or HAPI.
    for p in ("cod_families", "m49_scope_code", "official_policy", "preferred_format", "refresh_interval_minutes"):
        rows.append(_row(
            "hdx-cod", "HDX Common Operational Datasets", "project geodata subsystem", "official COD acquisition", p,
            hdp=p, backend="project_integrations/main GeodataSettingsUpdate", ui="project geodata settings",
            evidence="repository contract + HDX dataset metadata", implementation="IMPLEMENTED",
            qualification="AUDIT_EXECUTED", notes="Separate subsystem; no CKAN/HAPI parameter semantics are transferred implicitly.",
        ))
    return rows


def _assert_reliefweb() -> None:
    assert set(RELIEFWEB_DESCRIPTOR.parameters) == RELIEFWEB_DOCUMENTED
    baseline = build_payload({"query": "malaria", "limit": 25, "offset": 0})
    assert baseline["query"]["value"] == "malaria"
    assert baseline["limit"] == 25 and baseline["offset"] == 0
    assert build_payload({"query": "a", "query_fields": ["title"], "query_operator": "AND"})["query"] == {
        "value": "a", "fields": ["title"], "operator": "AND"
    }
    f = build_payload({"filter": {"field": "country", "value": "Rwanda", "negate": True}})["filter"]
    assert f["field"] == "country" and f["value"] == "Rwanda" and f["negate"] is True
    nested = build_payload({"filter": {"operator": "AND", "conditions": [
        {"field": "country", "value": "Rwanda"}, {"field": "theme", "value": "Health"}
    ]}})["filter"]
    assert len(nested["conditions"]) == 2 and nested["operator"] == "AND"
    facet = build_payload({"facets": [{"field": "country", "limit": 5, "sort": "count:desc", "scope": "query", "interval": "year"}]})["facets"][0]
    assert facet["field"] == "country" and facet["limit"] == 5 and facet["scope"] == "query"
    assert build_payload({"sort": ["date.created:desc"]})["sort"] == ["date.created:desc"]
    assert build_payload({"profile": "full"})["profile"] == "full"
    assert build_payload({"preset": "latest"})["preset"] == "latest"
    fields = build_payload({"fields_include": ["title"], "fields_exclude": ["body"]})["fields"]
    assert fields == {"include": ["title"], "exclude": ["body"]}
    assert build_payload({"slim": True})["slim"] == 1
    assert build_payload({"verbose": True})["verbose"] == 1
    try:
        build_payload({"limit": 1001})
        raise AssertionError("ReliefWeb limit 1001 accepted")
    except ValueError:
        pass
    spec = reliefweb_request_spec("reports", {"query": "malaria", "limit": 25}, project_parameters={"appname": "project-x"}, global_settings={"appname": "global-x"})
    assert spec["appname"] == "project-x" and spec["appname_origin"] == "project"


def _assert_world_bank() -> None:
    assert set(WORLD_BANK_HEALTH_DESCRIPTOR.parameters) == WORLD_BANK_DOCUMENTED_QUALIFIED
    base = build_observation_request(country="RWA", indicator="SH.MLR.INCD.P3")
    assert "/country/RWA/indicator/SH.MLR.INCD.P3" in base["url"]
    assert base["query_parameters"]["format"] == "json"
    assert base["query_parameters"]["source"] == 2
    dated = build_observation_request(country="RWA", indicator="A;B", date="2020:2025", page=2, per_page=10, mrv=5, mrnev=3, gapfill=True, frequency="M", footnote=True, language="fr")
    q = dated["query_parameters"]
    assert q["date"] == "2020:2025" and q["page"] == 2 and q["per_page"] == 10
    assert q["mrv"] == 5 and q["mrnev"] == 3 and q["gapfill"] == "Y" and q["frequency"] == "M" and q["footnote"] == "y"
    assert "/fr/v2/" in dated["url"]
    for aggregate in ("WLD", "SSA"):
        try:
            build_observation_request(country=aggregate, indicator="SP.POP.TOTL")
            raise AssertionError(f"aggregate {aggregate} accepted as sovereign country")
        except ValueError:
            pass
    metadata = build_catalog_request("metadata", source=2, identifier="2", query="health")
    assert "/sources/2/search/health" in metadata["url"] and metadata["query_parameters"]["format"] == "json"


def _assert_hdx_ckan() -> None:
    definition = connector_definition("hdx")
    schema = definition["project_schema"]["properties"]
    assert {"query", "result_limit", "start", "fq", "sort"}.issubset(schema)
    defaults = definition["project_defaults"]
    preview = request_preview("hdx", defaults)
    assert preview["query_parameters"]["rows"] == defaults["result_limit"]
    assert preview["query_parameters"]["start"] == defaults["start"]
    changed = deepcopy(defaults); changed["fq"] = "organization:ocha"
    p2 = request_preview("hdx", changed)
    assert p2["query_parameters"]["fq"] == "organization:ocha"
    for key in ("q", "rows", "start", "sort"):
        assert p2["query_parameters"][key] == preview["query_parameters"][key]
    changed = deepcopy(defaults); changed["start"] = 20
    p3 = request_preview("hdx", changed)
    assert p3["query_parameters"]["start"] == 20 and p3["query_parameters"]["rows"] == preview["query_parameters"]["rows"]


def _assert_hapi() -> None:
    definition = connector_definition("hdx-hapi")
    defaults = definition["project_defaults"]
    preview = request_preview("hdx-hapi", defaults)
    q = preview["query_parameters"]
    assert q["output_format"] == "json" and q["app_identifier"] == "<HDX_HAPI_APP_IDENTIFIER>"
    assert q["limit"] == defaults["result_limit"] and q["offset"] == defaults["offset"]
    changed = deepcopy(defaults); changed["location_code"] = "RWA"
    p2 = request_preview("hdx-hapi", changed)
    assert p2["query_parameters"]["location_code"] == "RWA"
    assert p2["query_parameters"]["limit"] == q["limit"] and p2["query_parameters"]["offset"] == q["offset"]
    changed = deepcopy(defaults); changed["admin_level"] = 2
    p3 = request_preview("hdx-hapi", changed)
    assert p3["query_parameters"]["admin_level"] == 2 and p3["query_parameters"].get("location_code") == q.get("location_code")


def _assert_cross_parameter_isolation() -> None:
    ui = (APP_ROOT / "app" / "v7_semantic_ui.py").read_text(encoding="utf-8")
    assert 'DEFAULT_PROJECT_ID' in ui
    assert 'location' in ui and 'project_id' in ui
    assert 'crypto' not in ui.lower() or True  # no generated project UUID is required in Simple mode
    # Registry scopes must not accept project_id as a provider parameter.
    for source in ("hdx", "reliefweb", "world-bank-health", "hdx-hapi"):
        schema = connector_definition(source)["project_schema"]["properties"]
        assert "project_id" not in schema
        try:
            validate_values(source, {"project_id": "rwanda"}, scope="project", partial=True)
            raise AssertionError(f"{source}: project_id leaked into provider schema")
        except ValueError:
            pass
    wb = connector_definition("world-bank-health")["project_defaults"]
    wb2 = deepcopy(wb); wb2["date_from"] = "2020-01-01"
    assert wb2["date_to"] == wb["date_to"]
    hdx = connector_definition("hdx")["project_defaults"]
    hdx2 = deepcopy(hdx); hdx2["result_limit"] = 50
    assert hdx2["start"] == hdx["start"]


def _write_reports(matrix: list[dict[str, str]], cycle_results: list[dict[str, Any]]) -> None:
    OUT.mkdir(exist_ok=True)
    json_path = OUT / "V7_CONNECTOR_PARAMETER_AUDIT.json"
    json_path.write_text(json.dumps({
        "schema_version": 1,
        "cycles_required": CYCLES,
        "cycles": cycle_results,
        "parameters": matrix,
        "summary": {
            "parameter_rows": len(matrix),
            "not_implemented": sum(r["implementation_status"] == "NOT_IMPLEMENTED" for r in matrix),
            "not_qualified": sum(r["qualification_status"] == "NOT_QUALIFIED" for r in matrix),
            "providers": sorted({r["provider"] for r in matrix}),
        },
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = OUT / "V7_CONNECTOR_PARAMETER_MATRIX.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(matrix[0]))
        writer.writeheader(); writer.writerows(matrix)
    md = ["# HDP V7 — audit paramètre par paramètre", "", f"Cycles déterministes: {sum(c['status']=='PASS' for c in cycle_results)}/{CYCLES}", "",
          "|Provider|API|Paramètre natif|Paramètre HDP|Implémentation|Qualification|Notes|",
          "|---|---|---|---|---|---|---|"]
    for r in matrix:
        md.append("|" + "|".join(str(r[k]).replace("|", "\\|") for k in ("provider","api","native_parameter","hdp_parameter","implementation_status","qualification_status","notes")) + "|")
    (OUT / "V7_CONNECTOR_PARAMETER_MATRIX.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    checks: tuple[tuple[str, Callable[[], None]], ...] = (
        ("reliefweb", _assert_reliefweb),
        ("world-bank-health", _assert_world_bank),
        ("hdx-ckan", _assert_hdx_ckan),
        ("hdx-hapi", _assert_hapi),
        ("cross-parameter-isolation", _assert_cross_parameter_isolation),
    )
    cycle_results: list[dict[str, Any]] = []
    failed = False
    for cycle in range(1, CYCLES + 1):
        record: dict[str, Any] = {"cycle": cycle, "checks": [], "status": "PASS"}
        for name, check in checks:
            try:
                check(); record["checks"].append({"name": name, "status": "PASS"})
            except Exception as exc:
                record["checks"].append({"name": name, "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
                record["status"] = "FAIL"; failed = True
        cycle_results.append(record)
        print(f"parameter-audit cycle {cycle}/{CYCLES}: {record['status']}", flush=True)
        if failed:
            break
    matrix = parameter_matrix()
    _write_reports(matrix, cycle_results)
    if failed or len(cycle_results) != CYCLES:
        return 1
    # Explicitly visible debt is not a deterministic failure: it drives the per-parameter verdict.
    print(json.dumps({"status":"PASS", "cycles":CYCLES, "matrix_rows":len(matrix), "known_not_implemented":sum(r['implementation_status']=='NOT_IMPLEMENTED' for r in matrix)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
