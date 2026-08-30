from __future__ import annotations

"""Evidence-driven semantic translation for the ten V6/V7 live providers."""

from dataclasses import asdict
from typing import Any

from .semantic_contracts import CapabilityMode, Completeness
from .source_registry import connector_definition

OPERATIONS: dict[str, str] = {
    "hdx": "discover",
    "reliefweb": "query_documents",
    "who-gho": "get_indicators",
    "world-bank-health": "query_observations",
    "unicef-sdmx": "discover",
    "un-sdg": "query_observations",
    "dhs": "get_indicators",
    "hdx-hapi": "query_observations",
    "unhcr": "query_observations",
    "gdacs": "query_events",
}

HEALTH_TERM_ALIASES = {
    "paludisme": "malaria",
    "choléra": "cholera",
    "cholera": "cholera",
    "rougeole": "measles",
}


def canonical_provider_keywords(value: str) -> tuple[str, str | None]:
    stripped = " ".join(value.strip().split())
    mapped = HEALTH_TERM_ALIASES.get(stripped.casefold())
    if mapped and mapped.casefold() != stripped.casefold():
        return mapped, f"Traduction terminologique HDP explicite : {stripped} → {mapped}."
    return stripped, None


def _base_parameters(intent: Any, result_limit: int) -> dict[str, Any]:
    canonical, _ = canonical_provider_keywords(intent.keywords)
    return {
        "query": canonical,
        "date_from": intent.date_from,
        "date_to": intent.date_to,
        "location": intent.location,
        "result_limit": result_limit,
        "auto_download": False,
    }


def _evidence(source_id: str) -> list[str]:
    evidence = list(connector_definition(source_id).get("documentation_evidence", []))
    additions = {
        "world-bank-health": ["https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures"],
        "un-sdg": ["https://unstats.un.org/SDGAPI/swagger/v1/swagger.json"],
        "hdx-hapi": ["https://hdx-hapi.readthedocs.io/en/latest/getting-started/", "https://hdx-hapi.readthedocs.io/en/latest/data_usage_guides/metadata/"],
        "unhcr": ["https://api.unhcr.org/docs/refugee-statistics.html"],
    }
    return list(dict.fromkeys(evidence + additions.get(source_id, [])))


def translate(source_id: str, intent: Any, *, result_limit: int) -> dict[str, Any]:
    params = _base_parameters(intent, result_limit)
    canonical_query, semantic_note = canonical_provider_keywords(intent.keywords)
    native: dict[str, Any] = {}
    criteria: dict[str, CapabilityMode] = {}
    warnings: list[str] = []
    if semantic_note:
        warnings.append(semantic_note)
    executable = True
    completeness = Completeness.BOUNDED
    if intent.keywords:
        criteria["keywords"] = CapabilityMode.TRANSLATED_FILTER if semantic_note else CapabilityMode.NATIVE_FILTER
    if intent.date_from or intent.date_to:
        criteria["time"] = CapabilityMode.POST_FILTER
    if intent.location:
        criteria["geography"] = CapabilityMode.POST_FILTER
    geo = intent.geography

    if source_id == "hdx":
        if geo:
            criteria["geography"] = CapabilityMode.POST_FILTER if canonical_query else CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = bool(canonical_query)
            warnings.append("HDX geography has no verified native package_search mapping; geography-only execution is blocked and keyword+geography remains bounded.")

    elif source_id == "reliefweb":
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native.update({"filter[field]": "country", "filter[value]": geo.name})
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.TRANSLATED_FILTER
            native["filter_date_field"] = "date.created"
            native["filter_date_from"] = intent.date_from
            native["filter_date_to"] = intent.date_to

    elif source_id == "who-gho":
        if geo or intent.date_from or intent.date_to:
            executable = False
            if geo:
                criteria["geography"] = CapabilityMode.UNSUPPORTED
            if intent.date_from or intent.date_to:
                criteria["time"] = CapabilityMode.UNSUPPORTED
            warnings.append("WHO observation routing is blocked pending requalification of the post-2025 World Health Data Hub contract; legacy GHO remains catalogue-only.")

    elif source_id == "world-bank-health":
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native["country"] = geo.iso3
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.TRANSLATED_FILTER
            start = intent.date_from[:4] if intent.date_from else ""
            end = intent.date_to[:4] if intent.date_to else ""
            native["date"] = f"{start}:{end}" if start and end else start or end
        native["indicator_search"] = canonical_query

    elif source_id == "unicef-sdmx":
        if geo or intent.date_from or intent.date_to:
            executable = False
            if geo:
                criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            if intent.date_from or intent.date_to:
                criteria["time"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            warnings.append("UNICEF SDMX observation routing requires dataflow/DSD-specific key resolution; structure discovery remains executable separately.")

    elif source_id == "un-sdg":
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native["areaCode"] = int(geo.m49)
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.TRANSLATED_FILTER
            if intent.date_from:
                native["timePeriodStart"] = int(intent.date_from[:4])
            if intent.date_to:
                native["timePeriodEnd"] = int(intent.date_to[:4])
        native["series_search"] = canonical_query

    elif source_id == "dhs":
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            native["iso3_lookup"] = geo.iso3
            warnings.append("DHS countryIds use DHS-specific codes. HDP records ISO3 for dynamic catalogue resolution but never substitutes ISO3 directly into countryIds.")

    elif source_id == "hdx-hapi":
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native["location_code"] = geo.iso3
            params["location_code"] = geo.iso3
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.POST_FILTER
            warnings.append("HAPI endpoint time-filter support is endpoint-dependent; current route preserves explicit post-filter status.")

    elif source_id == "unhcr":
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native["cf_type"] = "ISO"
            native["country_roles"] = ["origin", "asylum"]
            native["iso3"] = geo.iso3
            warnings.append("Generic UNHCR geography is executed as two distinct native queries (origin and asylum); roles remain tagged and are never silently fused.")
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.TRANSLATED_FILTER
            if intent.date_from:
                native["yearFrom"] = int(intent.date_from[:4])
            if intent.date_to:
                native["yearTo"] = int(intent.date_to[:4])

    elif source_id == "gdacs":
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.NATIVE_FILTER
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            warnings.append("GDACS administrative ISO3 lookup is not treated as an event-search country filter; exact event filter remains unverified.")
    else:
        executable = False
        warnings.append("No semantic adapter registered for this source.")

    return {
        "source": source_id,
        "operation": OPERATIONS.get(source_id, "unknown"),
        "executable": executable,
        "parameters": params,
        "native_parameters": native,
        "criteria": {key: value.value for key, value in criteria.items()},
        "completeness": completeness.value,
        "warnings": warnings,
        "evidence": _evidence(source_id),
        "canonical_geography": asdict(geo) if geo else None,
    }
