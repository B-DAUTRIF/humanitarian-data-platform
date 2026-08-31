from __future__ import annotations

"""Provider-native execution helpers for the V7 semantic router."""

import asyncio
import json
from typing import Any, Iterable

import httpx


def _timeout(settings: dict[str, Any]) -> httpx.Timeout:
    return httpx.Timeout(float(settings["timeout_seconds"]), connect=float(settings["connect_timeout_seconds"]))


def _headers(settings: dict[str, Any]) -> dict[str, str]:
    return {"User-Agent": str(settings["user_agent"]), "Accept-Language": str(settings["accept_language"]), "Accept": "application/json, application/geo+json;q=0.9"}


async def _get_json(url: str, params: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, str]:
    """Fetch JSON with retries while enforcing the connector response-size contract."""
    retries = int(settings["retry_count"])
    backoff = int(settings["backoff_seconds"])
    max_bytes = int(settings.get("max_response_bytes") or 25_000_000)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=_timeout(settings), follow_redirects=True) as client:
                async with client.stream("GET", url, params=params, headers=_headers(settings)) as response:
                    response.raise_for_status()
                    declared = response.headers.get("content-length")
                    if declared and declared.isdigit() and int(declared) > max_bytes:
                        raise RuntimeError(f"Réponse fournisseur trop volumineuse: {declared} octets > {max_bytes}")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise RuntimeError(f"Réponse fournisseur trop volumineuse: > {max_bytes} octets")
                    request_url = str(response.request.url)
            return json.loads(body), request_url
        except httpx.HTTPError as exc:
            last_error = exc
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = status is None or status == 429 or status >= 500
            if attempt >= retries or not retryable:
                raise
            await asyncio.sleep(backoff * (2**attempt))
    raise RuntimeError("Échec HTTP sans réponse") from last_error


async def execute_reliefweb_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    """Execute semantic ReliefWeb searches through the same ProviderService as the native API.

    The semantic adapter currently targets reports because SearchIntent represents
    document discovery. Native ReliefWeb UI/API callers can select all documented
    content types. Project-specific configuration is accepted when injected in the
    route; until the semantic API passes it, global/default resolution remains active.
    """
    from .providers.reliefweb.service import ReliefWebService

    parameters, native = route["parameters"], route.get("native_parameters", {})
    filters: list[dict[str, Any]] = []
    if native.get("filter[field]"):
        filters.append({"field": native["filter[field]"], "value": native["filter[value]"]})
    if native.get("filter_date_field"):
        value: dict[str, str] = {}
        if native.get("filter_date_from"):
            value["from"] = f"{native['filter_date_from']}T00:00:00+00:00"
        if native.get("filter_date_to"):
            value["to"] = f"{native['filter_date_to']}T23:59:59+00:00"
        filters.append({"field": native["filter_date_field"], "value": value})
    rw_parameters: dict[str, Any] = {
        "query": parameters.get("query") or "",
        "limit": int(parameters.get("result_limit") or 25),
        "offset": 0,
        "profile": "full",
        "preset": "latest",
        "sort": ["date.created:desc"],
    }
    if len(filters) == 1:
        rw_parameters["filter"] = filters[0]
    elif filters:
        rw_parameters["filter"] = {"operator": "AND", "conditions": filters}
    service = ReliefWebService(settings)
    project_config = route.get("provider_configuration") if isinstance(route.get("provider_configuration"), dict) else {}
    return await service.execute("reports", rw_parameters, global_settings=settings, project_settings=project_config)


async def execute_hapi_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    from .main import search_remote_source
    parameters = dict(route["parameters"])
    parameters.update({key: value for key, value in route.get("native_parameters", {}).items() if key == "location_code"})
    payload, items = await search_remote_source("hdx-hapi", parameters, settings)
    from .source_registry import request_preview
    preview = request_preview("hdx-hapi", parameters)
    return payload, items, {"method": preview["method"], "url": preview["url"], "query_parameters": preview["query_parameters"]}


async def execute_unhcr_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    from .main import search_remote_source
    native = route.get("native_parameters", {})
    iso3 = str(native.get("iso3") or "")
    base = dict(route["parameters"])
    payloads: dict[str, Any] = {}
    items: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    roles = native.get("country_roles") or ["origin", "asylum"]
    for role in roles:
        parameters = dict(base)
        if role == "origin":
            parameters["country_of_origin"] = iso3
            parameters["country_of_asylum"] = ""
        else:
            parameters["country_of_origin"] = ""
            parameters["country_of_asylum"] = iso3
        payload, role_items = await search_remote_source("unhcr", parameters, settings)
        payloads[role] = payload
        from .source_registry import request_preview
        preview = request_preview("unhcr", parameters)
        requests.append({"role": role, "method": preview["method"], "url": preview["url"], "query_parameters": preview["query_parameters"]})
        for item in role_items:
            tagged = dict(item)
            tagged["_hdp_semantics"] = {"geography_role": role, "iso3": iso3}
            tagged["id"] = f"{role}:{tagged.get('id')}"
            items.append(tagged)
    return payloads, items[: int(base.get("result_limit") or 25)], {"requests": requests}


def _tokens(value: str) -> list[str]:
    return [token for token in value.casefold().replace("_", " ").replace("-", " ").split() if token]


def _matches(value: str, query: str) -> bool:
    if not query:
        return True
    haystack = value.casefold()
    return all(token in haystack for token in _tokens(query))


async def execute_world_bank_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    """Delegate all World Bank semantic execution to the reference provider service."""
    from .providers.world_bank_health.service import WorldBankHealthService

    service = WorldBankHealthService(settings)
    project_config = route.get("provider_configuration") if isinstance(route.get("provider_configuration"), dict) else {}
    return await service.execute_semantic(route, global_settings=settings, project_settings=project_config)


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _series_identity(row: dict[str, Any]) -> tuple[str, str]:
    code_value = row.get("seriesCode") or row.get("series_code") or row.get("code")
    label_value = row.get("seriesDescription") or row.get("description") or row.get("name") or row.get("title")
    code = str(code_value) if isinstance(code_value, (str, int)) else ""
    label = str(label_value) if isinstance(label_value, (str, int)) else ""
    return code, label


async def execute_un_sdg_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    native, parameters = route.get("native_parameters", {}), route["parameters"]
    area_code = native.get("areaCode")
    query = str(native.get("series_search") or parameters.get("query") or "")
    if area_code is not None:
        catalog_url = f"https://unstats.un.org/SDGAPI/v1/sdg/GeoArea/{area_code}/List"
        catalog, catalog_request = await _get_json(catalog_url, {}, settings)
    else:
        catalog_url = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
        catalog, catalog_request = await _get_json(catalog_url, {}, settings)
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in _walk_dicts(catalog):
        code, label = _series_identity(row)
        if code and code not in seen and _matches(f"{code} {label}", query):
            seen.add(code)
            candidates.append((code, label))
    candidates = candidates[:5]
    if not query:
        items = [{"id": code, "title": label or code, "description": "Series available for selected SDG geography", "date": None, "url": catalog_request, "source": "UN Global SDG Indicators Database", "organization": "UNSD", "geographic_scope": str(area_code or ""), "series_code": code, "resources": []} for code, label in candidates[: int(parameters.get("result_limit") or 25)]]
        return {"catalog": catalog}, items, {"catalog_url": catalog_request, "observation_requests": []}
    observations: list[Any] = []
    items: list[dict[str, Any]] = []
    requests: list[str] = []
    for code, label in candidates:
        args: dict[str, Any] = {"seriesCode": code, "page": 1, "pageSize": min(1000, int(parameters.get("result_limit") or 25) * 4)}
        if area_code is not None:
            args["areaCode"] = area_code
        if native.get("timePeriodStart") is not None:
            args["timePeriodStart"] = native["timePeriodStart"]
        if native.get("timePeriodEnd") is not None:
            args["timePeriodEnd"] = native["timePeriodEnd"]
        payload, request_url = await _get_json("https://unstats.un.org/SDGAPI/v1/sdg/Series/Data", args, settings)
        observations.append(payload)
        requests.append(request_url)
        for row in _walk_dicts(payload):
            row_series = str(row.get("seriesCode") or row.get("series_code") or "")
            if row_series and row_series != code:
                continue
            period = row.get("timePeriod") or row.get("time_period") or row.get("year")
            value = row.get("value") if "value" in row else row.get("Value")
            geo_name = row.get("geoAreaName") or row.get("geo_area_name") or row.get("geoAreaCode") or area_code
            if period is None and value is None:
                continue
            items.append({"id": f"{code}:{row.get('geoAreaCode') or area_code}:{period}:{len(items)}", "title": f"{label or code} — {geo_name} — {period}", "description": f"value={value}; units={row.get('units') or row.get('unit') or ''}; nature={row.get('nature') or row.get('natureCode') or ''}", "date": f"{int(float(period)):04d}-12-31" if str(period or "").replace(".0", "").isdigit() else None, "url": request_url, "source": "UN Global SDG Indicators Database", "organization": "UNSD", "geographic_scope": str(geo_name or ""), "series_code": code, "value": value, "unit": row.get("units") or row.get("unit"), "resources": []})
            if len(items) >= int(parameters.get("result_limit") or 25):
                break
        if len(items) >= int(parameters.get("result_limit") or 25):
            break
    return {"catalog": catalog, "observations": observations}, items, {"catalog_url": catalog_request, "observation_requests": requests}


async def execute_native_route(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]] | None:
    source = route["source"]
    if source == "reliefweb":
        return await execute_reliefweb_native(route, settings)
    if source == "hdx-hapi":
        return await execute_hapi_native(route, settings)
    if source == "unhcr" and route.get("native_parameters", {}).get("iso3"):
        return await execute_unhcr_native(route, settings)
    if source == "world-bank-health":
        return await execute_world_bank_native(route, settings)
    if source == "un-sdg":
        return await execute_un_sdg_native(route, settings)
    return None
