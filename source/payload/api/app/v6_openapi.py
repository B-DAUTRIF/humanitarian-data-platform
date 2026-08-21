from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any, Mapping
from urllib.parse import urlparse

from .v6_catalog import canonical_json


HTTP_METHODS = ("get", "head", "post", "put", "patch", "delete", "options", "trace")
SENSITIVE_NAME = re.compile(r"(?:token|secret|password|api[_-]?key|authorization|cookie)", re.IGNORECASE)


class OpenApiInventoryError(ValueError):
    pass


def document_sha256(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def _json_pointer(document: Mapping[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise OpenApiInventoryError("seules les références OpenAPI locales sont admises")
    value: Any = document
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or part not in value:
            raise OpenApiInventoryError(f"référence OpenAPI introuvable: {reference}")
        value = value[part]
    return value


def _resolve(
    document: Mapping[str, Any],
    value: Any,
    *,
    references: tuple[str, ...] = (),
    depth: int = 0,
) -> Any:
    if depth > 40:
        raise OpenApiInventoryError("profondeur maximale de résolution OpenAPI dépassée")
    if not isinstance(value, Mapping) or "$ref" not in value:
        return value
    reference = value["$ref"]
    if not isinstance(reference, str):
        raise OpenApiInventoryError("référence OpenAPI invalide")
    if reference in references:
        return {"type": "object", "x-hdp-recursive-ref": reference}
    target = _json_pointer(document, reference)
    if not isinstance(target, Mapping):
        raise OpenApiInventoryError(f"la référence {reference} ne pointe pas vers un objet")
    merged = deepcopy(dict(target))
    merged.update({key: deepcopy(item) for key, item in value.items() if key != "$ref"})
    return _resolve(document, merged, references=(*references, reference), depth=depth + 1)


def _schema(document: Mapping[str, Any], value: Any) -> dict[str, Any]:
    resolved = _resolve(document, value)
    if not isinstance(resolved, Mapping):
        return {}
    allowed = {
        "type", "format", "enum", "const", "default", "example", "examples", "minimum",
        "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength", "maxLength",
        "pattern", "minItems", "maxItems", "uniqueItems", "multipleOf", "nullable",
        "readOnly", "writeOnly", "deprecated", "description", "title", "oneOf", "anyOf",
        "allOf", "not", "properties", "required", "items", "additionalProperties",
        "x-hdp-recursive-ref",
    }
    return {key: deepcopy(item) for key, item in resolved.items() if key in allowed}


def _response_fields(
    document: Mapping[str, Any],
    schema: Any,
    *,
    prefix: str,
    required: bool = False,
    depth: int = 0,
    references: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    if depth > 30:
        return []
    if isinstance(schema, Mapping) and "$ref" in schema:
        reference = schema.get("$ref")
        if reference in references:
            return [
                {
                    "path": prefix,
                    "schema": {"type": "object", "x-hdp-recursive-ref": reference},
                    "documented": True,
                    "observed": False,
                    "nullable": True,
                    "cardinality": "one",
                }
            ]
        resolved = _resolve(document, schema, references=references, depth=depth)
        return _response_fields(
            document,
            resolved,
            prefix=prefix,
            required=required,
            depth=depth + 1,
            references=(*references, str(reference)),
        )
    if not isinstance(schema, Mapping):
        return []
    fields: list[dict[str, Any]] = []
    combinations = [schema.get(name) for name in ("allOf", "oneOf", "anyOf") if schema.get(name)]
    for variants in combinations:
        for index, variant in enumerate(variants):
            fields.extend(
                _response_fields(
                    document,
                    variant,
                    prefix=prefix,
                    required=required,
                    depth=depth + 1,
                    references=references,
                )
            )
    schema_type = schema.get("type")
    if schema_type == "array" or "items" in schema:
        array_path = f"{prefix}[]"
        fields.append(
            {
                "path": array_path,
                "schema": _schema(document, schema),
                "description": str(schema.get("description", ""))[:5000],
                "documented": True,
                "observed": False,
                "nullable": bool(schema.get("nullable", not required)),
                "cardinality": "many",
            }
        )
        fields.extend(
            _response_fields(
                document,
                schema.get("items", {}),
                prefix=array_path,
                required=True,
                depth=depth + 1,
                references=references,
            )
        )
        return fields
    properties = schema.get("properties", {})
    if isinstance(properties, Mapping):
        required_properties = set(schema.get("required", []))
        for name, property_schema in properties.items():
            property_path = f"{prefix}.{name}" if prefix else str(name)
            resolved = _resolve(document, property_schema)
            normalized = _schema(document, resolved)
            property_required = name in required_properties
            fields.append(
                {
                    "path": property_path,
                    "schema": normalized,
                    "description": str(normalized.get("description", ""))[:5000],
                    "documented": True,
                    "observed": False,
                    "nullable": bool(normalized.get("nullable", not property_required)),
                    "cardinality": "many" if normalized.get("type") == "array" else "one",
                }
            )
            if isinstance(resolved, Mapping) and (
                resolved.get("properties") or resolved.get("items") or resolved.get("allOf")
                or resolved.get("oneOf") or resolved.get("anyOf")
            ):
                fields.extend(
                    _response_fields(
                        document,
                        resolved,
                        prefix=property_path,
                        required=property_required,
                        depth=depth + 1,
                        references=references,
                    )
                )
    return fields


def _parameter(document: Mapping[str, Any], value: Any) -> dict[str, Any]:
    parameter = _resolve(document, value)
    if not isinstance(parameter, Mapping):
        raise OpenApiInventoryError("paramètre OpenAPI invalide")
    name, location = parameter.get("name"), parameter.get("in")
    if not isinstance(name, str) or location not in {"path", "query", "header", "cookie", "body"}:
        raise OpenApiInventoryError("nom ou emplacement de paramètre OpenAPI invalide")
    schema = _schema(document, parameter.get("schema", {}))
    if not schema and isinstance(parameter.get("content"), Mapping):
        media = next(iter(parameter["content"].values()), {})
        schema = _schema(document, media.get("schema", {}) if isinstance(media, Mapping) else {})
    sensitive = bool(SENSITIVE_NAME.search(name))
    if sensitive:
        schema.pop("default", None)
        schema.pop("example", None)
        schema.pop("examples", None)
    return {
        "name": name,
        "location": location,
        "schema": schema,
        "required": bool(parameter.get("required", location == "path")),
        "description": str(parameter.get("description", ""))[:5000],
        "documented": True,
        "supported": False,
        "sensitive": sensitive,
        "dependencies": [],
    }


def _request_body_parameters(document: Mapping[str, Any], operation: Mapping[str, Any]) -> list[dict[str, Any]]:
    request_body = operation.get("requestBody")
    if not request_body:
        return []
    body = _resolve(document, request_body)
    if not isinstance(body, Mapping):
        raise OpenApiInventoryError("corps de requête OpenAPI invalide")
    content = body.get("content", {})
    if not isinstance(content, Mapping):
        raise OpenApiInventoryError("content de requestBody invalide")
    parameters: list[dict[str, Any]] = []
    for media_type, media in content.items():
        schema = _schema(document, media.get("schema", {}) if isinstance(media, Mapping) else {})
        parameters.append(
            {
                "name": f"body:{media_type}",
                "location": "body",
                "schema": schema,
                "required": bool(body.get("required", False)),
                "description": str(body.get("description", ""))[:5000],
                "documented": True,
                "supported": False,
                "sensitive": False,
                "dependencies": [f"content-type={media_type}"],
            }
        )
    return parameters


def _authentication(document: Mapping[str, Any], operation: Mapping[str, Any]) -> dict[str, Any]:
    requirements = operation.get("security", document.get("security", []))
    schemes = document.get("components", {}).get("securitySchemes", {}) if isinstance(document.get("components"), Mapping) else {}
    if "swagger" in document:
        schemes = document.get("securityDefinitions", {})
    public = requirements == []
    profiles = []
    for requirement in requirements or []:
        if not isinstance(requirement, Mapping):
            continue
        for name, scopes in requirement.items():
            definition = _resolve(document, schemes.get(name, {})) if isinstance(schemes, Mapping) else {}
            profiles.append(
                {
                    "name": name,
                    "type": definition.get("type", "unknown") if isinstance(definition, Mapping) else "unknown",
                    "in": definition.get("in") if isinstance(definition, Mapping) else None,
                    "scheme": definition.get("scheme") if isinstance(definition, Mapping) else None,
                    "scopes": list(scopes) if isinstance(scopes, list) else [],
                }
            )
    return {"type": "none" if public or not profiles else "documented", "profiles": profiles}


def _allowed_hosts(document: Mapping[str, Any]) -> list[str]:
    hosts: set[str] = set()
    for server in document.get("servers", []) if isinstance(document.get("servers"), list) else []:
        if isinstance(server, Mapping) and isinstance(server.get("url"), str):
            hostname = urlparse(server["url"].replace("{", "").replace("}", "")).hostname
            if hostname:
                hosts.add(hostname)
    if isinstance(document.get("host"), str):
        hosts.add(document["host"].split(":", 1)[0])
    return sorted(hosts)


def inventory_openapi_document(
    document: Mapping[str, Any],
    *,
    source_id: str,
    api_version: str,
    documentation_url: str,
) -> list[dict[str, Any]]:
    if not isinstance(document, Mapping) or not isinstance(document.get("paths"), Mapping):
        raise OpenApiInventoryError("document OpenAPI/Swagger sans objet paths")
    if not (document.get("openapi") or document.get("swagger")):
        raise OpenApiInventoryError("version OpenAPI/Swagger absente")
    paths = document["paths"]
    if len(paths) > 10_000:
        raise OpenApiInventoryError("document OpenAPI trop volumineux")
    hosts = _allowed_hosts(document)
    base_path = str(document.get("basePath", "")).rstrip("/") if "swagger" in document else ""
    contracts: list[dict[str, Any]] = []
    for raw_path, raw_path_item in paths.items():
        if not isinstance(raw_path, str) or not raw_path.startswith("/"):
            raise OpenApiInventoryError("chemin OpenAPI invalide")
        path_item = _resolve(document, raw_path_item)
        if not isinstance(path_item, Mapping):
            continue
        inherited_parameters = path_item.get("parameters", [])
        if not isinstance(inherited_parameters, list):
            raise OpenApiInventoryError(f"parameters invalide pour {raw_path}")
        for method in HTTP_METHODS:
            if method not in path_item:
                continue
            operation = _resolve(document, path_item[method])
            if not isinstance(operation, Mapping):
                raise OpenApiInventoryError(f"opération invalide: {method.upper()} {raw_path}")
            operation_parameters = operation.get("parameters", [])
            if not isinstance(operation_parameters, list):
                raise OpenApiInventoryError(f"parameters invalide: {method.upper()} {raw_path}")
            raw_parameters = [*inherited_parameters, *operation_parameters]
            parameters = [_parameter(document, item) for item in raw_parameters]
            parameters.extend(_request_body_parameters(document, operation))
            deduplicated_parameters: dict[tuple[str, str], dict[str, Any]] = {}
            for parameter in parameters:
                deduplicated_parameters[(parameter["location"], parameter["name"])] = parameter
            response_fields: dict[str, dict[str, Any]] = {}
            formats: set[str] = set(document.get("produces", [])) if isinstance(document.get("produces"), list) else set()
            responses = operation.get("responses", {})
            if not isinstance(responses, Mapping):
                raise OpenApiInventoryError(f"responses invalide: {method.upper()} {raw_path}")
            for status, response_value in responses.items():
                response = _resolve(document, response_value)
                if not isinstance(response, Mapping):
                    continue
                schemas: list[tuple[str, Any]] = []
                if "schema" in response:
                    schemas.append(("default", response["schema"]))
                content = response.get("content", {})
                if isinstance(content, Mapping):
                    for media_type, media in content.items():
                        formats.add(str(media_type))
                        if isinstance(media, Mapping) and "schema" in media:
                            schemas.append((str(media_type), media["schema"]))
                for media_type, schema in schemas:
                    prefix = f"responses.{status}.{media_type}"
                    for field in _response_fields(document, schema, prefix=prefix):
                        response_fields[field["path"]] = field
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", operation_id):
                identity_hash = hashlib.sha256(f"{method}:{raw_path}".encode("utf-8")).hexdigest()[:16]
                operation_id = f"{method.upper()}:{identity_hash}"
            contracts.append(
                {
                    "source_id": source_id,
                    "api_version": api_version,
                    "endpoint_id": operation_id,
                    "method": method.upper(),
                    "path": f"{base_path}{raw_path}" or "/",
                    "state": "inventoried",
                    "documentation_url": documentation_url,
                    "summary": str(operation.get("summary") or operation.get("description") or "")[:5000],
                    "authentication": _authentication(document, operation),
                    "formats": sorted(formats),
                    "limits": deepcopy(operation.get("x-rate-limit", document.get("x-rate-limit", {}))),
                    "cache": deepcopy(operation.get("x-cache", document.get("x-cache", {}))),
                    "allowed_hosts": hosts,
                    "parameters": list(deduplicated_parameters.values()),
                    "response_fields": list(response_fields.values()),
                }
            )
    if not contracts:
        raise OpenApiInventoryError("aucune opération HTTP documentée")
    return contracts
