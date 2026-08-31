from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

import httpx

from ..base.contracts import resolve_provider_configuration
from .descriptor import WORLD_BANK_HEALTH_DESCRIPTOR

ISO3_RE = re.compile(r"^[A-Z]{3}$")
FREQUENCIES = {"", "Y", "Q", "M"}
# Provider aggregate identifiers that are syntactically three letters but are not
# sovereign ISO3 countries. The authoritative country/aggregate catalogue remains
# the final source of truth; this deny-list prevents common silent conflation.
WORLD_BANK_AGGREGATE_CODES = {
    "WLD", "ARB", "CSS", "CEB", "EAR", "EAS", "EAP", "TEA", "EMU", "ECS", "ECA", "TEC",
    "EUU", "FCS", "HPC", "HIC", "IBD", "IBT", "IDB", "IDX", "IDA", "LTE", "LCN", "LAC", "TLA",
    "LDC", "LMY", "LIC", "LMC", "MEA", "MNA", "TMN", "MIC", "NAC", "OED", "OSS", "PSS",
    "PST", "PRE", "SST", "SAS", "TSA", "SSA", "SSF", "TSS", "UMC",
}


def validate_country_code(value: str) -> str:
    value = value.strip().upper()
    if value in {"", "ALL"}:
        return "all"
    parts = value.split(";")
    if not all(ISO3_RE.fullmatch(part) for part in parts):
        raise ValueError("World Bank sovereign-country routing requires verified ISO3 codes")
    aggregates = [part for part in parts if part in WORLD_BANK_AGGREGATE_CODES]
    if aggregates:
        raise ValueError(f"World Bank aggregate identifiers require explicit aggregate semantics: {','.join(aggregates)}")
    return ";".join(parts)


def build_observation_request(*, country: str, indicator: str, source: int = 2, date: str = "", page: int = 1, per_page: int = 50, mrv: int | None = None, mrnev: int | None = None, gapfill: bool = False, frequency: str = "", footnote: bool = False, language: str = "en") -> dict[str, Any]:
    country = validate_country_code(country)
    indicator = ";".join(x.strip() for x in indicator.split(";") if x.strip())
    if not indicator:
        raise ValueError("At least one World Bank indicator code is required")
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be positive")
    frequency = frequency.upper()
    if frequency not in FREQUENCIES:
        raise ValueError("frequency must be Y, Q, M or empty")
    params: dict[str, Any] = {"format": "json", "source": int(source), "page": int(page), "per_page": int(per_page)}
    if date:
        params["date"] = date
    if mrv is not None:
        params["mrv"] = int(mrv)
    if mrnev is not None:
        params["mrnev"] = int(mrnev)
    if gapfill:
        params["gapfill"] = "Y"
    if frequency:
        params["frequency"] = frequency
    if footnote:
        params["footnote"] = "y"
    lang = language.strip().lower()
    prefix = f"/{lang}" if lang and lang != "en" else ""
    url = f"https://api.worldbank.org{prefix}/v2/country/{country}/indicator/{indicator}"
    return {"method": "GET", "url": url, "query_parameters": params, "qualified_format": "json"}


def normalize_observations(payload: Any, request_url: str = "") -> list[dict[str, Any]]:
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list) else []
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        country = row.get("country") if isinstance(row.get("country"), dict) else {}
        indicator = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        code = str(indicator.get("id") or "")
        iso3 = str(row.get("countryiso3code") or "")
        period = str(row.get("date") or "")
        items.append({
            "id": f"{code}:{iso3 or country.get('id')}:{period}",
            "title": f"{indicator.get('value') or code} — {country.get('value') or iso3} — {period}",
            "description": f"value={row.get('value')}; obs_status={row.get('obs_status') or ''}; decimal={row.get('decimal')}",
            "date": f"{period}-12-31" if period.isdigit() and len(period) == 4 else None,
            "url": request_url,
            "source": "World Bank Health Indicators",
            "organization": "World Bank",
            "geographic_scope": country.get("value") or iso3,
            "country_iso3": iso3,
            "indicator_code": code,
            "indicator_name": indicator.get("value"),
            "value": row.get("value"),
            "observation_status": row.get("obs_status"),
            "decimal": row.get("decimal"),
            "_native": row,
            "resources": [],
        })
    return items


class WorldBankHealthService:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings

    def effective_configuration(self, *, global_settings: dict[str, Any] | None = None, project_settings: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        return resolve_provider_configuration(WORLD_BANK_HEALTH_DESCRIPTOR, global_settings=global_settings, project_settings=project_settings)

    async def get_json(self, url: str, params: dict[str, Any]) -> tuple[Any, str, int]:
        timeout = httpx.Timeout(float(self.settings.get("timeout_seconds", 40)), connect=float(self.settings.get("connect_timeout_seconds", 20)))
        headers = {"User-Agent": str(self.settings.get("user_agent", "HDP/7")), "Accept": "application/json", "Accept-Language": str(self.settings.get("accept_language", "en"))}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json(), str(response.request.url), response.status_code

    async def list_indicators(self, *, source: int = 2, page: int = 1, per_page: int = 20000) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        url = f"https://api.worldbank.org/v2/source/{int(source)}/indicator"
        params = {"format": "json", "page": int(page), "per_page": int(per_page)}
        payload, native_url, status = await self.get_json(url, params)
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list) else []
        return payload, rows, {"method": "GET", "url": native_url, "query_parameters": params, "http_status": status}

    async def observations(self, **kwargs: Any) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        spec = build_observation_request(**kwargs)
        payload, native_url, status = await self.get_json(spec["url"], spec["query_parameters"])
        native = dict(spec)
        native["url"] = native_url
        native["http_status"] = status
        return payload, normalize_observations(payload, native_url), native


def request_url(spec: dict[str, Any]) -> str:
    return f"{spec['url']}?{urlencode(spec['query_parameters'])}"
