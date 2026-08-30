from __future__ import annotations

"""Deterministic semantic routing for HDP federated searches.

The router deliberately separates user intent from provider parameters.  It does not
invent provider identifiers: a geographic value is promoted to a native source
parameter only when an explicit, verified mapping exists.  Otherwise the execution
plan records that HDP must use metadata/post filtering or that the criterion is not
supported by the source operation.
"""

import json
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


M49_PATH = Path(__file__).with_name("un_m49_snapshot.json")


@dataclass(frozen=True)
class Geography:
    input: str
    name: str
    m49: str
    iso3: str
    entity_type: str = "country_or_area"
    authority: str = "United Nations Statistics Division / M49"


@dataclass(frozen=True)
class SemanticIntent:
    keywords: str
    location: str
    date_from: str
    date_to: str
    geography: Geography | None
    interpretation: str


# Capability claims are intentionally conservative and are limited to behaviour
# already represented by the V6 connector contracts/inventory.
SOURCE_CAPABILITIES: dict[str, dict[str, str]] = {
    "hdx": {
        "keywords": "native",
        "geography": "post_filter",
        "time": "post_filter",
    },
    "reliefweb": {
        "keywords": "native",
        "geography": "post_filter",
        "time": "post_filter",
    },
    "who-gho": {
        "keywords": "catalog_metadata",
        "geography": "unsupported_catalog_operation",
        "time": "unsupported_catalog_operation",
    },
    "world-bank-health": {
        "keywords": "catalog_metadata",
        "geography": "unsupported_catalog_operation",
        "time": "unsupported_catalog_operation",
    },
    "unicef-sdmx": {
        "keywords": "catalog_metadata",
        "geography": "unsupported_catalog_operation",
        "time": "unsupported_catalog_operation",
    },
    "un-sdg": {
        "keywords": "catalog_metadata",
        "geography": "unsupported_catalog_operation",
        "time": "unsupported_catalog_operation",
    },
    "dhs": {
        "keywords": "catalog_metadata",
        "geography": "provider_identifier_required",
        "time": "provider_dimension_required",
    },
    "hdx-hapi": {
        "keywords": "catalog_or_endpoint_metadata",
        "geography": "provider_identifier_required",
        "time": "endpoint_dependent",
    },
    "unhcr": {
        "keywords": "limited",
        "geography": "ambiguous_origin_or_asylum",
        "time": "native_year_range",
    },
    "gdacs": {
        "keywords": "post_filter",
        "geography": "post_filter",
        "time": "native",
    },
}


def normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.casefold().strip().split())


def _load_m49_entities() -> tuple[dict[str, Any], ...]:
    with M49_PATH.open(encoding="utf-8") as stream:
        snapshot = json.load(stream)
    entities = snapshot.get("entities")
    if snapshot.get("schema_version") != 1 or not isinstance(entities, list):
        raise RuntimeError("Instantané ONU M49 invalide")
    return tuple(dict(entity) for entity in entities)


M49_ENTITIES = _load_m49_entities()
M49_COUNTRIES = tuple(
    entity for entity in M49_ENTITIES
    if int(entity.get("type", -1)) == 4 and entity.get("iso3166")
)
M49_BY_NORMALIZED_NAME = {
    normalized_text(entity["name"]): entity for entity in M49_COUNTRIES
}
M49_BY_ISO3 = {
    str(entity["iso3166"]).upper(): entity for entity in M49_COUNTRIES
}
M49_BY_CODE = {
    str(entity["code"]): entity for entity in M49_COUNTRIES
}


def resolve_geography(value: str) -> Geography | None:
    """Resolve an exact country/area name, ISO3 or M49 code using the bundled UN snapshot.

    Fuzzy guessing is intentionally excluded from the routing path.  Ambiguous or
    unknown free text remains free text and can still be used by provider searches.
    """
    candidate = value.strip()
    if not candidate:
        return None
    entity = M49_BY_NORMALIZED_NAME.get(normalized_text(candidate))
    if entity is None:
        entity = M49_BY_ISO3.get(candidate.upper())
    if entity is None:
        entity = M49_BY_CODE.get(candidate.zfill(3) if candidate.isdigit() else candidate)
    if entity is None:
        return None
    return Geography(
        input=candidate,
        name=str(entity["name"]),
        m49=str(entity["code"]),
        iso3=str(entity["iso3166"]).upper(),
    )


def _validate_date(value: str) -> str:
    if not value:
        return ""
    return date.fromisoformat(value).isoformat()


def build_semantic_intent(
    *,
    query: str = "",
    location: str = "",
    date_from: str = "",
    date_to: str = "",
) -> SemanticIntent:
    """Build the canonical HDP intent.

    An exact country entered as the sole keyword is interpreted as geography.  This
    fixes the class of failure where ``RWANDA`` was sent only to text-search capable
    catalogues.  A non-geographic query is never silently rewritten.
    """
    query = " ".join(query.strip().split())
    location = " ".join(location.strip().split())
    start = _validate_date(date_from)
    end = _validate_date(date_to)
    if start and end and start > end:
        raise ValueError("date_from doit être antérieure ou égale à date_to")

    explicit_geo = resolve_geography(location) if location else None
    query_geo = resolve_geography(query) if query and not location else None
    if explicit_geo:
        return SemanticIntent(query, explicit_geo.name, start, end, explicit_geo, "explicit_location")
    if query_geo:
        return SemanticIntent("", query_geo.name, start, end, query_geo, "keyword_resolved_as_geography")
    return SemanticIntent(query, location, start, end, None, "literal")


def _criterion_status(source_id: str, criterion: str, active: bool) -> str:
    if not active:
        return "not_requested"
    return SOURCE_CAPABILITIES.get(source_id, {}).get(criterion, "unknown")


def route_intent_to_source(source_id: str, intent: SemanticIntent, *, result_limit: int = 25) -> dict[str, Any]:
    """Create an auditable per-source route without inventing provider IDs."""
    if source_id not in SOURCE_CAPABILITIES:
        return {
            "source": source_id,
            "status": "unsupported_source",
            "parameters": {},
            "criteria": {},
            "warnings": ["Source absente de la matrice de capacités du routeur."],
        }

    parameters: dict[str, Any] = {
        "query": intent.keywords,
        "date_from": intent.date_from,
        "date_to": intent.date_to,
        "location": intent.location,
        "result_limit": result_limit,
        "auto_download": False,
    }
    criteria = {
        "keywords": _criterion_status(source_id, "keywords", bool(intent.keywords)),
        "geography": _criterion_status(source_id, "geography", bool(intent.location)),
        "time": _criterion_status(source_id, "time", bool(intent.date_from or intent.date_to)),
    }
    warnings: list[str] = []
    if intent.geography:
        geo_status = criteria["geography"]
        if geo_status in {"provider_identifier_required", "ambiguous_origin_or_asylum", "unsupported_catalog_operation"}:
            warnings.append(
                f"{intent.geography.name} est résolu par HDP (ISO3={intent.geography.iso3}, M49={intent.geography.m49}), "
                f"mais aucun identifiant fournisseur sûr n'est injecté automatiquement pour {source_id}."
            )
        elif geo_status == "post_filter":
            warnings.append(
                "Le critère géographique sera vérifié sur les métadonnées normalisées après la réponse fournisseur; "
                "l'exhaustivité dépend donc de la pagination amont."
            )

    requested = [value for value in criteria.values() if value != "not_requested"]
    if any(value.startswith("unsupported") for value in requested):
        status = "partial"
    elif any(value in {"provider_identifier_required", "ambiguous_origin_or_asylum", "unknown"} for value in requested):
        status = "partial"
    elif requested:
        status = "routable"
    else:
        status = "routable"

    return {
        "source": source_id,
        "status": status,
        "parameters": parameters,
        "criteria": criteria,
        "warnings": warnings,
    }


def build_execution_plan(
    sources: Iterable[str],
    *,
    query: str = "",
    location: str = "",
    date_from: str = "",
    date_to: str = "",
    result_limit: int = 25,
) -> dict[str, Any]:
    if result_limit < 1 or result_limit > 100:
        raise ValueError("result_limit doit être compris entre 1 et 100")
    intent = build_semantic_intent(
        query=query,
        location=location,
        date_from=date_from,
        date_to=date_to,
    )
    routes = [route_intent_to_source(source_id, intent, result_limit=result_limit) for source_id in dict.fromkeys(sources)]
    return {
        "schema_version": 1,
        "intent": {
            **asdict(intent),
            "geography": asdict(intent.geography) if intent.geography else None,
        },
        "routes": routes,
        "principles": {
            "no_silent_error_as_empty": True,
            "no_unverified_provider_identifier": True,
            "post_filter_is_explicit": True,
        },
    }
