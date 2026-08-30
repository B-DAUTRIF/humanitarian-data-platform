from __future__ import annotations

"""Provider-specific semantic translation.

Only translations supported by the checked-in V6 provider contracts are emitted.
Unknown provider identifiers are blocked rather than guessed.
"""

from dataclasses import asdict
from typing import Any

from .semantic_contracts import CapabilityMode, Completeness
from .source_registry import connector_definition


OPERATIONS: dict[str, str] = {
    "hdx": "discover",
    "reliefweb": "query_documents",
    "who-gho": "get_indicators",
    "world-bank-health": "get_indicators",
    "unicef-sdmx": "discover",
    "un-sdg": "get_indicators",
    "dhs": "get_indicators",
    "hdx-hapi": "query_observations",
    "unhcr": "query_observations",
    "gdacs": "query_events",
}


def _base_parameters(intent: Any, result_limit: int) -> dict[str, Any]:
    return {
        "query": intent.keywords,
        "date_from": intent.date_from,
        "date_to": intent.date_to,
        "location": intent.location,
        "result_limit": result_limit,
        "auto_download": False,
    }


def _evidence(source_id: str) -> list[str]:
    return list(connector_definition(source_id).get("documentation_evidence", []))


def translate(source_id: str, intent: Any, *, result_limit: int) -> dict[str, Any]:
    params = _base_parameters(intent, result_limit)
    native: dict[str, Any] = {}
    criteria: dict[str, CapabilityMode] = {}
    warnings: list[str] = []
    executable = True
    completeness = Completeness.BOUNDED

    if intent.keywords:
        criteria["keywords"] = CapabilityMode.NATIVE_FILTER
    if intent.date_from or intent.date_to:
        criteria["time"] = CapabilityMode.POST_FILTER
    if intent.location:
        criteria["geography"] = CapabilityMode.POST_FILTER

    geo = intent.geography

    if source_id == "hdx":
        # CKAN package_search remains a catalogue operation. HDP does not invent an
        # fq field/value for HDX geography until the HDX metadata contract proves it.
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = bool(intent.keywords)
            warnings.append("HDX geography mapping is not yet verified for native package_search; geography-only execution is blocked.")
        completeness = Completeness.BOUNDED

    elif source_id == "reliefweb":
        # ReliefWeb documents country.iso3; encode the structured filter in the
        # adapter output. The request builder consumes __semantic_native_filter.
        if geo:
            criteria["geography"] = CapabilityMode.TRANSLATED_FILTER
            native["filter[field]"] = "country.iso3"
            native["filter[value]"] = geo.iso3
            params["__semantic_native_filter"] = dict(native)
        completeness = Completeness.BOUNDED

    elif source_id in {"who-gho", "world-bank-health", "unicef-sdmx", "un-sdg"}:
        # Current V6 operations are catalogue/structure discovery, not observation
        # queries. A country-only request must therefore not be executed as if it
        # queried observations.
        if geo:
            criteria["geography"] = CapabilityMode.UNSUPPORTED
            executable = False
            warnings.append("Current connector operation is catalogue/structure discovery; geographic observation query requires a dedicated operation.")
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.UNSUPPORTED
            executable = False

    elif source_id == "dhs":
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            warnings.append("DHS countryIds require the DHS provider catalogue; ISO3 is not substituted without a verified DHS mapping.")

    elif source_id == "hdx-hapi":
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            warnings.append("HAPI location_code requires the HAPI location catalogue; ISO3/M49 is not guessed.")

    elif source_id == "unhcr":
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            warnings.append("UNHCR geography is semantically ambiguous: choose country of origin or country of asylum before execution.")
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.TRANSLATED_FILTER

    elif source_id == "gdacs":
        if intent.date_from or intent.date_to:
            criteria["time"] = CapabilityMode.NATIVE_FILTER
        if geo:
            criteria["geography"] = CapabilityMode.BLOCKED_MISSING_MAPPING
            executable = False
            warnings.append("GDACS native country filtering is not emitted until its exact Swagger request parameter is represented in the HDP contract.")
        completeness = Completeness.BOUNDED

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
