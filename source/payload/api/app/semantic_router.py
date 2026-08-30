from __future__ import annotations

"""Canonical semantic intent and auditable provider execution planning."""

import json
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .provider_semantic_adapters import OPERATIONS, canonical_provider_keywords, translate
from .semantic_provenance import query_fingerprint

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
    canonical_keywords: str
    location: str
    date_from: str
    date_to: str
    geography: Geography | None
    interpretation: str
    semantic_notes: tuple[str, ...] = ()


SOURCE_CAPABILITIES = {source_id: {"operation": operation} for source_id, operation in OPERATIONS.items()}


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
M49_COUNTRIES = tuple(entity for entity in M49_ENTITIES if int(entity.get("type", -1)) == 4 and entity.get("iso3166"))
M49_BY_NORMALIZED_NAME = {normalized_text(entity["name"]): entity for entity in M49_COUNTRIES}
M49_BY_ISO3 = {str(entity["iso3166"]).upper(): entity for entity in M49_COUNTRIES}
M49_BY_CODE = {str(entity["code"]): entity for entity in M49_COUNTRIES}


def resolve_geography(value: str) -> Geography | None:
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
    return Geography(input=candidate, name=str(entity["name"]), m49=str(entity["code"]), iso3=str(entity["iso3166"]).upper())


def _validate_date(value: str) -> str:
    return date.fromisoformat(value).isoformat() if value else ""


def build_semantic_intent(*, query: str = "", location: str = "", date_from: str = "", date_to: str = "") -> SemanticIntent:
    query = " ".join(query.strip().split())
    location = " ".join(location.strip().split())
    start, end = _validate_date(date_from), _validate_date(date_to)
    if start and end and start > end:
        raise ValueError("date_from doit être antérieure ou égale à date_to")
    explicit_geo = resolve_geography(location) if location else None
    query_geo = resolve_geography(query) if query and not location else None
    if query_geo:
        return SemanticIntent("", "", query_geo.name, start, end, query_geo, "keyword_resolved_as_geography")
    canonical_keywords, note = canonical_provider_keywords(query)
    notes = (note,) if note else ()
    if explicit_geo:
        return SemanticIntent(query, canonical_keywords, explicit_geo.name, start, end, explicit_geo, "explicit_location", notes)
    return SemanticIntent(query, canonical_keywords, location, start, end, None, "literal", notes)


def route_intent_to_source(source_id: str, intent: SemanticIntent, *, result_limit: int = 25) -> dict[str, Any]:
    if source_id not in SOURCE_CAPABILITIES:
        return {"source": source_id, "operation": "unknown", "executable": False, "parameters": {}, "native_parameters": {}, "criteria": {}, "completeness": "unknown", "warnings": ["Source absente du registre d’adaptateurs sémantiques."], "evidence": []}
    return translate(source_id, intent, result_limit=result_limit)


def build_execution_plan(sources: Iterable[str], *, query: str = "", location: str = "", date_from: str = "", date_to: str = "", result_limit: int = 25) -> dict[str, Any]:
    if result_limit < 1 or result_limit > 100:
        raise ValueError("result_limit doit être compris entre 1 et 100")
    if not any(str(value or "").strip() for value in (query, location, date_from, date_to)):
        raise ValueError("La recherche sémantique doit contenir au moins un critère : mots-clés, lieu ou période")
    intent = build_semantic_intent(query=query, location=location, date_from=date_from, date_to=date_to)
    routes = [route_intent_to_source(source_id, intent, result_limit=result_limit) for source_id in dict.fromkeys(sources)]
    plan = {
        "schema_version": 2,
        "contract_version": "7.0.0",
        "intent": {**asdict(intent), "geography": asdict(intent.geography) if intent.geography else None, "semantic_notes": list(intent.semantic_notes)},
        "routes": routes,
        "principles": {
            "no_silent_error_as_empty": True,
            "no_unverified_provider_identifier": True,
            "post_filter_is_explicit": True,
            "non_exhaustive_post_filter_cannot_claim_empty": True,
            "provider_operations_are_explicit": True,
            "semantic_request_requires_explicit_criterion": True,
        },
    }
    plan["query_fingerprint"] = query_fingerprint(plan)
    return plan
