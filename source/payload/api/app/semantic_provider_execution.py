from __future__ import annotations

"""Execution helpers for semantic routes that need provider-native parameters."""

import asyncio
from typing import Any

import httpx


async def execute_reliefweb_native(route: dict[str, Any], global_settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
    """Execute ReliefWeb with its documented structured country/date filters."""
    from .main import RELIEFWEB_APPNAME, normalize_reliefweb_items

    if not RELIEFWEB_APPNAME:
        raise RuntimeError("ReliefWeb exige RELIEFWEB_APPNAME pré-approuvé")
    parameters = route["parameters"]
    native = route.get("native_parameters", {})
    query: dict[str, Any] = {
        "appname": RELIEFWEB_APPNAME,
        "limit": int(parameters.get("result_limit") or 25),
        "offset": 0,
        "profile": "full",
        "preset": "latest",
        "sort[]": "date.created:desc",
    }
    if parameters.get("query"):
        query["query[value]"] = parameters["query"]
    if native.get("filter[field]"):
        query["filter[field]"] = native["filter[field]"]
        query["filter[value]"] = native["filter[value]"]
    if native.get("filter_date_field"):
        # A single date filter can represent both bounds. If geography is also
        # present, nested ReliefWeb filters are required; implement that explicitly.
        date_from = native.get("filter_date_from")
        date_to = native.get("filter_date_to")
        if "filter[field]" in query:
            country_field, country_value = query.pop("filter[field]"), query.pop("filter[value]")
            query["filter[operator]"] = "AND"
            query["filter[conditions][0][field]"] = country_field
            query["filter[conditions][0][value]"] = country_value
            query["filter[conditions][1][field]"] = native["filter_date_field"]
            if date_from:
                query["filter[conditions][1][value][from]"] = f"{date_from}T00:00:00+00:00"
            if date_to:
                query["filter[conditions][1][value][to]"] = f"{date_to}T23:59:59+00:00"
        else:
            query["filter[field]"] = native["filter_date_field"]
            if date_from:
                query["filter[value][from]"] = f"{date_from}T00:00:00+00:00"
            if date_to:
                query["filter[value][to]"] = f"{date_to}T23:59:59+00:00"

    timeout = httpx.Timeout(float(global_settings["timeout_seconds"]), connect=float(global_settings["connect_timeout_seconds"]))
    retries = int(global_settings["retry_count"])
    backoff = int(global_settings["backoff_seconds"])
    headers = {"User-Agent": str(global_settings["user_agent"]), "Accept-Language": str(global_settings["accept_language"]), "Accept": "application/json"}
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get("https://api.reliefweb.int/v2/reports", params=query, headers=headers)
                response.raise_for_status()
                payload = response.json()
                return payload, normalize_reliefweb_items(payload)
        except httpx.HTTPError as exc:
            last_error = exc
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if attempt >= retries or (status is not None and status != 429 and status < 500):
                raise
            await asyncio.sleep(backoff * (2**attempt))
    raise RuntimeError("Échec ReliefWeb sans réponse") from last_error
