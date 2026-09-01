from __future__ import annotations

from typing import Any

import httpx

from ...reliefweb_v2 import request_spec
from ..base.contracts import resolve_provider_configuration
from ..base.errors import ProviderConfigurationError, ProviderRateLimitedError
from .descriptor import RELIEFWEB_DESCRIPTOR


def normalize_items(payload: Any, content_type: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        title = fields.get("title") or fields.get("name") or fields.get("shortname") or f"ReliefWeb {content_type} {row.get('id')}"
        date_obj = fields.get("date") if isinstance(fields.get("date"), dict) else {}
        country = fields.get("primary_country") or fields.get("country")
        if isinstance(country, list) and country:
            country = country[0]
        geo = country.get("name") if isinstance(country, dict) else None
        normalized.append({
            "id": str(row.get("id")),
            "title": str(title),
            "description": fields.get("body") or fields.get("description") or fields.get("headline", {}).get("summary") if isinstance(fields.get("headline"), dict) else fields.get("description"),
            "date": date_obj.get("created") or date_obj.get("changed") if isinstance(date_obj, dict) else None,
            "url": fields.get("url") or row.get("href"),
            "source": "ReliefWeb",
            "organization": "OCHA ReliefWeb",
            "geographic_scope": geo,
            "content_type": content_type,
            "reliefweb_id": row.get("id"),
            "reliefweb_href": row.get("href"),
            "score": row.get("score"),
            "_native": row,
            "resources": [],
        })
    return normalized


class ReliefWebService:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings

    def effective_configuration(self, *, global_settings: dict[str, Any] | None = None, project_settings: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        return resolve_provider_configuration(RELIEFWEB_DESCRIPTOR, global_settings=global_settings, project_settings=project_settings)

    async def execute(self, content_type: str, parameters: dict[str, Any], *, global_settings: dict[str, Any] | None = None, project_settings: dict[str, Any] | None = None, item_id: str | int | None = None) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        spec = request_spec(content_type, parameters, project_parameters=project_settings, global_settings=global_settings, item_id=item_id)
        appname = str(spec["appname"] or "").strip()
        if not appname:
            raise ProviderConfigurationError(
                "ReliefWeb exige un APPNAME pré-approuvé depuis le 1er novembre 2025; configurez RELIEFWEB_APPNAME ou le paramètre projet appname"
            )
        timeout = httpx.Timeout(float(self.settings.get("timeout_seconds", 20)), connect=float(self.settings.get("connect_timeout_seconds", 5)))
        headers = {"User-Agent": str(self.settings.get("user_agent", "HDP/7")), "Accept-Language": str(self.settings.get("accept_language", "en")), "Accept": "application/json"}
        method = spec["method"]
        payload = spec["payload"]
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            if method == "POST":
                response = await client.post(spec["url"], params={"appname": appname}, json=payload, headers=headers)
            else:
                query: dict[str, Any] = {"appname": appname}
                if "query" in payload:
                    q = payload["query"]
                    query["query[value]"] = q.get("value")
                    if q.get("operator"):
                        query["query[operator]"] = q["operator"]
                    for i, value in enumerate(q.get("fields") or []):
                        query[f"query[fields][{i}]"] = value
                if "filter" in payload:
                    f = payload["filter"]
                    if f.get("field"):
                        query["filter[field]"] = f["field"]
                        value = f.get("value")
                        if isinstance(value, dict):
                            for key, val in value.items(): query[f"filter[value][{key}]"] = val
                        elif isinstance(value, list):
                            for i, val in enumerate(value): query[f"filter[value][{i}]"] = val
                        elif value is not None: query["filter[value]"] = value
                        if f.get("operator"): query["filter[operator]"] = f["operator"]
                        if f.get("negate") is not None: query["filter[negate]"] = int(bool(f["negate"]))
                for key in ("limit", "offset", "profile", "preset", "slim", "verbose"):
                    if key in payload: query[key] = payload[key]
                for i, value in enumerate(payload.get("sort") or []): query[f"sort[{i}]"] = value
                fields = payload.get("fields") or {}
                for part in ("include", "exclude"):
                    for i, value in enumerate(fields.get(part) or []): query[f"fields[{part}][{i}]"] = value
                response = await client.get(spec["url"], params=query, headers=headers)
            if response.status_code == 403:
                raise ProviderConfigurationError(
                    f"ReliefWeb a refusé l'APPNAME configuré (origine={spec['appname_origin']}) avec HTTP 403; utilisez un APPNAME pré-approuvé"
                )
            if response.status_code == 429:
                raise ProviderRateLimitedError("ReliefWeb rate limit reached")
            response.raise_for_status()
            raw = response.json()
        native_request = {"method": method, "url": spec["url"], "appname": appname, "appname_origin": spec["appname_origin"], "payload": payload, "http_status": response.status_code}
        return raw, normalize_items(raw, content_type), native_request
