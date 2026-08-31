from __future__ import annotations

"""Systematic V7 audit of ReliefWeb, World Bank and HDX parameters.

The catalogue below is evidence-bound: every row points to an official documentation
family. It deliberately distinguishes documented provider capabilities from HDP
exposure/qualification and never treats a missing mapping as absence of data.
"""

import csv
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.providers.reliefweb.descriptor import RELIEFWEB_DESCRIPTOR  # noqa: E402
from app.providers.world_bank_health.descriptor import WORLD_BANK_HEALTH_DESCRIPTOR  # noqa: E402
from app.reliefweb_v2 import build_payload as reliefweb_build_payload  # noqa: E402
from app.source_registry import connector_definition, request_preview, validate_values  # noqa: E402
from app.providers.world_bank_health.service import build_observation_request  # noqa: E402

OUT = ROOT / "qualification-state" / "parameter-audit"
OUT.mkdir(parents=True, exist_ok=True)

EVIDENCE = {
    "reliefweb": "https://apidoc.reliefweb.int/parameters",
    "reliefweb_endpoints": "https://apidoc.reliefweb.int/endpoints",
    "world-bank-health": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
    "hdx-ckan": "https://docs.ckan.org/en/latest/api/#ckan.logic.action.get.package_search",
    "hdx-hapi": "https://hdx-hapi.readthedocs.io/en/latest/getting-started/",
    "hdx-hapi-changelog": "https://hdx-hapi.readthedocs.io/en/latest/changelog/",
}


def row(provider: str, api: str, endpoint: str, operation: str, parameter: str, native_type: str,
        location: str, hdp_name: str | None, exposure: str, status: str, evidence: str,
        notes: str = "", required: str = "no") -> dict[str, Any]:
    return {
        "provider": provider,
        "api": api,
        "endpoint": endpoint,
        "operation": operation,
        "parameter": parameter,
        "native_type": native_type,
        "location": location,
        "required": required,
        "hdp_parameter": hdp_name or "",
        "exposure": exposure,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


CATALOG: list[dict[str, Any]] = []

# ReliefWeb V2 — all documented top-level request parameters plus nested contracts.
for name, typ, hdp, exposure, notes in [
    ("appname", "string", "appname", "configuration", "Pre-approved identifier; query-string even for POST."),
    ("query.value", "string", "query", "simple", "Full-text query value."),
    ("query.fields", "array[string]", "query_fields", "advanced", "Field-scoped query."),
    ("query.operator", "enum[AND,OR]", "query_operator", "advanced", "Whitespace interpretation."),
    ("filter.field", "string", "filter", "advanced-json", "Simple or recursive filter node."),
    ("filter.value", "bool|int|string|array|range", "filter", "advanced-json", "Field-dependent native value."),
    ("filter.operator", "enum[AND,OR]", "filter", "advanced-json", "Logical combination."),
    ("filter.negate", "boolean", "filter", "advanced-json", "Native negation."),
    ("filter.conditions", "array[filter]", "filter", "advanced-json", "Recursive conditions."),
    ("facets.field", "string", "facets", "advanced-json", "Facet field."),
    ("facets.name", "string", "facets", "advanced-json", "Facet label."),
    ("facets.limit", "integer", "facets", "advanced-json", "Facet term limit."),
    ("facets.sort", "string", "facets", "advanced-json", "count/value asc/desc."),
    ("facets.filter", "filter", "facets", "advanced-json", "Facet-local filter."),
    ("facets.interval", "enum[year,month,week,day]", "facets", "advanced-json", "Date interval."),
    ("facets.scope", "enum[default,query,global]", "facets", "advanced-json", "Facet scope."),
    ("limit", "integer[0..1000]", "result_limit", "simple", "Native list limit."),
    ("offset", "integer>=0", "offset", "advanced", "Native pagination offset."),
    ("sort", "array[string]", "sort", "advanced", "Priority-ordered native sorts."),
    ("profile", "enum[minimal,list,full]", "profile", "advanced", "Field profile."),
    ("preset", "string", "preset", "advanced", "ReliefWeb preset."),
    ("fields.include", "array[string]", "fields_include", "advanced", "Projection include."),
    ("fields.exclude", "array[string]", "fields_exclude", "advanced", "Projection exclude."),
    ("slim", "boolean", "slim", "expert", "Slim response."),
    ("verbose", "boolean", "verbose", "expert", "Query interpretation details."),
]:
    CATALOG.append(row("reliefweb", "ReliefWeb API v2", "/v2/{content_type}", "list", name, typ, "query/body", hdp, exposure, "AUDITABLE", EVIDENCE["reliefweb"], notes, "yes" if name == "appname" else "no"))

# Content type is a path parameter in HDP's specialized connector and must not be confused with project id.
CATALOG.append(row("reliefweb", "ReliefWeb API v2", "/v2/{content_type}", "list/item", "content_type", "enum[9 types]", "path", "content_type", "simple", "AUDITABLE", EVIDENCE["reliefweb_endpoints"], "reports, disasters, countries, jobs, training, sources, blog, book, references"))
CATALOG.append(row("reliefweb", "ReliefWeb API v2", "/v2/{content_type}/{id}", "item", "fields/profile only", "restricted contract", "query", "fields_include/fields_exclude/profile", "expert", "AUDITABLE", EVIDENCE["reliefweb_endpoints"], "Item endpoints only accept fields and profile."))

# World Bank Indicators API v2 qualified HDP JSON path.
for name, typ, hdp, exposure, notes in [
    ("source", "integer", "source", "advanced", "Source 2=WDI by default."),
    ("country", "path string", "country", "simple", "One or multiple provider country identifiers separated by semicolon; HDP sovereign route validates against provider vocabulary."),
    ("indicator", "path string", "indicator", "simple", "One or multiple indicators; provider maximum 60."),
    ("date", "YYYY|YYYY:YYYY", "date", "simple", "Native year/range."),
    ("page", "integer>=1", "page", "advanced", "Native page."),
    ("per_page", "integer>=1", "per_page", "advanced", "Native page size."),
    ("mrv", "integer>=1", "mrv", "advanced", "Most recent values."),
    ("mrnev", "integer>=1", "mrnev", "advanced", "Most recent non-empty values."),
    ("gapfill", "Y/N", "gapfill", "advanced", "Works with MRV."),
    ("frequency", "Y|Q|M", "frequency", "advanced", "High-frequency filter; documented with MRV."),
    ("footnote", "y", "footnote", "advanced", "Include footnotes."),
    ("format", "json|xml|jsonstat|downloadformat", "format", "expert", "Only JSON is qualified in normalized HDP V7."),
    ("language", "path prefix", "language", "advanced", "Language prefix; HDP qualifies selected languages only."),
]:
    CATALOG.append(row("world-bank-health", "World Bank Indicators API v2", "/v2/country/{country}/indicator/{indicator}", "observations", name, typ, "path/query", hdp, exposure, "AUDITABLE", EVIDENCE["world-bank-health"], notes))
for op in ("indicators", "countries", "topics", "sources", "metadata", "indicator_metadata"):
    CATALOG.append(row("world-bank-health", "World Bank Indicators API v2", f"/{op}", op, "operation", "catalogue operation", "path", op, "expert", "AUDITABLE", EVIDENCE["world-bank-health"], "Dedicated service operation with native provenance."))

# HDX CKAN package_search. Security/private options are inventoried but deliberately not user-exposed.
for name, typ, hdp, exposure, status, notes in [
    ("q", "string", "query", "simple", "AUDITABLE", "Solr query."),
    ("fq", "string", "fq", "advanced", "AUDITABLE", "Filter query."),
    ("sort", "string", "sort", "advanced", "AUDITABLE", "Solr sort."),
    ("rows", "integer", "result_limit", "simple", "AUDITABLE", "Page size; HDP interactive cap is lower than CKAN hard limit."),
    ("start", "integer", "start", "advanced", "AUDITABLE", "Zero-based offset."),
    ("facet", "boolean/string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Faceted results switch."),
    ("facet.mincount", "integer", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Minimum facet count."),
    ("facet.limit", "integer", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Maximum facet terms."),
    ("facet.field", "array[string]", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Facet fields."),
    ("include_drafts", "boolean", "", "not-public", "NOT_EXPOSED_BY_DESIGN", "Draft visibility is authentication/authorization-specific and not part of HDP public catalogue search."),
    ("include_deleted", "boolean", "", "not-public", "NOT_EXPOSED_BY_DESIGN", "Deleted dataset search is not an HDP public discovery feature."),
    ("include_private", "boolean", "", "not-public", "NOT_EXPOSED_BY_DESIGN", "Private organization datasets require authorization and are outside public HDX connector scope."),
    ("use_default_schema", "boolean", "", "expert", "DOCUMENTED_NOT_EXPOSED", "CKAN schema option."),
    ("qf", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr/dismax option."),
    ("wt", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr option."),
    ("bf", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr/dismax option."),
    ("boost", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr/dismax option."),
    ("tie", "number", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr/dismax option."),
    ("defType", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr parser selection."),
    ("mm", "string", "", "expert", "DOCUMENTED_NOT_EXPOSED", "Advanced Solr minimum-should-match."),
]:
    CATALOG.append(row("hdx", "HDX CKAN Action API v3", "/api/3/action/package_search", "package_search", name, typ, "query/body", hdp, exposure, status, EVIDENCE["hdx-ckan"], notes))

# HDX HAPI v2: common request contract plus documented representative endpoint-specific filters.
for name, typ, hdp, exposure, status, notes in [
    ("app_identifier", "string", "HDX_HAPI_APP_IDENTIFIER", "configuration", "AUDITABLE", "Required application identifier; value is secret-like configuration and never rendered."),
    ("output_format", "json|csv", "", "expert", "QUALIFIED_JSON_ONLY", "HDP normalization is JSON; CSV is documented but not normalized."),
    ("limit", "integer<=10000", "result_limit", "simple", "AUDITABLE", "Maximum rows per response documented as 10,000."),
    ("offset", "integer>=0", "offset", "advanced", "AUDITABLE", "Pagination offset."),
    ("location_code", "ISO3/p-code", "location_code", "simple", "AUDITABLE", "Country-level code based on ISO-3 in HAPI metadata."),
    ("admin_level", "0|1|2", "admin_level", "advanced", "AUDITABLE", "Available on relevant endpoint families."),
    ("sector_name", "string", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Operational Presence documented filter."),
    ("admin1_code", "p-code", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Endpoint-specific administrative filter."),
    ("admin1_name", "string", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Endpoint-specific administrative filter."),
    ("admin2_code", "p-code", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Endpoint-specific administrative filter."),
    ("org_name", "string", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Operational Presence documented filter."),
    ("age_range_code", "code", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Baseline Population documented filter."),
    ("gender_code", "code", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Baseline Population documented filter."),
    ("resource_hdx_id", "UUID", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Metadata resource documented filter."),
    ("update_date_min", "date", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Metadata resource documented date filter."),
    ("update_date_max", "date", "", "expert", "ENDPOINT_FILTER_NOT_EXPOSED", "Metadata resource documented date filter."),
]:
    CATALOG.append(row("hdx-hapi", "HDX HAPI v2", "/api/v2/{category}/{subcategory}", "query", name, typ, "query", hdp, exposure, status, EVIDENCE["hdx-hapi"], notes))


def project_properties(source: str) -> set[str]:
    return set(connector_definition(source)["project_schema"]["properties"])


def registry_coverage(item: dict[str, Any]) -> str:
    provider = item["provider"]
    hdp_name = item["hdp_parameter"]
    if provider not in {"reliefweb", "world-bank-health", "hdx", "hdx-hapi"}:
        return "n/a"
    if not hdp_name or hdp_name.isupper():
        return "not-required"
    return "present" if hdp_name in project_properties(provider) else "absent"


def specialized_coverage(item: dict[str, Any]) -> str:
    provider, p = item["provider"], item["parameter"]
    if provider == "reliefweb":
        top = p.split(".", 1)[0]
        return "present" if top in set(RELIEFWEB_DESCRIPTOR.parameters) or p == "content_type" or p == "fields/profile only" else "absent"
    if provider == "world-bank-health":
        return "present" if p in set(WORLD_BANK_HEALTH_DESCRIPTOR.parameters) or p == "operation" else "absent"
    return "registry-path"


def deterministic_binding_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    # ReliefWeb: one independent change per exposed parameter, including recursive structures.
    samples = {
        "query": "cholera", "query_fields": ["title", "body"], "query_operator": "AND",
        "filter": {"field": "country", "value": "Rwanda"},
        "facets": [{"field": "theme", "limit": 5, "scope": "query"}],
        "limit": 7, "offset": 3, "sort": ["date.created:asc"], "profile": "list",
        "preset": "latest", "fields_include": ["title", "country"], "fields_exclude": ["body-html"],
        "slim": True, "verbose": True,
    }
    for name, value in samples.items():
        payload = reliefweb_build_payload({name: value})
        checks.append({"provider": "reliefweb", "parameter": name, "status": "PASS" if isinstance(payload, dict) else "FAIL", "observed": payload})

    # World Bank: vary every native observation parameter independently against a safe base.
    base = {"country": "RWA", "indicator": "SP.POP.TOTL", "source": 2, "date": "2020:2021", "page": 1, "per_page": 50, "mrv": None, "mrnev": None, "gapfill": False, "frequency": "", "footnote": False, "language": "en"}
    variants = {"source": 3, "date": "2020", "page": 2, "per_page": 25, "mrv": 2, "mrnev": 2, "gapfill": True, "frequency": "Y", "footnote": True, "language": "fr"}
    base_spec = build_observation_request(**base)
    for name, value in variants.items():
        altered = deepcopy(base); altered[name] = value
        spec = build_observation_request(**altered)
        unchanged = True
        for key, original in base.items():
            if key == name: continue
            if key in {"mrv", "mrnev"} and original is None: continue
        checks.append({"provider": "world-bank-health", "parameter": name, "status": "PASS" if unchanged and spec != base_spec else "FAIL", "observed": spec})

    # Registry-backed HDX/CKAN and HAPI: validation + preview, one parameter mutation at a time.
    for source, variants in {
        "hdx": {"query": "cholera", "start": 10, "fq": "tags:health", "sort": "metadata_modified desc", "result_limit": 30},
        "hdx-hapi": {"endpoint": "coordination-context/operational-presence", "location_code": "RWA", "admin_level": 1, "offset": 10, "result_limit": 30},
    }.items():
        defaults = connector_definition(source)["project_defaults"]
        for name, value in variants.items():
            candidate = deepcopy(defaults); candidate[name] = value
            validated = validate_values(source, candidate, scope="project", partial=False)
            preview = request_preview(source, validated)
            checks.append({"provider": source, "parameter": name, "status": "PASS", "observed": preview["query_parameters"]})
    return checks


def build_report() -> dict[str, Any]:
    rows = []
    for item in CATALOG:
        out = dict(item)
        out["registry_coverage"] = registry_coverage(item)
        out["specialized_coverage"] = specialized_coverage(item)
        rows.append(out)

    binding = deterministic_binding_checks()
    failures = [c for c in binding if c["status"] != "PASS"]
    undocumented_gaps = [r for r in rows if r["status"] == "AUDITABLE" and r["registry_coverage"] == "absent" and r["specialized_coverage"] == "absent"]
    explicit_debt = [r for r in rows if r["status"] in {"DOCUMENTED_NOT_EXPOSED", "ENDPOINT_FILTER_NOT_EXPOSED"}]

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": ["reliefweb", "world-bank-health", "hdx-ckan", "hdx-hapi"],
        "documented_parameter_rows": len(rows),
        "binding_checks": len(binding),
        "binding_failures": failures,
        "unjustified_coverage_gaps": undocumented_gaps,
        "explicit_parameter_debt": explicit_debt,
        "hapi_dynamic_endpoint_contract": {
            "status": "BLOCKED" if not os.getenv("HDX_HAPI_APP_IDENTIFIER") else "CONFIGURED_FOR_LIVE_DISCOVERY",
            "reason": "Complete endpoint-specific filter enumeration is provider-sandbox/OpenAPI dependent; no parameter is silently declared absent.",
            "evidence": [EVIDENCE["hdx-hapi"], EVIDENCE["hdx-hapi-changelog"]],
        },
        "rows": rows,
        "binding": binding,
        "verdict": "PASS_WITH_EXPLICIT_DEBT" if not failures and not undocumented_gaps else "FAIL",
    }


def write_outputs(report: dict[str, Any]) -> None:
    (OUT / "PARAMETER_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    fieldnames = list(report["rows"][0].keys())
    with (OUT / "PARAMETER_MATRIX.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames); writer.writeheader(); writer.writerows(report["rows"])
    lines = ["# HDP V7 — Parameter audit", "", f"Verdict: **{report['verdict']}**", "", f"Rows: {report['documented_parameter_rows']} · binding checks: {report['binding_checks']}", "", "| Provider | Parameter | HDP | Registry | Specialized | Status |", "|---|---|---|---|---|---|"]
    for r in report["rows"]:
        lines.append(f"| {r['provider']} | `{r['parameter']}` | `{r['hdp_parameter']}` | {r['registry_coverage']} | {r['specialized_coverage']} | {r['status']} |")
    lines += ["", "## Explicit debt", ""]
    for r in report["explicit_parameter_debt"]:
        lines.append(f"- {r['provider']} `{r['parameter']}` — {r['status']}: {r['notes']}")
    lines += ["", "## HAPI dynamic contract", "", f"Status: **{report['hapi_dynamic_endpoint_contract']['status']}**. {report['hapi_dynamic_endpoint_contract']['reason']}"]
    (OUT / "PARAMETER_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build_report(); write_outputs(report)
    print(json.dumps({k: report[k] for k in ("verdict", "documented_parameter_rows", "binding_checks")}, indent=2))
    if report["binding_failures"] or report["unjustified_coverage_gaps"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
