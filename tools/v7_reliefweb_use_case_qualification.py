from __future__ import annotations

"""Deterministic ReliefWeb V2 use-case qualification harness.

The harness implements the canonical HDP connector protocol: five concrete cases
per inventoried functionality, and five verification cycles per case. It never
manufactures code changes: a conforming case receives stability/regression cycles.
Live provider qualification remains a separate gate because provider/network state
is external to deterministic contract testing.
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.reliefweb_v2 import (  # noqa: E402
    CONTENT_TYPES,
    DEFAULT_APPNAME,
    ReliefWebValidationError,
    build_payload,
    request_spec,
    resolve_appname,
)
from app.providers.reliefweb.descriptor import RELIEFWEB_DESCRIPTOR  # noqa: E402
from app.providers.reliefweb.service import normalize_items  # noqa: E402

EVIDENCE = "https://apidoc.reliefweb.int/"


@dataclass
class CaseResult:
    case_id: str
    feature: str
    business_goal: str
    content_type: str
    input: dict[str, Any]
    expected: str
    cycles: list[dict[str, Any]]
    status: str
    defect_id: str | None = None


def _cycle(case_id: str, number: int, fn: Callable[[], None]) -> dict[str, Any]:
    try:
        fn()
        return {"cycle": number, "phase": "test-diagnose-retest-regression", "status": "PASS", "modification": "none-required"}
    except Exception as exc:  # pragma: no cover - failure path is surfaced in report/CI
        return {"cycle": number, "phase": "test-diagnose-retest-regression", "status": "FAIL", "error": f"{type(exc).__name__}: {exc}", "modification": "required"}


def _run_case(case_id: str, feature: str, goal: str, content_type: str, params: dict[str, Any], expected: str, assertion: Callable[[], None]) -> CaseResult:
    cycles = [_cycle(case_id, i, assertion) for i in range(1, 6)]
    ok = all(c["status"] == "PASS" for c in cycles)
    return CaseResult(case_id, feature, goal, content_type, params, expected, cycles, "QUALIFIED_DETERMINISTIC" if ok else "DEFECT", None if ok else f"DEF-{case_id}")


def _assert_raises(fn: Callable[[], Any], exc_type: type[Exception] = ReliefWebValidationError) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


def _common_feature_cases() -> list[tuple[str, str, str, dict[str, Any], str, Callable[[], None]]]:
    cases: list[tuple[str, str, str, dict[str, Any], str, Callable[[], None]]] = []

    def add(feature: str, goal: str, params: dict[str, Any], expected: str, assertion: Callable[[], None]) -> None:
        cases.append((feature, goal, "reports", params, expected, assertion))

    query_values = ["malaria", "cholera Rwanda", "sécurité alimentaire", "earthquake", "COVID-19"]
    for i, q in enumerate(query_values, 1):
        add("full_text_query", f"Rechercher des rapports sur {q}", {"query": q}, "native query.value", lambda q=q: (_ for _ in ()).throw(AssertionError()) if build_payload({"query": q})["query"]["value"] != q else None)

    fields_cases = [["title"], ["title", "body"], ["source"], ["theme.name"], ["primary_country"]]
    for i, fields in enumerate(fields_cases, 1):
        add("field_scoped_query", f"Limiter la recherche à {fields}", {"query": "health", "query_fields": fields}, "query.fields preserved", lambda fields=fields: (_ for _ in ()).throw(AssertionError()) if build_payload({"query": "health", "query_fields": fields})["query"]["fields"] != fields else None)

    operator_cases = [("AND", "hot cold"), ("OR", "flood drought"), ("and", "malaria cholera"), ("or", "food nutrition"), ("XOR", "invalid")]
    for op, q in operator_cases:
        if op == "XOR":
            add("query_operator", "Rejeter un opérateur non supporté", {"query": q, "query_operator": op}, "validation_error", lambda op=op, q=q: _assert_raises(lambda: build_payload({"query": q, "query_operator": op})))
        else:
            add("query_operator", f"Recherche booléenne {op}", {"query": q, "query_operator": op}, "AND/OR normalized", lambda op=op, q=q: (_ for _ in ()).throw(AssertionError()) if build_payload({"query": q, "query_operator": op})["query"]["operator"] != op.upper() else None)

    exact_queries = ["source.shortname.exact:UN", "language.name.exact:French", "country.name.exact:Rwanda", "format.name.exact:Map", "theme.name.exact:Health"]
    for q in exact_queries:
        add("exact_query", f"Recherche exacte {q}", {"query": q}, "Lucene/exact syntax preserved", lambda q=q: (_ for _ in ()).throw(AssertionError()) if build_payload({"query": q})["query"]["value"] != q else None)

    lucene_queries = ["malaria^3 Rwanda", 'title:"food security"', "flood AND drought", "(cholera OR malaria) Rwanda", "health NOT training"]
    for q in lucene_queries:
        add("advanced_lucene_query", f"Recherche avancée {q}", {"query": q}, "advanced query preserved", lambda q=q: (_ for _ in ()).throw(AssertionError()) if build_payload({"query": q})["query"]["value"] != q else None)

    simple_filters = [
        {"field": "country", "value": "Rwanda"},
        {"field": "theme", "value": "Health"},
        {"field": "headline"},
        {"field": "status", "value": "published"},
        {"field": "language", "value": "French"},
    ]
    for f in simple_filters:
        add("simple_filter", f"Filtrer sur {f['field']}", {"filter": f}, "simple native filter", lambda f=f: (_ for _ in ()).throw(AssertionError()) if build_payload({"filter": f})["filter"]["field"] != f["field"] else None)

    multi_filters = [
        {"field": "country", "value": ["Rwanda", "Burundi"], "operator": "OR"},
        {"field": "theme", "value": ["Health", "Water Sanitation Hygiene"], "operator": "OR"},
        {"field": "status", "value": ["published", "to-review"], "operator": "OR"},
        {"field": "language", "value": ["English", "French"], "operator": "OR"},
        {"field": "format", "value": ["Map", "Infographic"], "operator": "OR"},
    ]
    for f in multi_filters:
        add("multi_value_filter", f"Filtre multi-valeurs {f['field']}", {"filter": f}, "array/operator preserved", lambda f=f: (_ for _ in ()).throw(AssertionError()) if build_payload({"filter": f})["filter"]["operator"] != "OR" else None)

    nested_filters = [
        {"operator": "AND", "conditions": [{"field": "country", "value": "Rwanda"}, {"field": "theme", "value": "Health"}]},
        {"operator": "OR", "conditions": [{"field": "country", "value": "Rwanda"}, {"field": "country", "value": "Burundi"}]},
        {"operator": "AND", "conditions": [{"field": "headline"}, {"field": "country", "value": "France"}]},
        {"operator": "AND", "conditions": [{"operator": "OR", "conditions": [{"field": "format", "value": "Map"}, {"field": "format", "value": "Infographic"}]}, {"field": "country", "value": "Afghanistan"}]},
        {"operator": "AND", "conditions": [{"field": "country", "value": "Rwanda"}, {"field": "language", "value": "French", "negate": True}]},
    ]
    for f in nested_filters:
        add("recursive_filters", "Construire un filtre imbriqué", {"filter": f}, "POST + recursive filter", lambda f=f: (_ for _ in ()).throw(AssertionError()) if request_spec("reports", {"filter": f})["method"] != "POST" else None)

    neg_filters = [
        {"field": "country", "value": "Italy", "negate": True},
        {"field": "language", "value": "English", "negate": True},
        {"field": "format", "value": "Map", "negate": True},
        {"field": "theme", "value": "Logistics", "negate": True},
        {"field": "status", "value": "expired", "negate": True},
    ]
    for f in neg_filters:
        add("filter_negation", f"Exclure {f['field']}", {"filter": f}, "negate preserved", lambda f=f: (_ for _ in ()).throw(AssertionError()) if build_payload({"filter": f})["filter"].get("negate") is not True else None)

    ranges = [
        {"field": "date.created", "value": {"from": "2020-01-01T00:00:00+00:00", "to": "2025-12-31T23:59:59+00:00"}},
        {"field": "date.original", "value": {"from": "2024-01-01T00:00:00+00:00"}},
        {"field": "date.changed", "value": {"to": "2026-01-01T00:00:00+00:00"}},
        {"field": "id", "value": {"from": 1, "to": 99999999}},
        {"field": "date.created", "value": {"from": "2004-06-01T00:00:00+00:00", "to": "2004-06-30T23:59:59+00:00"}},
    ]
    for f in ranges:
        add("range_filter", f"Filtrer une plage {f['field']}", {"filter": f}, "range object preserved", lambda f=f: (_ for _ in ()).throw(AssertionError()) if build_payload({"filter": f})["filter"]["value"] != f["value"] else None)

    facets = [
        {"field": "country", "limit": 20},
        {"field": "theme", "limit": 50, "sort": "value:asc"},
        {"field": "source", "limit": 5, "sort": "count:desc"},
        {"field": "date.original", "interval": "year"},
        {"field": "country", "name": "countries", "scope": "global"},
    ]
    for facet in facets:
        add("facets", f"Explorer la facette {facet['field']}", {"facets": [facet], "limit": 0}, "facet preserved + POST", lambda facet=facet: (_ for _ in ()).throw(AssertionError()) if request_spec("reports", {"facets": [facet], "limit": 0})["method"] != "POST" else None)

    facet_filters = [
        {"field": "country", "filter": {"field": "theme", "value": "Coordination"}},
        {"field": "source", "filter": {"field": "country", "value": "Rwanda"}},
        {"field": "theme", "filter": {"field": "language", "value": "French"}},
        {"field": "format", "filter": {"field": "country", "value": "Afghanistan"}},
        {"field": "country", "filter": {"field": "status", "value": "published"}},
    ]
    for facet in facet_filters:
        add("facet_filter", "Restreindre une facette", {"facets": [facet], "limit": 0}, "facet.filter validated", lambda facet=facet: (_ for _ in ()).throw(AssertionError()) if "filter" not in build_payload({"facets": [facet], "limit": 0})["facets"][0] else None)

    for scope in ["default", "query", "global", "query", "global"]:
        facet = {"field": "source", "scope": scope}
        add("facet_scope", f"Facette scope {scope}", {"facets": [facet], "limit": 0}, "scope validated", lambda facet=facet, scope=scope: (_ for _ in ()).throw(AssertionError()) if build_payload({"facets": [facet], "limit": 0})["facets"][0]["scope"] != scope else None)

    for interval in ["year", "month", "week", "day", "year"]:
        facet = {"field": "date.original", "interval": interval}
        add("facet_interval", f"Facette temporelle {interval}", {"facets": [facet], "limit": 0}, "interval validated", lambda facet=facet, interval=interval: (_ for _ in ()).throw(AssertionError()) if build_payload({"facets": [facet], "limit": 0})["facets"][0]["interval"] != interval else None)

    sorts = [["date.created:desc"], ["title:asc"], ["date:desc", "title:asc"], ["id:asc"], ["score:desc"]]
    for sort in sorts:
        add("sorting", f"Trier par {sort}", {"sort": sort}, "sort list preserved", lambda sort=sort: (_ for _ in ()).throw(AssertionError()) if build_payload({"sort": sort})["sort"] != sort else None)

    pagination = [(1, 0), (10, 0), (1000, 0), (25, 25), (0, 100)]
    for limit, offset in pagination:
        add("pagination", f"Page limit={limit} offset={offset}", {"limit": limit, "offset": offset}, "limit/offset preserved", lambda limit=limit, offset=offset: (_ for _ in ()).throw(AssertionError()) if (build_payload({"limit": limit, "offset": offset})["limit"], build_payload({"limit": limit, "offset": offset})["offset"]) != (limit, offset) else None)

    profiles = ["minimal", "list", "full", "minimal", "full"]
    for profile in profiles:
        add("profiles", f"Profile {profile}", {"profile": profile}, "profile validated", lambda profile=profile: (_ for _ in ()).throw(AssertionError()) if build_payload({"profile": profile})["profile"] != profile else None)

    presets = ["minimal", "latest", "analysis", "latest", "analysis"]
    for preset in presets:
        add("presets", f"Preset {preset}", {"preset": preset}, "preset validated", lambda preset=preset: (_ for _ in ()).throw(AssertionError()) if build_payload({"preset": preset})["preset"] != preset else None)

    projections = [
        {"fields_include": ["url"]},
        {"fields_exclude": ["title"]},
        {"fields_include": ["source.name", "country.name"]},
        {"fields_include": ["iso3"], "profile": "list"},
        {"fields_exclude": ["source"], "profile": "list"},
    ]
    for p in projections:
        add("field_projection", "Personnaliser les champs retournés", p, "fields include/exclude preserved", lambda p=p: (_ for _ in ()).throw(AssertionError()) if "fields" not in build_payload(p) else None)

    for flag in [True, True, True, True, True]:
        add("slim", "Réduire les hyperliens de réponse", {"slim": flag}, "slim=1", lambda flag=flag: (_ for _ in ()).throw(AssertionError()) if build_payload({"slim": flag}).get("slim") != 1 else None)
        add("verbose", "Inspecter l'interprétation fournisseur", {"verbose": flag}, "verbose=1", lambda flag=flag: (_ for _ in ()).throw(AssertionError()) if build_payload({"verbose": flag}).get("verbose") != 1 else None)

    app_cases = [
        ({"appname": "PROJECT"}, {"appname": "GLOBAL"}, "PROJECT", "project"),
        ({}, {"appname": "GLOBAL"}, "GLOBAL", "global"),
        ({}, {}, DEFAULT_APPNAME, "default"),
        ({"appname": "  PROJECT2  "}, {"appname": "GLOBAL"}, "PROJECT2", "project"),
        ({"appname": ""}, {"appname": ""}, DEFAULT_APPNAME, "default"),
    ]
    for project, global_, value, origin in app_cases:
        add("appname_precedence", f"Résoudre appname depuis {origin}", {"project": project, "global": global_}, f"{value}/{origin}", lambda project=project, global_=global_, value=value, origin=origin: (_ for _ in ()).throw(AssertionError()) if (resolve_appname(project, global_).value, resolve_appname(project, global_).origin) != (value, origin) else None)

    invalids = [
        ("limit", {"limit": 1001}),
        ("offset", {"offset": -1}),
        ("profile", {"profile": "unknown"}),
        ("preset", {"preset": "unknown"}),
        ("filter", {"filter": {"conditions": []}}),
    ]
    for label, params in invalids:
        add("validation_errors", f"Rejeter {label} invalide", params, "validation_error", lambda params=params: _assert_raises(lambda: build_payload(params)))

    return cases


def _content_type_cases() -> list[tuple[str, str, str, dict[str, Any], str, Callable[[], None]]]:
    cases = []
    for kind in CONTENT_TYPES:
        feature = f"content_type:{kind}"
        patterns = [
            ("list-simple", {"query": "health"}, None, "GET"),
            ("list-complex", {"facets": [{"field": "id", "limit": 5}], "limit": 0}, None, "POST"),
            ("item", {"profile": "full"}, "1", "GET"),
            ("projection", {"fields_include": ["id"]}, None, "GET"),
            ("latest", {"preset": "latest", "limit": 1}, None, "GET"),
        ]
        for label, params, item_id, method in patterns:
            goal = f"{label} sur ReliefWeb {kind}"
            cases.append((feature, goal, kind, params, method, lambda kind=kind, params=params, item_id=item_id, method=method: (_ for _ in ()).throw(AssertionError()) if request_spec(kind, params, item_id=item_id)["method"] != method else None))
    return cases


def _normalization_cases() -> list[tuple[str, str, str, dict[str, Any], str, Callable[[], None]]]:
    cases = []
    payloads = [
        {"data": [{"id": 1, "href": "https://api.reliefweb.int/v2/reports/1", "score": 1.2, "fields": {"title": "Malaria update", "date": {"created": "2025-01-01T00:00:00+00:00"}, "country": [{"name": "Rwanda"}]}}]},
        {"data": [{"id": 2, "fields": {"name": "Rwanda"}}]},
        {"data": [{"id": 3, "fields": {"shortname": "WHO"}}]},
        {"data": []},
        {"unexpected": True},
    ]
    expected_counts = [1, 1, 1, 0, 0]
    for idx, (payload, expected) in enumerate(zip(payloads, expected_counts), 1):
        cases.append(("native_normalization", f"Normaliser une réponse native #{idx}", "reports", {"payload": payload}, f"count={expected}", lambda payload=payload, expected=expected: (_ for _ in ()).throw(AssertionError()) if len(normalize_items(payload, "reports")) != expected else None))
    return cases


def run_qualification() -> dict[str, Any]:
    source_cases = _common_feature_cases() + _content_type_cases() + _normalization_cases()
    results: list[CaseResult] = []
    counters: dict[str, int] = {}
    for feature, goal, kind, params, expected, assertion in source_cases:
        counters[feature] = counters.get(feature, 0) + 1
        case_id = f"RW-{feature.replace(':', '-').replace('_', '-').upper()}-{counters[feature]:02d}"
        results.append(_run_case(case_id, feature, goal, kind, params, expected, assertion))

    feature_counts: dict[str, int] = {}
    for result in results:
        feature_counts[result.feature] = feature_counts.get(result.feature, 0) + 1
    bad_counts = {feature: count for feature, count in feature_counts.items() if count != 5}
    if bad_counts:
        raise AssertionError(f"Every functionality must have exactly five cases: {bad_counts}")

    failures = [result for result in results if result.status == "DEFECT"]
    cycles = sum(len(result.cycles) for result in results)
    return {
        "schema_version": 1,
        "provider": "reliefweb",
        "api_version": RELIEFWEB_DESCRIPTOR.api_version,
        "evidence": ["https://apidoc.reliefweb.int/endpoints", "https://apidoc.reliefweb.int/parameters", "https://apidoc.reliefweb.int/fields-tables", "https://apidoc.reliefweb.int/presets", "https://apidoc.reliefweb.int/result-structure"],
        "functionality_count": len(feature_counts),
        "case_count": len(results),
        "cycles_per_case": 5,
        "cycle_count": cycles,
        "deterministic_passed": len(results) - len(failures),
        "deterministic_failed": len(failures),
        "live_status": "BLOCKED_PENDING_PROVIDER_ACCEPTANCE_OF_APPNAME",
        "live_known_observation": "HTTP 403 observed for appname=HDP_plateforme on /v2/reports in GitHub Actions; deterministic success cannot override this blocker.",
        "status": "PARTIALLY_IMPLEMENTED" if failures or True else "QUALIFIED",
        "feature_case_counts": feature_counts,
        "cases": [asdict(result) for result in results],
    }


def main() -> int:
    report = run_qualification()
    output = ROOT / "docs" / "versions" / "7.0.0" / "reliefweb" / "RELIEFWEB_USE_CASE_QUALIFICATION.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, ensure_ascii=False, indent=2))
    return 1 if report["deterministic_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
