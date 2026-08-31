from __future__ import annotations

"""Non-destructive live parameter probes for the V7 systematic connector audit.

This script never interprets an empty payload as proof of absence. It only records
provider acceptance/rejection of documented request shapes and leaves missing
credentials or transient provider timeouts as BLOCKED.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

OUT = Path("qualification-state/parameter-audit")
OUT.mkdir(parents=True, exist_ok=True)
TIMEOUT = httpx.Timeout(40.0, connect=10.0)
UA = "HDP-V7-parameter-audit/1.1"


def record(provider: str, parameter: str, url: str, status: str, http_status: int | None = None,
           observed: Any = None, error: str | None = None) -> dict[str, Any]:
    return {
        "provider": provider,
        "parameter": parameter,
        "url": url,
        "status": status,
        "http_status": http_status,
        "observed": observed,
        "error": error,
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
    }


async def request_json(client: httpx.AsyncClient, provider: str, parameter: str, method: str, url: str,
                       *, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        response = await client.request(method, url, params=params, json=body)
        status = "PASS" if 200 <= response.status_code < 300 else "FAIL"
        observed: Any = None
        try:
            payload = response.json()
            if isinstance(payload, dict):
                observed = {
                    "keys": list(payload)[:20],
                    "data_count": len(payload.get("data") or []) if isinstance(payload.get("data"), list) else None,
                    "success": payload.get("success"),
                }
            elif isinstance(payload, list):
                observed = {"list_length": len(payload), "shape": [type(x).__name__ for x in payload[:2]]}
        except ValueError:
            observed = {"content_type": response.headers.get("content-type"), "length": len(response.content)}
        return record(provider, parameter, str(response.request.url), status, response.status_code, observed,
                      None if status == "PASS" else response.text[:500])
    except httpx.TimeoutException as exc:
        return record(provider, parameter, url, "BLOCKED", error=f"TIMEOUT: {type(exc).__name__}: {exc}")
    except httpx.HTTPError as exc:
        return record(provider, parameter, url, "BLOCKED", error=f"TRANSPORT: {type(exc).__name__}: {exc}")


async def reliefweb(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    appname = (os.getenv("RELIEFWEB_APPNAME") or "HDP_plateforme").strip()
    base = "https://api.reliefweb.int/v2/reports"
    q = {"appname": appname}
    probes: list[dict[str, Any]] = []
    get_cases = [
        ("appname", {**q, "limit": 1}),
        ("query.value", {**q, "query[value]": "cholera", "limit": 1}),
        ("query.fields", {**q, "query[value]": "cholera", "query[fields][0]": "title", "limit": 1}),
        ("query.operator", {**q, "query[value]": "cholera health", "query[operator]": "AND", "limit": 1}),
        ("filter.field/value", {**q, "filter[field]": "country", "filter[value]": "Rwanda", "limit": 1}),
        ("filter.negate", {**q, "filter[field]": "country", "filter[value]": "Rwanda", "filter[negate]": 1, "limit": 1}),
        ("limit", {**q, "limit": 2}),
        ("offset", {**q, "limit": 1, "offset": 1}),
        ("sort", {**q, "limit": 1, "sort[0]": "date.created:desc"}),
        ("profile", {**q, "limit": 1, "profile": "list"}),
        ("preset", {**q, "limit": 1, "preset": "latest"}),
        ("fields.include", {**q, "limit": 1, "fields[include][0]": "country.iso3"}),
        ("fields.exclude", {**q, "limit": 1, "profile": "full", "fields[exclude][0]": "body-html"}),
        ("slim", {**q, "limit": 1, "slim": 1}),
        ("verbose", {**q, "query[value]": "cholera", "limit": 1, "verbose": 1}),
    ]
    for name, params in get_cases:
        probes.append(await request_json(client, "reliefweb", name, "GET", base, params=params))
    post_cases = [
        ("filter.conditions/operator", {"filter": {"operator": "AND", "conditions": [{"field": "country", "value": "Rwanda"}, {"field": "theme", "value": "Health"}]}, "limit": 1}),
        ("facets.field/name/limit/sort/scope", {"facets": [{"field": "country", "name": "countries", "limit": 2, "sort": "count:desc", "scope": "global"}], "limit": 0}),
        ("facets.interval", {"facets": [{"field": "date.created", "interval": "year"}], "limit": 0}),
        ("facets.filter", {"facets": [{"field": "source", "filter": {"field": "country", "value": "Rwanda"}, "limit": 2}], "limit": 0}),
    ]
    for name, body in post_cases:
        probes.append(await request_json(client, "reliefweb", name, "POST", base, params={"appname": appname}, body=body))
    for content in ("reports", "disasters", "countries", "jobs", "training", "sources", "blog", "book", "references"):
        probes.append(await request_json(client, "reliefweb", f"content_type:{content}", "GET", f"https://api.reliefweb.int/v2/{content}", params={"appname": appname, "limit": 1}))
    return probes


async def world_bank(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    base = "https://api.worldbank.org/v2/country/RWA/indicator/SP.POP.TOTL"
    probes: list[dict[str, Any]] = []
    cases = [
        ("source", {"format": "json", "source": 2, "per_page": 1}),
        ("country", {"format": "json", "source": 2, "per_page": 1}),
        ("indicator", {"format": "json", "source": 2, "per_page": 1}),
        ("date", {"format": "json", "source": 2, "date": "2020:2021", "per_page": 2}),
        ("page", {"format": "json", "source": 2, "page": 1, "per_page": 1}),
        ("per_page", {"format": "json", "source": 2, "per_page": 2}),
        ("mrv", {"format": "json", "source": 2, "mrv": 2}),
        ("mrnev", {"format": "json", "source": 2, "mrnev": 2}),
        ("gapfill", {"format": "json", "source": 2, "mrv": 2, "gapfill": "Y"}),
        ("frequency", {"format": "json", "source": 2, "mrv": 2, "frequency": "Y"}),
        ("footnote", {"format": "json", "source": 2, "footnote": "y", "per_page": 1}),
        ("ctrycode", {"format": "json", "source": 2, "ctrycode": "y", "per_page": 1}),
        ("scale", {"format": "json", "source": 2, "scale": "y", "per_page": 1}),
        ("format", {"format": "json", "source": 2, "per_page": 1}),
    ]
    for name, params in cases:
        probes.append(await request_json(client, "world-bank-health", name, "GET", base, params=params))
    probes.append(await request_json(client, "world-bank-health", "language", "GET", "https://api.worldbank.org/v2/fr/country/RWA/indicator/SP.POP.TOTL", params={"format": "json", "source": 2, "per_page": 1}))
    probes.append(await request_json(client, "world-bank-health", "multi_country", "GET", "https://api.worldbank.org/v2/country/RWA;UGA/indicator/SP.POP.TOTL", params={"format": "json", "source": 2, "date": "2020", "per_page": 5}))
    probes.append(await request_json(client, "world-bank-health", "multi_indicator", "GET", "https://api.worldbank.org/v2/country/RWA/indicator/SP.POP.TOTL;SP.DYN.LE00.IN", params={"format": "json", "source": 2, "date": "2020", "per_page": 5}))
    for name, url in [
        ("catalogue_indicators", "https://api.worldbank.org/v2/source/2/indicator"),
        ("catalogue_countries", "https://api.worldbank.org/v2/country"),
        ("catalogue_topics", "https://api.worldbank.org/v2/topic"),
        ("catalogue_sources", "https://api.worldbank.org/v2/source"),
        ("indicator_metadata", "https://api.worldbank.org/v2/indicator/SP.POP.TOTL"),
        ("metadata_search", "https://api.worldbank.org/v2/sources/2/search/health"),
    ]:
        probes.append(await request_json(client, "world-bank-health", name, "GET", url, params={"format": "json", "per_page": 2}))
    return probes


async def hdx_ckan(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    base = "https://data.humdata.org/api/3/action/package_search"
    cases = [
        ("q", {"q": "cholera", "rows": 1}),
        ("fq", {"q": "cholera", "fq": "tags:health", "rows": 1}),
        ("sort", {"q": "cholera", "sort": "metadata_modified desc", "rows": 1}),
        ("rows", {"q": "cholera", "rows": 2}),
        ("start", {"q": "cholera", "rows": 1, "start": 1}),
        ("facet", {"q": "cholera", "rows": 0, "facet": "true"}),
        ("facet.mincount", {"q": "cholera", "rows": 0, "facet.field": '["tags"]', "facet.mincount": 1}),
        ("facet.limit", {"q": "cholera", "rows": 0, "facet.field": '["tags"]', "facet.limit": 2}),
        ("facet.field", {"q": "cholera", "rows": 0, "facet.field": '["tags"]'}),
    ]
    return [await request_json(client, "hdx", name, "GET", base, params=params) for name, params in cases]


async def hdx_hapi(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    identifier = os.getenv("HDX_HAPI_APP_IDENTIFIER", "").strip()
    if not identifier:
        return [record("hdx-hapi", "endpoint_specific_contract", "https://hapi.humdata.org/", "BLOCKED", error="HDX_HAPI_APP_IDENTIFIER is not configured; endpoint filters are not treated as absent.")]
    base = "https://hapi.humdata.org/api/v2/coordination-context/operational-presence"
    common = {"app_identifier": identifier, "output_format": "json", "limit": 1, "offset": 0, "location_code": "RWA"}
    cases = [
        ("app_identifier", common),
        ("output_format", common),
        ("limit", {**common, "limit": 2}),
        ("offset", {**common, "offset": 1}),
        ("location_code", common),
        ("sector_name", {**common, "sector_name": "Health"}),
        ("admin1_code", {**common, "admin1_code": "RW01"}),
        ("org_name", {**common, "org_name": "UNICEF"}),
    ]
    return [await request_json(client, "hdx-hapi", name, "GET", base, params=params) for name, params in cases]


async def main_async() -> int:
    headers = {"User-Agent": UA, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
        results = []
        results.extend(await reliefweb(client))
        results.extend(await world_bank(client))
        results.extend(await hdx_ckan(client))
        results.extend(await hdx_hapi(client))
    report = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "blocked": sum(1 for r in results if r["status"] == "BLOCKED"),
        "rule": "Provider errors, transport failures, timeouts and blocked credentials are never interpreted as empty data.",
    }
    (OUT / "LIVE_PARAMETER_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("pass", "fail", "blocked")}, indent=2))
    return 1 if report["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
