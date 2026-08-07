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
TABULAR_FORMAT_ALIASES = {"csv", "xlsx", "xls", "excel", "spreadsheet"}
M49_TYPE_LABELS = {
    0: "Monde",
    1: "Région",
    2: "Sous-région",
    3: "Région intermédiaire",
    4: "Pays ou zone",
}
OFFICIAL_COD_SERIES = "COD - Subnational Administrative Boundaries"
OFFICIAL_COD_PS_SERIES = "COD - Subnational Population Statistics"
OFFICIAL_COD_LEVELS = {"cod-enhanced", "cod-standard"}
OFFICIAL_COD_POLICIES = {"enhanced_only", "enhanced_preferred"}
OFFICIAL_COD_CATALOG_QUERY = "name:cod-ab-* AND cod_level:(cod-enhanced OR cod-standard)"
OFFICIAL_COD_CATALOG_QUERIES = {
    "cod-ab": OFFICIAL_COD_CATALOG_QUERY,
    "cod-ps": "name:cod-ps-*",
}
OFFICIAL_COD_FAMILIES: dict[str, dict[str, Any]] = {
    "cod-ab": {
        "id": "cod-ab",
        "label": "COD-AB",
        "title": "Limites administratives",
        "data_series": OFFICIAL_COD_SERIES,
        "selectable": True,
        "retired": False,
        "resource_kind": "geospatial",
    },
    "cod-ps": {
        "id": "cod-ps",
        "label": "COD-PS",
        "title": "Statistiques de population infranationales",
        "data_series": OFFICIAL_COD_PS_SERIES,
        "selectable": True,
        "retired": False,
        "resource_kind": "tabular",
    },
    "cod-cs": {
        "id": "cod-cs",
        "label": "COD-CS",
        "title": "Données spécifiques au pays",
        "data_series": None,
        "selectable": False,
        "retired": False,
        "resource_kind": "registry",
        "reason": "Le registre vérifié embarqué ne contient actuellement aucun jeu COD-CS.",
    },
    "cod-hp": {
        "id": "cod-hp",
        "label": "COD-HP",
        "title": "Profil humanitaire",
        "data_series": None,
        "selectable": False,
        "retired": True,
        "resource_kind": "retired",
        "reason": "Famille retirée par OCHA ; les jeux Humanitarian Needs qui lui succèdent ne sont pas des COD.",
    },
}
SELECTABLE_COD_FAMILIES = {family for family, data in OFFICIAL_COD_FAMILIES.items() if data["selectable"]}


def _load_m49_snapshot() -> dict[str, Any]:
    path = Path(__file__).with_name("un_m49_snapshot.json")
    with path.open(encoding="utf-8") as stream:
        snapshot = json.load(stream)
    entities = snapshot.get("entities")
    if snapshot.get("schema_version") != 1 or not isinstance(entities, list):
        raise RuntimeError("Instantané ONU M49 invalide")
    return snapshot


def _load_cod_cs_registry() -> dict[str, Any]:
    path = Path(__file__).with_name("official_cod_cs_registry.json")
    with path.open(encoding="utf-8") as stream:
        registry = json.load(stream)
    if registry.get("schema_version") != 1 or not isinstance(registry.get("datasets"), list):
        raise RuntimeError("Registre COD-CS officiel invalide")
    return registry


UN_M49_SNAPSHOT = _load_m49_snapshot()
OFFICIAL_COD_CS_REGISTRY = _load_cod_cs_registry()
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


def validate_m49_country_code(value: str) -> str:
    code = validate_m49_code(value)
    entity = M49_BY_CODE[code]
    if int(entity["type"]) != 4 or not entity.get("iso3166"):
        raise ValueError("Sélectionnez un pays ou une zone ONU M49 également disponible sur HDX")
    return code


def validate_cod_families(values: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        family = str(value).strip().lower()
        if family not in OFFICIAL_COD_FAMILIES:
            raise ValueError(f"Famille COD inconnue : {family or '(vide)'}")
        if family not in SELECTABLE_COD_FAMILIES:
            reason = str(OFFICIAL_COD_FAMILIES[family].get("reason") or "Famille indisponible")
            raise ValueError(f"{OFFICIAL_COD_FAMILIES[family]['label']} indisponible : {reason}")
        if family not in normalized:
            normalized.append(family)
    if not normalized:
        raise ValueError("Sélectionnez au moins une famille COD officielle disponible")
    return normalized


def official_cod_family_catalog() -> list[dict[str, Any]]:
    result = []
    for family in ("cod-ab", "cod-ps", "cod-cs", "cod-hp"):
        data = dict(OFFICIAL_COD_FAMILIES[family])
        if family == "cod-cs":
            data["registry_dataset_count"] = len(OFFICIAL_COD_CS_REGISTRY["datasets"])
            data["registry_source"] = OFFICIAL_COD_CS_REGISTRY["source"]
        result.append(data)
    return result


def validate_official_cod_policy(value: str) -> str:
    policy = value.strip().lower()
    if policy not in OFFICIAL_COD_POLICIES:
        raise ValueError("Politique COD-AB officielle invalide")
    return policy


def geodata_profile_changed(
    current: dict[str, Any],
    scope_code: str,
    policy: str,
    preferred_format: str,
    cod_families: list[str] | None = None,
) -> bool:
    changed = (
        scope_code != str(current.get("m49_scope_code") or "")
        or policy != str(current.get("official_policy") or "")
        or preferred_format != str(current.get("preferred_format") or "")
    )
    if cod_families is not None:
        changed = changed or cod_families != list(current.get("cod_families") or [])
    return changed


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


def select_cod_resources(
    resources: list[dict[str, Any]], family: str, preferred_format: str
) -> list[dict[str, Any]]:
    normalized_family = family.strip().lower()
    if normalized_family == "cod-ab":
        return select_geodata_resources(resources, preferred_format)
    if normalized_family != "cod-ps":
        return []
    selected = []
    for resource in resources:
        resource_format = normalize_resource_format(resource.get("format"))
        name = str(resource.get("name") or "").lower()
        url_name = str(resource.get("url") or "").rsplit("?", 1)[0].rsplit("/", 1)[-1].lower()
        if (
            any(alias == resource_format or alias in resource_format for alias in TABULAR_FORMAT_ALIASES)
            or any(alias in name for alias in TABULAR_FORMAT_ALIASES)
            or any(url_name.endswith(f".{alias}") for alias in ("csv", "xlsx", "xls"))
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


def official_cod_metadata(
    dataset: dict[str, Any], family: str = "cod-ab"
) -> dict[str, Any] | None:
    normalized_family = family.strip().lower()
    if normalized_family not in SELECTABLE_COD_FAMILIES:
        return None
    cod_level = str(_dataset_value(dataset, "cod_level") or "").strip().lower()
    if normalized_family == "cod-ab" and cod_level not in OFFICIAL_COD_LEVELS:
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
    data_series = str(_dataset_value(dataset, "dataseries_name") or "").strip()
    dataset_name = str(dataset.get("name") or "").strip().lower()
    canonical_name = f"{normalized_family}-{iso3.lower()}"
    official_series = str(OFFICIAL_COD_FAMILIES[normalized_family]["data_series"])
    if (
        data_series.casefold() != official_series.casefold()
        and dataset_name != canonical_name
    ):
        return None

    organization = dataset.get("organization") if isinstance(dataset.get("organization"), dict) else {}
    return {
        "dataset_id": str(dataset.get("name") or dataset.get("id") or ""),
        "iso3": iso3,
        "m49_code": M49_ISO3_TO_CODE[iso3],
        "cod_family": normalized_family,
        "cod_level": cod_level or "not-published",
        "data_series": official_series,
        "publisher": str(organization.get("title") or organization.get("name") or ""),
        "license_id": str(dataset.get("license_id") or ""),
        "metadata_modified": str(dataset.get("metadata_modified") or ""),
    }


def select_official_cod_datasets(
    datasets: list[dict[str, Any]], scope_code: str, policy: str, family: str = "cod-ab"
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scope = validate_m49_code(scope_code)
    normalized_policy = validate_official_cod_policy(policy)
    expected = {str(entity["iso3166"]): entity for entity in m49_country_entities(scope)}
    candidates: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for dataset in datasets:
        metadata = official_cod_metadata(dataset, family)
        if not metadata or metadata["iso3"] not in expected:
            continue
        if (
            family == "cod-ab"
            and normalized_policy == "enhanced_only"
            and metadata["cod_level"] != "cod-enhanced"
        ):
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


def official_cod_availability(
    catalogs: dict[str, list[dict[str, Any]]], families: list[str]
) -> dict[str, Any]:
    selected_families = validate_cod_families(families)
    available_by_family: dict[str, set[str]] = {}
    for family in selected_families:
        available_by_family[family] = {
            metadata["iso3"]
            for dataset in catalogs.get(family, [])
            if (metadata := official_cod_metadata(dataset, family)) is not None
        }
    intersection = set.intersection(*(available_by_family[family] for family in selected_families))
    countries = []
    for iso3 in sorted(intersection, key=lambda code: str(M49_BY_CODE[M49_ISO3_TO_CODE[code]]["name"])):
        entity = M49_BY_CODE[M49_ISO3_TO_CODE[iso3]]
        countries.append(
            {
                "code": str(entity["code"]),
                "name": str(entity["name"]),
                "type": 4,
                "type_label": M49_TYPE_LABELS[4],
                "iso3": iso3,
                "country_count": 1,
            }
        )
    return {
        "selected_families": selected_families,
        "family_counts": {
            family: len(available_by_family[family]) for family in selected_families
        },
        "intersection_count": len(countries),
        "countries": countries,
    }
