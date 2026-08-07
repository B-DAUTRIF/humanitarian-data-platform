from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FORMAT_ALIASES: dict[str, set[str]] = {
    "geojson": {"geojson", "json"},
    "geopackage": {"geopackage", "gpkg"},
    "shapefile": {"shp", "shp zip", "shapefile", "zipped shapefile"},
    "geodatabase": {"geodatabase", "gdb", "file geodatabase"},
}
M49_TYPE_LABELS = {
    0: "Monde",
    1: "Région",
    2: "Sous-région",
    3: "Région intermédiaire",
    4: "Pays ou zone",
}
OFFICIAL_COD_SERIES = "COD - Subnational Administrative Boundaries"
OFFICIAL_COD_LEVELS = {"cod-enhanced", "cod-standard"}
OFFICIAL_COD_POLICIES = {"enhanced_only", "enhanced_preferred"}


def _load_m49_snapshot() -> dict[str, Any]:
    path = Path(__file__).with_name("un_m49_snapshot.json")
    with path.open(encoding="utf-8") as stream:
        snapshot = json.load(stream)
    entities = snapshot.get("entities")
    if snapshot.get("schema_version") != 1 or not isinstance(entities, list):
        raise RuntimeError("Instantané ONU M49 invalide")
    return snapshot


UN_M49_SNAPSHOT = _load_m49_snapshot()
UN_M49_SOURCE: dict[str, Any] = dict(UN_M49_SNAPSHOT["source"])
UN_M49_ENTITIES: tuple[dict[str, Any], ...] = tuple(UN_M49_SNAPSHOT["entities"])
M49_BY_CODE = {str(entity["code"]): entity for entity in UN_M49_ENTITIES}
M49_ISO3_TO_CODE = {
    str(entity["iso3166"]).upper(): str(entity["code"])
    for entity in UN_M49_ENTITIES
    if entity.get("iso3166")
}


def validate_repository_name(value: str) -> str:
    name = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name):
        raise ValueError(
            "Le nom du dépôt doit contenir 1 à 100 lettres, chiffres, points, tirets ou caractères de soulignement"
        )
    if name in {".", ".."}:
        raise ValueError("Nom de dépôt GitHub non autorisé")
    return name


def validate_github_owner(value: str) -> str:
    owner = value.strip()
    if owner and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner):
        raise ValueError("Nom de propriétaire ou d'organisation GitHub invalide")
    return owner


def github_repository_endpoint(owner: str, authenticated_login: str) -> str:
    normalized = validate_github_owner(owner)
    if not normalized or normalized.casefold() == authenticated_login.casefold():
        return "https://api.github.com/user/repos"
    return f"https://api.github.com/orgs/{normalized}/repos"


def validate_hdx_dataset_id(value: str) -> str:
    dataset_id = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,99}", dataset_id):
        raise ValueError("Identifiant de jeu HDX invalide")
    return dataset_id


def validate_m49_code(value: str) -> str:
    code = value.strip()
    if not re.fullmatch(r"\d{3}", code) or code not in M49_BY_CODE:
        raise ValueError("Code ONU M49 absent de la nomenclature embarquée")
    return code


def validate_official_cod_policy(value: str) -> str:
    policy = value.strip().lower()
    if policy not in OFFICIAL_COD_POLICIES:
        raise ValueError("Politique COD-AB officielle invalide")
    return policy


def _m49_depth(code: str) -> int:
    depth = 0
    current = M49_BY_CODE[code]
    visited = {code}
    while current.get("parent"):
        parent = str(current["parent"])
        if parent in visited or parent not in M49_BY_CODE:
            break
        visited.add(parent)
        depth += 1
        current = M49_BY_CODE[parent]
    return depth


def m49_country_entities(scope_code: str) -> list[dict[str, Any]]:
    scope = validate_m49_code(scope_code)
    countries: list[dict[str, Any]] = []
    for entity in UN_M49_ENTITIES:
        if int(entity["type"]) != 4 or not entity.get("iso3166"):
            continue
        current = str(entity["code"])
        visited: set[str] = set()
        while current not in visited and current in M49_BY_CODE:
            if current == scope:
                countries.append(dict(entity))
                break
            visited.add(current)
            parent = M49_BY_CODE[current].get("parent")
            if not parent:
                break
            current = str(parent)
    return sorted(countries, key=lambda item: (str(item["name"]), str(item["code"])))


def un_m49_catalog() -> list[dict[str, Any]]:
    children: dict[str | None, list[dict[str, Any]]] = {}
    for entity in UN_M49_ENTITIES:
        parent = str(entity["parent"]) if entity.get("parent") else None
        children.setdefault(parent, []).append(entity)
    for values in children.values():
        values.sort(key=lambda item: (int(item["type"]), str(item["name"])))

    catalog: list[dict[str, Any]] = []

    def visit(entity: dict[str, Any]) -> None:
        code = str(entity["code"])
        catalog.append(
            {
                "code": code,
                "name": str(entity["name"]),
                "type": int(entity["type"]),
                "type_label": M49_TYPE_LABELS[int(entity["type"])],
                "parent": entity.get("parent"),
                "iso3": entity.get("iso3166"),
                "depth": _m49_depth(code),
                "country_count": len(m49_country_entities(code)),
            }
        )
        for child in children.get(code, []):
            visit(child)

    world = M49_BY_CODE["001"]
    visit(world)
    return catalog


def m49_scope(code: str) -> dict[str, Any]:
    normalized = validate_m49_code(code)
    entity = M49_BY_CODE[normalized]
    return {
        "code": normalized,
        "name": str(entity["name"]),
        "type": int(entity["type"]),
        "type_label": M49_TYPE_LABELS[int(entity["type"])],
        "parent": entity.get("parent"),
        "iso3": entity.get("iso3166"),
        "country_count": len(m49_country_entities(normalized)),
    }


def normalize_resource_format(value: str | None) -> str:
    return (value or "").strip().lower().lstrip(".")


def select_geodata_resources(
    resources: list[dict[str, Any]], preferred_format: str
) -> list[dict[str, Any]]:
    aliases = FORMAT_ALIASES[preferred_format]
    selected = []
    for resource in resources:
        resource_format = normalize_resource_format(resource.get("format"))
        name = str(resource.get("name") or "").lower()
        url = str(resource.get("url") or "")
        suffix = url.rsplit("?", 1)[0].rsplit("/", 1)[-1].lower()
        if (
            resource_format in aliases
            or any(alias in resource_format for alias in aliases)
            or any(alias in name for alias in aliases)
            or any(suffix.endswith(f".{alias}") for alias in aliases)
        ):
            selected.append(resource)
    return selected


def _dataset_value(dataset: dict[str, Any], key: str) -> Any:
    for candidate, value in dataset.items():
        if str(candidate).casefold() == key.casefold() and value not in (None, ""):
            return value
    for extra in dataset.get("extras", []):
        if not isinstance(extra, dict):
            continue
        if str(extra.get("key") or "").casefold() == key.casefold():
            return extra.get("value")
    return None


def official_cod_metadata(dataset: dict[str, Any]) -> dict[str, Any] | None:
    cod_level = str(_dataset_value(dataset, "cod_level") or "").strip().lower()
    data_series = str(_dataset_value(dataset, "dataseries_name") or "").strip()
    if cod_level not in OFFICIAL_COD_LEVELS or data_series.casefold() != OFFICIAL_COD_SERIES.casefold():
        return None

    iso3_codes: set[str] = set()
    for group in dataset.get("groups", []):
        if not isinstance(group, dict):
            continue
        name = str(group.get("name") or "").upper()
        if name in M49_ISO3_TO_CODE:
            iso3_codes.add(name)
    for field in ("iso3", "country_code", "location_code"):
        value = str(_dataset_value(dataset, field) or "").upper()
        if value in M49_ISO3_TO_CODE:
            iso3_codes.add(value)
    if len(iso3_codes) != 1:
        return None

    iso3 = next(iter(iso3_codes))
    organization = dataset.get("organization") if isinstance(dataset.get("organization"), dict) else {}
    return {
        "dataset_id": str(dataset.get("name") or dataset.get("id") or ""),
        "iso3": iso3,
        "m49_code": M49_ISO3_TO_CODE[iso3],
        "cod_level": cod_level,
        "data_series": OFFICIAL_COD_SERIES,
        "publisher": str(organization.get("title") or organization.get("name") or ""),
        "license_id": str(dataset.get("license_id") or ""),
        "metadata_modified": str(dataset.get("metadata_modified") or ""),
    }


def select_official_cod_datasets(
    datasets: list[dict[str, Any]], scope_code: str, policy: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scope = validate_m49_code(scope_code)
    normalized_policy = validate_official_cod_policy(policy)
    expected = {str(entity["iso3166"]): entity for entity in m49_country_entities(scope)}
    candidates: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for dataset in datasets:
        metadata = official_cod_metadata(dataset)
        if not metadata or metadata["iso3"] not in expected:
            continue
        if normalized_policy == "enhanced_only" and metadata["cod_level"] != "cod-enhanced":
            continue
        candidates.setdefault(metadata["iso3"], []).append((dataset, metadata))

    selected: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for iso3, entity in expected.items():
        available = candidates.get(iso3, [])
        if not available:
            missing.append(dict(entity))
            continue
        available.sort(
            key=lambda item: (
                item[1]["cod_level"] == "cod-enhanced",
                item[1]["metadata_modified"],
                item[1]["dataset_id"],
            ),
            reverse=True,
        )
        dataset = dict(available[0][0])
        dataset["_hdp_official"] = available[0][1]
        selected.append(dataset)
    selected.sort(key=lambda item: item["_hdp_official"]["iso3"])
    missing.sort(key=lambda item: str(item["name"]))
    return selected, missing
