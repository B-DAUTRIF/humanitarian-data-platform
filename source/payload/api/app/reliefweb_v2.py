from __future__ import annotations

"""ReliefWeb V2 native contract for HDP.

Official contract: https://apidoc.reliefweb.int/
This module deliberately keeps ReliefWeb-native concepts instead of forcing them
through the generic provider schema.
"""

from dataclasses import dataclass
from typing import Any, Literal

CONTENT_TYPES = ("reports", "disasters", "countries", "jobs", "training", "sources", "blog", "book", "references")
PROFILES = ("minimal", "list", "full")
PRESETS = ("minimal", "latest", "analysis")
OPERATORS = ("AND", "OR")
FACET_SCOPES = ("default", "query", "global")
FACET_INTERVALS = ("year", "month", "week", "day")
DEFAULT_APPNAME = "HDP_plateforme"
BASE_URL = "https://api.reliefweb.int/v2"

class ReliefWebValidationError(ValueError):
    pass

@dataclass(frozen=True)
class EffectiveAppName:
    value: str
    origin: Literal["project", "global", "default"]

def resolve_appname(project_parameters: dict[str, Any] | None, global_settings: dict[str, Any] | None) -> EffectiveAppName:
    project = str((project_parameters or {}).get("appname") or "").strip()
    if project:
        return EffectiveAppName(project, "project")
    global_value = str((global_settings or {}).get("appname") or "").strip()
    if global_value:
        return EffectiveAppName(global_value, "global")
    return EffectiveAppName(DEFAULT_APPNAME, "default")

def _operator(value: Any, *, default: str = "AND") -> str:
    op = str(value or default).upper()
    if op not in OPERATORS:
        raise ReliefWebValidationError(f"Invalid ReliefWeb operator: {op}")
    return op

def validate_filter(node: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    if depth > 20:
        raise ReliefWebValidationError("ReliefWeb filter nesting exceeds HDP safety limit (20)")
    if not isinstance(node, dict):
        raise ReliefWebValidationError("ReliefWeb filter must be an object")
    out: dict[str, Any] = {}
    if "negate" in node:
        out["negate"] = bool(node["negate"])
    conditions = node.get("conditions")
    field = str(node.get("field") or "").strip()
    if conditions is not None:
        if field:
            raise ReliefWebValidationError("ReliefWeb filter cannot contain both field and conditions")
        if not isinstance(conditions, list) or not conditions:
            raise ReliefWebValidationError("ReliefWeb conditions must be a non-empty array")
        out["operator"] = _operator(node.get("operator"))
        out["conditions"] = [validate_filter(item, depth + 1) for item in conditions]
        return out
    if not field:
        raise ReliefWebValidationError("ReliefWeb simple filter requires field")
    out["field"] = field
    if "value" in node:
        out["value"] = node["value"]
    if "operator" in node:
        out["operator"] = _operator(node["operator"])
    return out

def validate_facets(facets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for facet in facets:
        field = str(facet.get("field") or "").strip()
        if not field:
            raise ReliefWebValidationError("ReliefWeb facet requires field")
        item: dict[str, Any] = {"field": field}
        for key in ("name", "sort"):
            if facet.get(key) not in (None, ""):
                item[key] = str(facet[key])
        if facet.get("limit") is not None:
            limit = int(facet["limit"])
            if limit < 0:
                raise ReliefWebValidationError("Facet limit must be >= 0")
            item["limit"] = limit
        if facet.get("scope") is not None:
            scope = str(facet["scope"])
            if scope not in FACET_SCOPES:
                raise ReliefWebValidationError(f"Invalid facet scope: {scope}")
            item["scope"] = scope
        if facet.get("interval") is not None:
            interval = str(facet["interval"])
            if interval not in FACET_INTERVALS:
                raise ReliefWebValidationError(f"Invalid facet interval: {interval}")
            item["interval"] = interval
        if facet.get("filter") is not None:
            item["filter"] = validate_filter(facet["filter"])
        output.append(item)
    return output

def build_payload(parameters: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    query_value = str(parameters.get("query") or "").strip()
    query_fields = parameters.get("query_fields") or []
    if query_value:
        query: dict[str, Any] = {"value": query_value}
        if query_fields:
            query["fields"] = [str(v) for v in query_fields]
        if parameters.get("query_operator"):
            query["operator"] = _operator(parameters["query_operator"], default="OR")
        payload["query"] = query
    if parameters.get("filter") is not None:
        payload["filter"] = validate_filter(parameters["filter"])
    if parameters.get("facets"):
        payload["facets"] = validate_facets(parameters["facets"])
    limit = int(parameters.get("limit", parameters.get("result_limit", 10)))
    if not 0 <= limit <= 1000:
        raise ReliefWebValidationError("ReliefWeb limit must be between 0 and 1000")
    payload["limit"] = limit
    offset = int(parameters.get("offset", 0))
    if offset < 0:
        raise ReliefWebValidationError("ReliefWeb offset must be >= 0")
    payload["offset"] = offset
    if parameters.get("sort"):
        payload["sort"] = [str(v) for v in parameters["sort"]]
    profile = parameters.get("profile")
    if profile:
        if profile not in PROFILES:
            raise ReliefWebValidationError(f"Invalid ReliefWeb profile: {profile}")
        payload["profile"] = profile
    preset = parameters.get("preset")
    if preset:
        if preset not in PRESETS:
            raise ReliefWebValidationError(f"Invalid ReliefWeb preset: {preset}")
        payload["preset"] = preset
    include, exclude = parameters.get("fields_include") or [], parameters.get("fields_exclude") or []
    if include or exclude:
        payload["fields"] = {}
        if include:
            payload["fields"]["include"] = [str(v) for v in include]
        if exclude:
            payload["fields"]["exclude"] = [str(v) for v in exclude]
    if parameters.get("slim"):
        payload["slim"] = 1
    if parameters.get("verbose"):
        payload["verbose"] = 1
    return payload

def request_spec(content_type: str, parameters: dict[str, Any], *, project_parameters: dict[str, Any] | None = None, global_settings: dict[str, Any] | None = None, item_id: str | int | None = None) -> dict[str, Any]:
    if content_type not in CONTENT_TYPES:
        raise ReliefWebValidationError(f"Unknown ReliefWeb content type: {content_type}")
    appname = resolve_appname(project_parameters, global_settings)
    url = f"{BASE_URL}/{content_type}" + (f"/{item_id}" if item_id is not None else "")
    if item_id is not None:
        allowed = {k: v for k, v in parameters.items() if k in {"profile", "fields_include", "fields_exclude"}}
        payload = build_payload({**allowed, "limit": 10, "offset": 0})
        payload.pop("limit", None); payload.pop("offset", None)
        return {"method": "GET", "url": url, "appname": appname.value, "appname_origin": appname.origin, "payload": payload}
    payload = build_payload(parameters)
    complex_request = bool(payload.get("facets") or (isinstance(payload.get("filter"), dict) and payload["filter"].get("conditions")))
    return {"method": "POST" if complex_request else "GET", "url": url, "appname": appname.value, "appname_origin": appname.origin, "payload": payload}
