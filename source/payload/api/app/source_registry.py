from __future__ import annotations

import re
from copy import deepcopy
from typing import Any
from urllib.parse import urlencode


REGISTRY_VERSION = "3.0.0-iteration-1"
VERIFIED_AT = "2026-08-14"


def field(
    value_type: str,
    title: str,
    *,
    default: Any = None,
    description: str = "",
    minimum: int | None = None,
    maximum: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[Any] | None = None,
    items: dict[str, Any] | None = None,
    read_only: bool = False,
) -> dict[str, Any]:
    definition: dict[str, Any] = {"type": value_type, "title": title}
    if default is not None:
        definition["default"] = default
    if description:
        definition["description"] = description
    if minimum is not None:
        definition["minimum"] = minimum
    if maximum is not None:
        definition["maximum"] = maximum
    if min_length is not None:
        definition["minLength"] = min_length
    if max_length is not None:
        definition["maxLength"] = max_length
    if pattern is not None:
        definition["pattern"] = pattern
    if enum is not None:
        definition["enum"] = enum
    if items is not None:
        definition["items"] = items
    if read_only:
        definition["readOnly"] = True
    return definition


GLOBAL_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "enabled": field("boolean", "Connecteur actif", default=True),
        "timeout_seconds": field(
            "integer", "Délai maximal", default=40, minimum=5, maximum=180
        ),
        "retry_count": field(
            "integer", "Nouvelles tentatives", default=2, minimum=0, maximum=5
        ),
        "backoff_seconds": field(
            "integer", "Délai initial de reprise", default=2, minimum=1, maximum=60
        ),
    },
}


COMMON_PROJECT_PROPERTIES: dict[str, Any] = {
    "query": field(
        "string",
        "Recherche",
        default="",
        min_length=0,
        max_length=200,
        description="Mots-clés transmis ou utilisés pour filtrer le catalogue (2 caractères minimum lors de l’exécution).",
    ),
    "result_limit": field(
        "integer", "Nombre maximal de résultats", default=25, minimum=1, maximum=100
    ),
    "auto_download": field(
        "boolean", "Télécharger les ressources", default=False
    ),
}


def project_schema(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    properties = deepcopy(COMMON_PROJECT_PROPERTIES)
    properties.update(deepcopy(extra or {}))
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["query", "result_limit", "auto_download"],
        "properties": properties,
    }


CONNECTORS: dict[str, dict[str, Any]] = {
    "hdx": {
        "version": "1.0.0",
        "base_url": "https://data.humdata.org/api/3/action/package_search",
        "allowed_hosts": ["data.humdata.org"],
        "secret_environment_variable": None,
        "documentation_evidence": ["https://docs.ckan.org/en/latest/api/"],
        "project_schema": project_schema(
            {
                "start": field("integer", "Décalage", default=0, minimum=0, maximum=10000),
                "fq": field(
                    "string", "Filtre CKAN fq", default="", max_length=500,
                    description="Filtre Solr CKAN optionnel, conservé tel quel dans la provenance."
                ),
                "sort": field(
                    "string", "Tri CKAN", default="score desc, metadata_modified desc",
                    max_length=120,
                ),
            }
        ),
    },
    "reliefweb": {
        "version": "1.0.0",
        "base_url": "https://api.reliefweb.int/v2/reports",
        "allowed_hosts": ["api.reliefweb.int", "reliefweb.int"],
        "secret_environment_variable": "RELIEFWEB_APPNAME",
        "documentation_evidence": [
            "https://apidoc.reliefweb.int/parameters",
            "https://apidoc.reliefweb.int/endpoints",
        ],
        "project_schema": project_schema(
            {
                "offset": field("integer", "Décalage", default=0, minimum=0, maximum=10000),
                "profile": field(
                    "string", "Profil de réponse", default="full",
                    enum=["minimal", "list", "full"],
                ),
                "preset": field("string", "Préréglage", default="latest", max_length=80),
                "sort": field(
                    "string", "Tri", default="date.created:desc", max_length=120
                ),
            }
        ),
    },
    "who-gho": {
        "version": "1.0.0",
        "base_url": "https://ghoapi.azureedge.net/api/Indicator",
        "allowed_hosts": ["ghoapi.azureedge.net"],
        "secret_environment_variable": None,
        "documentation_evidence": [
            "https://www.who.int/data/gho/info/gho-odata-api"
        ],
        "project_schema": project_schema(
            {
                "skip": field("integer", "Décalage OData", default=0, minimum=0, maximum=10000),
                "catalog_top": field(
                    "integer", "Taille du catalogue interrogé", default=100,
                    minimum=100, maximum=5000,
                ),
            }
        ),
    },
    "world-bank-health": {
        "version": "1.0.0",
        "base_url": "https://api.worldbank.org/v2/source/2/indicator",
        "allowed_hosts": ["api.worldbank.org"],
        "secret_environment_variable": None,
        "documentation_evidence": [
            "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures"
        ],
        "project_schema": project_schema(
            {
                "page": field("integer", "Page", default=1, minimum=1, maximum=10000),
                "catalog_page_size": field(
                    "integer", "Indicateurs chargés", default=20000,
                    minimum=100, maximum=50000,
                ),
                "language": field(
                    "string", "Langue", default="en", enum=["en", "fr", "es", "ar", "zh"]
                ),
            }
        ),
    },
    "unicef-sdmx": {
        "version": "1.0.0",
        "base_url": "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest",
        "allowed_hosts": ["sdmx.data.unicef.org"],
        "secret_environment_variable": None,
        "documentation_evidence": [
            "https://data.unicef.org/sdmx-api-documentation/",
            "https://sdmx.org/?page_id=5008",
        ],
        "project_schema": project_schema(
            {
                "agency": field(
                    "string", "Agence SDMX", default="all", pattern=r"^[A-Za-z0-9_.-]{1,80}$"
                ),
                "dataflow": field(
                    "string", "Flux SDMX", default="all", pattern=r"^[A-Za-z0-9_.-]{1,120}$"
                ),
                "version": field(
                    "string", "Version du flux", default="latest", pattern=r"^[A-Za-z0-9_.-]{1,40}$"
                ),
                "detail": field(
                    "string", "Détail structurel", default="full",
                    enum=["allstubs", "referencestubs", "referencepartial", "allcompletestubs", "full"],
                ),
                "references": field(
                    "string", "Références SDMX", default="none", max_length=80
                ),
            }
        ),
    },
    "un-sdg": {
        "version": "1.0.0",
        "base_url": "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List",
        "allowed_hosts": ["unstats.un.org"],
        "secret_environment_variable": None,
        "documentation_evidence": ["https://unstats.un.org/sdgapi/swagger/"],
        "project_schema": project_schema(),
    },
    "dhs": {
        "version": "1.0.0",
        "base_url": "https://api.dhsprogram.com/rest/dhs/indicators",
        "allowed_hosts": ["api.dhsprogram.com"],
        "secret_environment_variable": None,
        "documentation_evidence": ["https://api.dhsprogram.com/"],
        "project_schema": project_schema(
            {
                "page": field("integer", "Page", default=1, minimum=1, maximum=10000),
                "catalog_page_size": field(
                    "integer", "Indicateurs chargés", default=5000,
                    minimum=100, maximum=10000,
                ),
                "country_ids": field(
                    "array", "Pays DHS", default=[], max_length=100,
                    items=field("string", "Code pays", pattern=r"^[A-Za-z0-9_-]{1,20}$"),
                ),
                "indicator_ids": field(
                    "array", "Indicateurs DHS", default=[], max_length=100,
                    items=field("string", "Code indicateur", pattern=r"^[A-Za-z0-9_-]{1,80}$"),
                ),
                "survey_years": field(
                    "array", "Années d’enquête", default=[], max_length=100,
                    items=field("integer", "Année", minimum=1900, maximum=2100),
                ),
                "breakdown": field(
                    "string", "Ventilation", default="", max_length=80
                ),
            }
        ),
    },
}


def _defaults(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(definition["default"])
        for key, definition in schema.get("properties", {}).items()
        if "default" in definition
    }


def connector_definition(source_id: str) -> dict[str, Any]:
    try:
        definition = deepcopy(CONNECTORS[source_id])
    except KeyError as exc:
        raise ValueError(f"Source non interrogeable : {source_id}") from exc
    definition.update(
        {
            "id": source_id,
            "registry_version": REGISTRY_VERSION,
            "verified_at": VERIFIED_AT,
            "global_settings_schema": deepcopy(GLOBAL_SCHEMA),
            "global_defaults": _defaults(GLOBAL_SCHEMA),
            "project_defaults": _defaults(definition["project_schema"]),
        }
    )
    return definition


def enrich_source_catalog(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for source in catalog:
        item = deepcopy(source)
        item["registry_version"] = REGISTRY_VERSION
        item["verified_at"] = VERIFIED_AT
        if item["id"] in CONNECTORS:
            item.update(connector_definition(item["id"]))
        else:
            item.update(
                {
                    "version": "reference-1.0.0",
                    "allowed_hosts": [],
                    "secret_environment_variable": None,
                    "documentation_evidence": [item["documentation_url"]],
                    "global_settings_schema": deepcopy(GLOBAL_SCHEMA),
                    "global_defaults": _defaults(GLOBAL_SCHEMA),
                    "project_schema": None,
                    "project_defaults": None,
                }
            )
        enriched.append(item)
    return enriched


def _validate_scalar(name: str, value: Any, definition: dict[str, Any]) -> Any:
    value_type = definition.get("type")
    if value_type == "boolean":
        if type(value) is not bool:
            raise ValueError(f"{name} doit être booléen")
    elif value_type == "integer":
        if type(value) is not int:
            raise ValueError(f"{name} doit être un entier")
        if "minimum" in definition and value < definition["minimum"]:
            raise ValueError(f"{name} est inférieur au minimum autorisé")
        if "maximum" in definition and value > definition["maximum"]:
            raise ValueError(f"{name} dépasse le maximum autorisé")
    elif value_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"{name} doit être une chaîne")
        value = value.strip()
        if "minLength" in definition and len(value) < definition["minLength"]:
            raise ValueError(f"{name} est trop court")
        if "maxLength" in definition and len(value) > definition["maxLength"]:
            raise ValueError(f"{name} est trop long")
        if definition.get("pattern") and not re.fullmatch(definition["pattern"], value):
            raise ValueError(f"{name} ne respecte pas le format attendu")
    elif value_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"{name} doit être une liste")
        if "maxLength" in definition and len(value) > definition["maxLength"]:
            raise ValueError(f"{name} contient trop d’éléments")
        item_definition = definition.get("items", {})
        value = [_validate_scalar(f"{name}[{index}]", item, item_definition) for index, item in enumerate(value)]
        value = list(dict.fromkeys(value))
    else:
        raise ValueError(f"Type de schéma non pris en charge pour {name}")
    if "enum" in definition and value not in definition["enum"]:
        raise ValueError(f"{name} ne fait pas partie des valeurs autorisées")
    return value


def validate_values(
    source_id: str,
    values: dict[str, Any],
    *,
    scope: str,
    partial: bool = False,
) -> dict[str, Any]:
    if scope == "global":
        schema = deepcopy(GLOBAL_SCHEMA)
    else:
        schema = connector_definition(source_id)["project_schema"]
    if not isinstance(values, dict):
        raise ValueError("Les paramètres doivent former un objet JSON")
    unknown = sorted(set(values) - set(schema["properties"]))
    if unknown:
        raise ValueError(f"Paramètres inconnus : {', '.join(unknown)}")
    result = {} if partial else _defaults(schema)
    for name, value in values.items():
        result[name] = _validate_scalar(name, value, schema["properties"][name])
    if not partial:
        missing = [name for name in schema.get("required", []) if name not in result]
        if missing:
            raise ValueError(f"Paramètres obligatoires absents : {', '.join(missing)}")
    return result


def merge_values(source_id: str, stored: dict[str, Any] | None, *, scope: str) -> dict[str, Any]:
    return validate_values(source_id, stored or {}, scope=scope, partial=False)


def request_preview(source_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    values = validate_values(source_id, parameters, scope="project")
    definition = connector_definition(source_id)
    url = definition["base_url"]
    query: dict[str, Any] = {}
    if source_id == "hdx":
        query = {"q": values["query"], "rows": values["result_limit"], "start": values["start"], "sort": values["sort"]}
        if values["fq"]:
            query["fq"] = values["fq"]
    elif source_id == "reliefweb":
        query = {
            "appname": "<RELIEFWEB_APPNAME>",
            "query[value]": values["query"],
            "limit": values["result_limit"],
            "offset": values["offset"],
            "profile": values["profile"],
            "preset": values["preset"],
            "sort[]": values["sort"],
        }
    elif source_id == "who-gho":
        escaped = values["query"].replace("'", "''")
        query = {
            "$filter": f"contains(IndicatorName,'{escaped}') or contains(IndicatorCode,'{escaped}')",
            "$top": max(values["catalog_top"], values["result_limit"]),
            "$skip": values["skip"],
            "$format": "json",
        }
    elif source_id == "world-bank-health":
        query = {"format": "json", "page": values["page"], "per_page": values["catalog_page_size"], "language": values["language"]}
    elif source_id == "unicef-sdmx":
        url = f"{url}/dataflow/{values['agency']}/{values['dataflow']}/{values['version']}/"
        query = {"format": "sdmx-json", "detail": values["detail"], "references": values["references"]}
    elif source_id == "un-sdg":
        query = {}
    elif source_id == "dhs":
        query = {"f": "json", "page": values["page"], "perpage": values["catalog_page_size"]}
        if values["country_ids"]:
            query["countryIds"] = ",".join(values["country_ids"])
        if values["indicator_ids"]:
            query["indicatorIds"] = ",".join(values["indicator_ids"])
        if values["survey_years"]:
            query["surveyYears"] = ",".join(map(str, values["survey_years"]))
        if values["breakdown"]:
            query["breakdown"] = values["breakdown"]
    encoded = urlencode(query, doseq=True, safe="<>")
    display_url = f"{url}?{encoded}" if encoded else url
    return {
        "method": "GET",
        "url": url,
        "query_parameters": query,
        "display_url": display_url,
        "curl": f'curl --fail --silent --show-error "{display_url}"',
        "secret_environment_variable": definition["secret_environment_variable"],
        "verified_at": definition["verified_at"],
        "documentation_evidence": definition["documentation_evidence"],
    }
