from __future__ import annotations

import re
from typing import Any


GEO_SCALES: tuple[dict[str, Any], ...] = (
    {
        "id": "terrain",
        "rank": 1,
        "label": "Terrain",
        "description": "Site, camp, quartier ou voisinage immédiat",
    },
    {
        "id": "local",
        "rank": 2,
        "label": "Local",
        "description": "Commune, district ou niveaux administratifs détaillés",
    },
    {
        "id": "national",
        "rank": 3,
        "label": "National",
        "description": "Pays et principaux niveaux administratifs",
    },
    {
        "id": "regional",
        "rank": 4,
        "label": "Régional",
        "description": "Ensemble de pays ou région humanitaire",
    },
    {
        "id": "world",
        "rank": 5,
        "label": "Monde",
        "description": "Couverture mondiale maximale",
    },
)
GEO_SCALE_IDS = {item["id"] for item in GEO_SCALES}

FORMAT_ALIASES: dict[str, set[str]] = {
    "geojson": {"geojson", "json"},
    "geopackage": {"geopackage", "gpkg"},
    "shapefile": {"shp", "shp zip", "shapefile", "zipped shapefile"},
    "geodatabase": {"geodatabase", "gdb", "file geodatabase"},
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
