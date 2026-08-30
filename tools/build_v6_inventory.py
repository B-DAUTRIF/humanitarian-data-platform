#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.health_sources import source_catalog  # noqa: E402
from app.source_registry import CONNECTORS, connector_definition  # noqa: E402

VERSION = "6.0.0"
OUT_DIR = API_ROOT / "app" / "api_inventory_parts"
DOC_DIR = ROOT / "docs" / "versions" / VERSION

SOURCE_NAMES = {item["id"]: item["name"] for item in source_catalog() if item.get("id") in CONNECTORS}

# Parameters explicitly documented by the provider for the public/search-oriented operations
# that HDP exposes or inventories. Parameters not currently mapped by HDP remain visible
# with supported=False, satisfying the UI requirement that they are still accessible as
# classified information rather than silently hidden.
CURATED_NATIVE: dict[str, list[dict[str, Any]]] = {
    "hdx": [
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"q","location":"query","type":"string","description":"Full text package search query.","supported":True},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"fq","location":"query","type":"string","description":"Solr filter query.","supported":True},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"fq_list","location":"query","type":"array","description":"Additional filter queries.","supported":False},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"sort","location":"query","type":"string","description":"Sort expression.","supported":True},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"rows","location":"query","type":"integer","description":"Maximum number of rows.","supported":True},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"start","location":"query","type":"integer","description":"Result offset.","supported":True},
        {"operation":"package_search","method":"GET","endpoint":"/api/3/action/package_search","name":"qf","location":"query","type":"string","description":"Query fields and boosts.","supported":False},
    ],
    "reliefweb": [
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"appname","location":"query","type":"string","description":"Approved ReliefWeb application identifier.","supported":True,"sensitive":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"query[value]","location":"query/body","type":"string","description":"Search expression.","supported":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"query[fields]","location":"query/body","type":"array","description":"Fields searched by the query.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"query[operator]","location":"query/body","type":"string","description":"Boolean query operator.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"filter","location":"query/body","type":"object","description":"Structured ReliefWeb filter tree.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"fields[include]","location":"query/body","type":"array","description":"Response fields to include.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"fields[exclude]","location":"query/body","type":"array","description":"Response fields to exclude.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"facets","location":"query/body","type":"array/object","description":"Facet definitions.","supported":False},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"limit","location":"query/body","type":"integer","description":"Maximum records returned.","supported":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"offset","location":"query/body","type":"integer","description":"Result offset.","supported":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"profile","location":"query/body","type":"string","description":"Response profile.","supported":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"preset","location":"query/body","type":"string","description":"ReliefWeb preset.","supported":True},
        {"operation":"reports","method":"GET/POST","endpoint":"/v2/reports","name":"sort[]","location":"query/body","type":"array/string","description":"Sort criteria.","supported":True},
    ],
    "who-gho": [
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$filter","location":"query","type":"string","description":"OData filter expression.","supported":True},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$select","location":"query","type":"string","description":"OData selected fields.","supported":False},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$orderby","location":"query","type":"string","description":"OData ordering expression.","supported":False},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$top","location":"query","type":"integer","description":"Maximum rows.","supported":True},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$skip","location":"query","type":"integer","description":"Rows skipped.","supported":True},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$format","location":"query","type":"string","description":"Response format.","supported":True},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$expand","location":"query","type":"string","description":"Related entities to expand.","supported":False},
        {"operation":"OData query","method":"GET","endpoint":"/api/{entity}","name":"$count","location":"query","type":"boolean","description":"Request total count.","supported":False},
    ],
    "world-bank-health": [
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"date","location":"query","type":"string","description":"Year, month, quarter or range.","supported":True},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"page","location":"query","type":"integer","description":"Page number.","supported":True},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"per_page","location":"query","type":"integer","description":"Results per page.","supported":True},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"mrv","location":"query","type":"integer","description":"Most recent values count.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"mrnev","location":"query","type":"integer","description":"Most recent non-empty values count.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"gapfill","location":"query","type":"string","description":"Backfill missing periods when using MRV.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"frequency","location":"query","type":"string","description":"Y, Q or M frequency.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"source","location":"query","type":"string","description":"Source identifier.","supported":True},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"footnote","location":"query","type":"string","description":"Include footnotes.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"format","location":"query","type":"string","description":"Response format such as json or xml.","supported":True},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{resource}","name":"downloadformat","location":"query","type":"string","description":"Bulk download format where available.","supported":False},
        {"operation":"Indicators API v2","method":"GET","endpoint":"/v2/{language}/{resource}","name":"language","location":"path","type":"string","description":"Language code.","supported":True},
        {"operation":"Indicator data","method":"GET","endpoint":"/v2/country/{country}/indicator/{indicator}","name":"country","location":"path","type":"string","description":"Country or economy code(s).","supported":True},
        {"operation":"Indicator data","method":"GET","endpoint":"/v2/country/{country}/indicator/{indicator}","name":"indicator","location":"path","type":"string","description":"Indicator code(s).","supported":True},
    ],
    "unicef-sdmx": [
        {"operation":"dataflow","method":"GET","endpoint":"/dataflow/{agency}/{dataflow}/{version}/","name":"agency","location":"path","type":"string","description":"SDMX agency identifier.","supported":True},
        {"operation":"dataflow","method":"GET","endpoint":"/dataflow/{agency}/{dataflow}/{version}/","name":"dataflow","location":"path","type":"string","description":"Dataflow identifier.","supported":True},
        {"operation":"dataflow","method":"GET","endpoint":"/dataflow/{agency}/{dataflow}/{version}/","name":"version","location":"path","type":"string","description":"Dataflow version.","supported":True},
        {"operation":"data/dataflow","method":"GET","endpoint":"/data/{agency},{dataflow},{version}/{dataQuery}","name":"dataQuery","location":"path","type":"string","description":"Dimension-key query, including + and dot selectors.","supported":False},
        {"operation":"SDMX REST","method":"GET","endpoint":"/*","name":"format","location":"query","type":"string","description":"SDMX output format.","supported":True},
        {"operation":"SDMX REST","method":"GET","endpoint":"/*","name":"detail","location":"query","type":"string","description":"Level of structural detail.","supported":True},
        {"operation":"SDMX REST","method":"GET","endpoint":"/*","name":"references","location":"query","type":"string","description":"Related structural references.","supported":True},
        {"operation":"SDMX data","method":"GET","endpoint":"/data/*","name":"startPeriod","location":"query","type":"string","description":"Start period.","supported":False},
        {"operation":"SDMX data","method":"GET","endpoint":"/data/*","name":"endPeriod","location":"query","type":"string","description":"End period.","supported":False},
        {"operation":"SDMX data","method":"GET","endpoint":"/data/*","name":"firstNObservations","location":"query","type":"integer","description":"First N observations.","supported":False},
        {"operation":"SDMX data","method":"GET","endpoint":"/data/*","name":"lastNObservations","location":"query","type":"integer","description":"Last N observations.","supported":False},
        {"operation":"SDMX data","method":"GET","endpoint":"/data/*","name":"dimension_at_observation","location":"query","type":"string","description":"Observation dimension in SDMX-JSON output.","supported":False},
    ],
    "un-sdg": [
        {"operation":"Indicator/List","method":"GET","endpoint":"/v1/sdg/Indicator/List","name":"goal","location":"query","type":"array/string","description":"Goal filter where supported by the endpoint contract.","supported":False},
        {"operation":"Indicator/List","method":"GET","endpoint":"/v1/sdg/Indicator/List","name":"target","location":"query","type":"array/string","description":"Target filter where supported by the endpoint contract.","supported":False},
        {"operation":"Indicator/List","method":"GET","endpoint":"/v1/sdg/Indicator/List","name":"indicator","location":"query","type":"array/string","description":"Indicator filter where supported by the endpoint contract.","supported":False},
    ],
    "dhs": [
        {"operation":"indicators","method":"GET","endpoint":"/rest/dhs/indicators","name":"f","location":"query","type":"string","description":"Response format.","supported":True},
        {"operation":"indicators","method":"GET","endpoint":"/rest/dhs/indicators","name":"page","location":"query","type":"integer","description":"Page number.","supported":True},
        {"operation":"indicators","method":"GET","endpoint":"/rest/dhs/indicators","name":"perpage","location":"query","type":"integer","description":"Rows per page.","supported":True},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"countryIds","location":"query","type":"array/string","description":"Country identifiers.","supported":True},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"indicatorIds","location":"query","type":"array/string","description":"Indicator identifiers.","supported":True},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"surveyYears","location":"query","type":"array/integer","description":"Survey years.","supported":True},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"breakdown","location":"query","type":"string","description":"Requested breakdown.","supported":True},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"surveyIds","location":"query","type":"array/string","description":"Survey identifiers.","supported":False},
        {"operation":"data","method":"GET","endpoint":"/rest/dhs/data","name":"surveyType","location":"query","type":"array/string","description":"Survey type filter.","supported":False},
    ],
    "hdx-hapi": [
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"app_identifier","location":"query/header","type":"string","description":"HAPI application identifier.","supported":True,"sensitive":True},
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"output_format","location":"query","type":"string","description":"Output format.","supported":True},
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"limit","location":"query","type":"integer","description":"Maximum rows.","supported":True},
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"offset","location":"query","type":"integer","description":"Result offset.","supported":True},
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"location_code","location":"query","type":"string","description":"Location code.","supported":True},
        {"operation":"HAPI data","method":"GET","endpoint":"/api/v2/{endpoint}","name":"admin_level","location":"query","type":"integer","description":"Administrative level.","supported":True},
    ],
    "unhcr": [
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"limit","location":"query","type":"integer","description":"Maximum rows.","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"page","location":"query","type":"integer","description":"Page number.","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"yearFrom","location":"query","type":"integer","description":"Start year.","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"yearTo","location":"query","type":"integer","description":"End year.","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"coo","location":"query","type":"string","description":"Country of origin ISO code(s).","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"coa","location":"query","type":"string","description":"Country of asylum ISO code(s).","supported":True},
        {"operation":"population","method":"GET","endpoint":"/population/v1/population/","name":"cf_type","location":"query","type":"string","description":"Country filtering code type.","supported":True},
    ],
    "gdacs": [
        {"operation":"geteventlist/SEARCH","method":"GET","endpoint":"/gdacsapi/api/events/geteventlist/SEARCH","name":"fromDate","location":"query","type":"date","description":"Start date.","supported":True},
        {"operation":"geteventlist/SEARCH","method":"GET","endpoint":"/gdacsapi/api/events/geteventlist/SEARCH","name":"toDate","location":"query","type":"date","description":"End date.","supported":True},
        {"operation":"geteventlist/SEARCH","method":"GET","endpoint":"/gdacsapi/api/events/geteventlist/SEARCH","name":"eventlist","location":"query","type":"array/string","description":"Event type filter.","supported":True},
        {"operation":"geteventlist/SEARCH","method":"GET","endpoint":"/gdacsapi/api/events/geteventlist/SEARCH","name":"alertlevel","location":"query","type":"array/string","description":"Alert level filter.","supported":True},
    ],
}

SPEC_CANDIDATES: dict[str, list[str]] = {
    "un-sdg": [
        "https://unstats.un.org/SDGAPI/swagger/v1/swagger.json",
        "https://unstats.un.org/sdgapi/swagger/v1/swagger.json",
    ],
    "hdx-hapi": [
        "https://hapi.humdata.org/openapi.json",
        "https://hapi.humdata.org/api/openapi.json",
    ],
    "gdacs": [
        "https://www.gdacs.org/gdacsapi/swagger/v1/swagger.json",
        "https://www.gdacs.org/gdacsapi/swagger/swagger.json",
    ],
    "unhcr": [
        "https://api.unhcr.org/openapi.json",
        "https://api.unhcr.org/swagger.json",
    ],
    "dhs": [
        "https://api.dhsprogram.com/swagger/docs/v1",
        "https://api.dhsprogram.com/swagger/v1/swagger.json",
    ],
}


def ui_control(schema: dict[str, Any], readonly: bool = False, sensitive: bool = False) -> str:
    if sensitive:
        return "secret / variable d’environnement"
    if readonly:
        return "information en lecture seule"
    typ = schema.get("type")
    if schema.get("enum"):
        return "liste de sélection"
    if typ == "boolean":
        return "case à cocher"
    if typ in {"integer", "number"}:
        return "champ numérique"
    if typ == "array":
        return "liste / sélection multiple"
    if typ == "object":
        return "éditeur JSON structuré"
    return "champ texte / mots-clés"


def base_row(source_id: str, *, operation: str, method: str, endpoint: str, name: str,
             location: str, schema: dict[str, Any], required: bool = False,
             description: str = "", supported: bool = True, readonly: bool = False,
             sensitive: bool = False, origin: str = "HDP registry",
             documentation_url: str = "") -> dict[str, Any]:
    return {
        "Source": SOURCE_NAMES.get(source_id, source_id),
        "source_slug": source_id,
        "Opération": operation,
        "Méthode": method,
        "Endpoint": endpoint,
        "Paramètre": name,
        "Emplacement": location,
        "Type": schema.get("type", "string"),
        "Obligatoire": bool(required),
        "Contrôle recommandé": ui_control(schema, readonly=readonly, sensitive=sensitive),
        "Classe d’accès": "modifiable" if supported and not readonly and not sensitive else ("secret" if sensitive else "information"),
        "Description officielle / synthèse": description or schema.get("description", ""),
        "readonly": bool(readonly),
        "supported": bool(supported),
        "sensitive": bool(sensitive),
        "origin": origin,
        "documentation_url": documentation_url,
        "default": schema.get("default"),
        "enum": schema.get("enum"),
        "minimum": schema.get("minimum"),
        "maximum": schema.get("maximum"),
        "pattern": schema.get("pattern"),
    }


def registry_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in CONNECTORS:
        d = connector_definition(source_id)
        doc = (d.get("documentation_evidence") or [""])[0]
        for scope, schema, operation, method, location in [
            ("global", d["global_settings_schema"], "Configuration globale HDP", "CONFIG", "configuration globale"),
            ("project", d["project_schema"], "Recherche / paramètres projet HDP", "GET", "interface projet"),
        ]:
            required = set(schema.get("required", []))
            for name, spec in schema.get("properties", {}).items():
                readonly = bool(spec.get("readOnly"))
                sensitive = "secret" in name.casefold() or "token" in name.casefold() or "password" in name.casefold()
                rows.append(base_row(
                    source_id,
                    operation=operation,
                    method=method,
                    endpoint=d["base_url"],
                    name=name,
                    location=location,
                    schema=spec,
                    required=name in required,
                    supported=not readonly,
                    readonly=readonly,
                    sensitive=sensitive,
                    origin=f"source_registry:{scope}",
                    documentation_url=doc,
                ))
        for item in CURATED_NATIVE.get(source_id, []):
            rows.append(base_row(
                source_id,
                operation=item["operation"], method=item["method"], endpoint=item["endpoint"],
                name=item["name"], location=item["location"], schema={"type": item.get("type", "string")},
                required=bool(item.get("required", False)), description=item.get("description", ""),
                supported=bool(item.get("supported", False)), readonly=not bool(item.get("supported", False)),
                sensitive=bool(item.get("sensitive", False)), origin="provider documentation / curated V6 baseline",
                documentation_url=doc,
            ))
    return rows


def fetch_json(url: str) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": "HDP/6.0.0 inventory-audit"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                return None
            data = json.load(response)
            return data if isinstance(data, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def resolve_ref(spec: dict[str, Any], value: Any) -> Any:
    if not isinstance(value, dict) or "$ref" not in value:
        return value
    ref = value["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return value
    node: Any = spec
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return value
        node = node.get(part.replace("~1", "/").replace("~0", "~"))
    return node if node is not None else value


def schema_from_parameter(spec: dict[str, Any], parameter: dict[str, Any]) -> dict[str, Any]:
    parameter = resolve_ref(spec, parameter)
    schema = resolve_ref(spec, parameter.get("schema", {})) if isinstance(parameter, dict) else {}
    if not isinstance(schema, dict):
        schema = {}
    if "type" not in schema and isinstance(parameter, dict) and parameter.get("type"):
        schema["type"] = parameter.get("type")
    if isinstance(parameter, dict) and parameter.get("enum") and "enum" not in schema:
        schema["enum"] = parameter.get("enum")
    return schema or {"type": "string"}


def openapi_rows(source_id: str, spec: dict[str, Any], spec_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return rows
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        common = path_item.get("parameters", []) if isinstance(path_item.get("parameters", []), list) else []
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"} or not isinstance(operation, dict):
                continue
            op_name = operation.get("operationId") or operation.get("summary") or f"{method.upper()} {path}"
            parameters = list(common)
            if isinstance(operation.get("parameters", []), list):
                parameters += operation["parameters"]
            for raw in parameters:
                p = resolve_ref(spec, raw)
                if not isinstance(p, dict) or not p.get("name"):
                    continue
                schema = schema_from_parameter(spec, p)
                name = str(p["name"])
                sensitive = name.casefold() in {"authorization", "api_key", "apikey", "token", "password"}
                rows.append(base_row(
                    source_id, operation=str(op_name), method=method.upper(), endpoint=str(path),
                    name=name, location=str(p.get("in", "query")), schema=schema,
                    required=bool(p.get("required", False)), description=str(p.get("description", "")),
                    supported=False, readonly=True, sensitive=sensitive,
                    origin="provider OpenAPI/Swagger", documentation_url=spec_url,
                ))
            rb = resolve_ref(spec, operation.get("requestBody"))
            if isinstance(rb, dict):
                content = rb.get("content", {})
                if isinstance(content, dict):
                    for media in content.values():
                        if not isinstance(media, dict):
                            continue
                        body_schema = resolve_ref(spec, media.get("schema", {}))
                        if isinstance(body_schema, dict):
                            props = body_schema.get("properties", {})
                            required_body = set(body_schema.get("required", []))
                            if isinstance(props, dict):
                                for name, raw_schema in props.items():
                                    body_prop = resolve_ref(spec, raw_schema)
                                    if not isinstance(body_prop, dict):
                                        body_prop = {"type": "string"}
                                    rows.append(base_row(
                                        source_id, operation=str(op_name), method=method.upper(), endpoint=str(path),
                                        name=str(name), location="body", schema=body_prop,
                                        required=name in required_body, description=str(body_prop.get("description", "")),
                                        supported=False, readonly=True, origin="provider OpenAPI requestBody",
                                        documentation_url=spec_url,
                                    ))
    return rows


def live_spec_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    report: dict[str, Any] = {}
    offline = os.getenv("HDP_INVENTORY_OFFLINE", "0") == "1"
    for source_id, candidates in SPEC_CANDIDATES.items():
        report[source_id] = {"status": "not_found", "url": None, "rows": 0}
        if offline:
            report[source_id]["status"] = "offline"
            continue
        for url in candidates:
            spec = fetch_json(url)
            if not spec:
                continue
            extracted = openapi_rows(source_id, spec, url)
            if extracted:
                rows.extend(extracted)
                report[source_id] = {"status": "loaded", "url": url, "rows": len(extracted)}
                break
    return rows, report


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["source_slug"], row["Opération"], row["Méthode"], row["Endpoint"],
            row["Emplacement"], row["Paramètre"],
        )
        current = chosen.get(key)
        if current is None:
            chosen[key] = row
            continue
        # Prefer an editable/supported mapping over a merely informational duplicate.
        if row.get("supported") and not current.get("supported"):
            chosen[key] = row
    return sorted(chosen.values(), key=lambda r: (r["Source"], r["Opération"], r["Endpoint"], r["Méthode"], r["Paramètre"]))


def write_parts(rows: list[dict[str, Any]], part_size: int = 400) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("part*.jsonl"):
        old.unlink()
    for i in range(0, len(rows), part_size):
        path = OUT_DIR / f"part{i // part_size:03d}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows[i:i + part_size]:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_docs(rows: list[dict[str, Any]], spec_report: dict[str, Any]) -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["source_slug"]].append(row)
    with (DOC_DIR / "API_INVENTORY.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    md = [
        "# HDP V6.0.0 — Inventaire des paramètres API",
        "",
        "Cet inventaire est généré sans flux compressé opaque. Il combine les schémas de configuration réellement utilisés par HDP, les paramètres natifs documentés des opérations de recherche/acquisition et, lorsqu'elle est disponible au moment de la construction, la spécification OpenAPI/Swagger du fournisseur.",
        "",
        "Les paramètres `supported=false` restent visibles dans l'interface comme informations classées. Ils ne sont jamais présentés comme fonctionnels tant qu'un adaptateur et ses tests ne les prennent pas en charge.",
        "",
        f"**Total : {len(rows)} entrées · {len(by_source)} sources.**",
        "",
        "## État des spécifications machine",
        "",
        "| Source | État | URL | Paramètres extraits |",
        "|---|---|---|---:|",
    ]
    for source_id in CONNECTORS:
        info = spec_report.get(source_id, {"status":"n/a","url":None,"rows":0})
        md.append(f"| {SOURCE_NAMES.get(source_id, source_id)} | {info.get('status','n/a')} | {info.get('url') or ''} | {info.get('rows',0)} |")
    for source_id in CONNECTORS:
        items = by_source[source_id]
        md += ["", f"## {SOURCE_NAMES.get(source_id, source_id)}", "",
               f"{len(items)} entrées cataloguées, dont {sum(bool(r.get('supported')) for r in items)} directement prises en charge par HDP.", "",
               "| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |",
               "|---|---|---|---|---|---|---|---|---|"]
        for r in items:
            esc = lambda x: str(x if x is not None else "").replace("|", "\\|").replace("\n", " ")
            md.append("| " + " | ".join(esc(x) for x in [r["Opération"],r["Méthode"],r["Endpoint"],r["Paramètre"],r["Emplacement"],r["Type"],r["Contrôle recommandé"],"oui" if r.get("supported") else "information",r["origin"]]) + " |")
    (DOC_DIR / "API_INVENTORY.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (DOC_DIR / "API_INVENTORY_SPEC_REPORT.json").write_text(json.dumps(spec_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate(rows: list[dict[str, Any]]) -> None:
    sources = {r["source_slug"] for r in rows}
    missing = set(CONNECTORS) - sources
    if missing:
        raise SystemExit(f"Sources absentes de l'inventaire: {sorted(missing)}")
    keys = {(r["source_slug"], r["Opération"], r["Méthode"], r["Endpoint"], r["Emplacement"], r["Paramètre"]) for r in rows}
    if len(keys) != len(rows):
        raise SystemExit("Doublons non résolus dans l'inventaire")
    # Every user-facing registry property must appear in the inventory.
    for source_id in CONNECTORS:
        d = connector_definition(source_id)
        for scope_name, schema in (("global", d["global_settings_schema"]), ("project", d["project_schema"])):
            for name in schema.get("properties", {}):
                if not any(r["source_slug"] == source_id and r["Paramètre"] == name for r in rows):
                    raise SystemExit(f"{source_id}:{scope_name}:{name} absent de l'inventaire")


def main() -> None:
    rows = registry_rows()
    live_rows, spec_report = live_spec_rows()
    rows = deduplicate(rows + live_rows)
    validate(rows)
    write_parts(rows)
    write_docs(rows, spec_report)
    print(json.dumps({
        "version": VERSION,
        "sources": len({r['source_slug'] for r in rows}),
        "entries": len(rows),
        "operations": len({(r['source_slug'],r['Opération'],r['Méthode'],r['Endpoint']) for r in rows}),
        "supported": sum(bool(r.get('supported')) for r in rows),
        "informational": sum(not bool(r.get('supported')) for r in rows),
        "spec_report": spec_report,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
