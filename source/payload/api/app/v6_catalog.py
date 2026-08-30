from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping


CATALOG_SCHEMA_VERSION = "6.0.0"
CAPABILITIES = ("discover", "describe", "search", "preview", "acquire", "refresh", "provenance")
ENDPOINT_STATES = (
    "inventoried",
    "contract_imported",
    "adapter_implemented",
    "tests_validated",
    "active_global",
    "active_project",
    "suspended",
    "obsolete",
)
GLOBAL_ENDPOINT_STATES = (
    "inventoried",
    "contract_imported",
    "adapter_implemented",
    "tests_validated",
    "active_global",
    "suspended",
    "obsolete",
)
SUPPORT_LEVELS = ("native", "hdp_equivalent", "partial", "unavailable")
STALE_MODES = ("fixed_duration", "frequency_multiple", "frequency_with_project_cap", "manual")
PROJECT_STALE_POLICIES = ("block", "allow_stale", "stale_if_error", "manual")
SECRET_NAME = re.compile(r"(?:token|secret|password|api[_-]?key|authorization|cookie)", re.IGNORECASE)


class CatalogValidationError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def contract_sha256(contract: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()


def validate_endpoint_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    required = {"source_id", "api_version", "endpoint_id", "method", "path", "state", "parameters", "response_fields"}
    missing = sorted(required - set(contract))
    if missing:
        raise CatalogValidationError(f"Champs de contrat absents: {missing}")
    unknown = set(contract) - (required | {"documentation_url", "summary", "authentication", "formats", "limits", "cache", "allowed_hosts"})
    if unknown:
        raise CatalogValidationError(f"Champs de contrat inconnus: {sorted(unknown)}")
    source_id = contract["source_id"]
    endpoint_id = contract["endpoint_id"]
    if not isinstance(source_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", source_id):
        raise CatalogValidationError("source_id invalide")
    if not isinstance(endpoint_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", endpoint_id):
        raise CatalogValidationError("endpoint_id invalide")
    method = str(contract["method"]).upper()
    if method not in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"}:
        raise CatalogValidationError("méthode HTTP invalide")
    path = contract["path"]
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise CatalogValidationError("chemin d'endpoint invalide")
    state = contract["state"]
    if state not in ENDPOINT_STATES:
        raise CatalogValidationError("état d'endpoint invalide")
    parameters = contract["parameters"]
    response_fields = contract["response_fields"]
    if not isinstance(parameters, list) or len(parameters) > 2000:
        raise CatalogValidationError("liste de paramètres invalide")
    if not isinstance(response_fields, list) or len(response_fields) > 20_000:
        raise CatalogValidationError("liste de champs de réponse invalide")
    normalized_parameters = [_validate_parameter(item, index) for index, item in enumerate(parameters)]
    normalized_fields = [_validate_response_field(item, index) for index, item in enumerate(response_fields)]
    authentication = contract.get("authentication", {"type": "none"})
    if not isinstance(authentication, Mapping):
        raise CatalogValidationError("contrat d'authentification invalide")
    serialized_auth = canonical_json(authentication)
    if SECRET_NAME.search(serialized_auth) and any(
        key in authentication for key in ("value", "token", "secret", "password", "api_key")
    ):
        raise CatalogValidationError("un contrat ne peut pas contenir une valeur secrète")
    allowed_hosts = contract.get("allowed_hosts", [])
    if not isinstance(allowed_hosts, list) or any(
        not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host) for host in allowed_hosts
    ):
        raise CatalogValidationError("liste d'hôtes autorisés invalide")
    normalized = dict(contract)
    normalized.update(
        {
            "method": method,
            "parameters": normalized_parameters,
            "response_fields": normalized_fields,
            "authentication": dict(authentication),
            "allowed_hosts": sorted(set(allowed_hosts)),
        }
    )
    normalized["contract_sha256"] = contract_sha256(normalized)
    normalized["schema_version"] = CATALOG_SCHEMA_VERSION
    return normalized


def _validate_parameter(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CatalogValidationError(f"parameters[{index}]: objet attendu")
    required = {"name", "location", "schema"}
    if not required <= set(value):
        raise CatalogValidationError(f"parameters[{index}]: name, location et schema requis")
    unknown = set(value) - (required | {"required", "description", "documented", "supported", "sensitive", "dependencies"})
    if unknown:
        raise CatalogValidationError(f"parameters[{index}]: champs inconnus {sorted(unknown)}")
    name = value["name"]
    location = value["location"]
    if not isinstance(name, str) or not 1 <= len(name) <= 160:
        raise CatalogValidationError(f"parameters[{index}].name invalide")
    if location not in {"path", "query", "header", "cookie", "body"}:
        raise CatalogValidationError(f"parameters[{index}].location invalide")
    if not isinstance(value["schema"], Mapping):
        raise CatalogValidationError(f"parameters[{index}].schema invalide")
    if value.get("sensitive") and "default" in value["schema"]:
        raise CatalogValidationError(f"parameters[{index}]: un paramètre sensible ne peut pas avoir de valeur par défaut")
    return {
        "name": name,
        "location": location,
        "schema": dict(value["schema"]),
        "required": bool(value.get("required", False)),
        "description": str(value.get("description", ""))[:5000],
        "documented": bool(value.get("documented", True)),
        "supported": bool(value.get("supported", False)),
        "sensitive": bool(value.get("sensitive", False)),
        "dependencies": list(value.get("dependencies", [])),
    }


def _validate_response_field(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CatalogValidationError(f"response_fields[{index}]: objet attendu")
    required = {"path", "schema"}
    if not required <= set(value):
        raise CatalogValidationError(f"response_fields[{index}]: path et schema requis")
    unknown = set(value) - (required | {"description", "documented", "observed", "nullable", "cardinality", "first_seen_version"})
    if unknown:
        raise CatalogValidationError(f"response_fields[{index}]: champs inconnus {sorted(unknown)}")
    path = value["path"]
    if not isinstance(path, str) or not 1 <= len(path) <= 500:
        raise CatalogValidationError(f"response_fields[{index}].path invalide")
    if not isinstance(value["schema"], Mapping):
        raise CatalogValidationError(f"response_fields[{index}].schema invalide")
    return {
        "path": path,
        "schema": dict(value["schema"]),
        "description": str(value.get("description", ""))[:5000],
        "documented": bool(value.get("documented", False)),
        "observed": bool(value.get("observed", False)),
        "nullable": bool(value.get("nullable", True)),
        "cardinality": value.get("cardinality"),
        "first_seen_version": value.get("first_seen_version"),
    }


def contract_diff(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    old = validate_endpoint_contract(previous)
    new = validate_endpoint_contract(current)
    old_parameters = {(item["location"], item["name"]): item for item in old["parameters"]}
    new_parameters = {(item["location"], item["name"]): item for item in new["parameters"]}
    old_fields = {item["path"]: item for item in old["response_fields"]}
    new_fields = {item["path"]: item for item in new["response_fields"]}
    parameter_changes = _mapping_diff(old_parameters, new_parameters)
    response_changes = _mapping_diff(old_fields, new_fields)
    breaking = bool(parameter_changes["removed"] or response_changes["removed"])
    for change in parameter_changes["changed"]:
        before, after = change["before"], change["after"]
        breaking = breaking or before["schema"].get("type") != after["schema"].get("type") or (
            not before["required"] and after["required"]
        )
    for change in response_changes["changed"]:
        breaking = breaking or change["before"]["schema"].get("type") != change["after"]["schema"].get("type")
    return {
        "previous_sha256": old["contract_sha256"],
        "current_sha256": new["contract_sha256"],
        "parameters": parameter_changes,
        "response_fields": response_changes,
        "breaking": breaking,
        "activation_requires_validation": old["contract_sha256"] != new["contract_sha256"],
    }


def _mapping_diff(previous: Mapping[Any, Any], current: Mapping[Any, Any]) -> dict[str, Any]:
    previous_keys, current_keys = set(previous), set(current)
    changed = [
        {"key": list(key) if isinstance(key, tuple) else key, "before": previous[key], "after": current[key]}
        for key in sorted(previous_keys & current_keys, key=str)
        if canonical_json(previous[key]) != canonical_json(current[key])
    ]
    return {
        "added": [list(key) if isinstance(key, tuple) else key for key in sorted(current_keys - previous_keys, key=str)],
        "removed": [list(key) if isinstance(key, tuple) else key for key in sorted(previous_keys - current_keys, key=str)],
        "changed": changed,
    }


def validate_capability_matrix(capabilities: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(capabilities) - set(CAPABILITIES)
    if unknown:
        raise CatalogValidationError(f"capacités inconnues: {sorted(unknown)}")
    normalized: dict[str, Any] = {}
    for capability in CAPABILITIES:
        item = capabilities.get(capability, {"support": "unavailable", "state": "inventoried"})
        if not isinstance(item, Mapping):
            raise CatalogValidationError(f"{capability}: objet attendu")
        support, state = item.get("support"), item.get("state")
        if support not in SUPPORT_LEVELS or state not in ENDPOINT_STATES:
            raise CatalogValidationError(f"{capability}: support ou état invalide")
        normalized[capability] = {
            "support": support,
            "state": state,
            "endpoint_ids": sorted(set(item.get("endpoint_ids", []))),
            "equivalent_recipe": item.get("equivalent_recipe"),
            "tested_at": item.get("tested_at"),
        }
    return normalized


def validate_endpoint_transition(current: str, target: str) -> tuple[str, str]:
    if current not in GLOBAL_ENDPOINT_STATES or target not in GLOBAL_ENDPOINT_STATES:
        raise CatalogValidationError("état global d'endpoint invalide")
    if current == target:
        return current, "unchanged"
    if current == "obsolete":
        raise CatalogValidationError("un endpoint obsolète ne peut pas être réactivé")
    if target == "obsolete":
        return target, "terminal"
    if target == "suspended" and current not in {"inventoried", "obsolete"}:
        return target, "suspended"
    if current == "suspended":
        if target not in {"contract_imported", "adapter_implemented", "tests_validated", "active_global"}:
            raise CatalogValidationError("état de reprise invalide")
        return target, "resumed_with_validation"
    order = {
        "inventoried": 0,
        "contract_imported": 1,
        "adapter_implemented": 2,
        "tests_validated": 3,
        "active_global": 4,
    }
    if target not in order or current not in order or order[target] != order[current] + 1:
        raise CatalogValidationError("l'activation doit progresser d'un seul état validé à la fois")
    return target, "progressed"


def _without_secrets(value: Any, path: str = "parameters") -> Any:
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if SECRET_NAME.search(str(key)):
                raise CatalogValidationError(f"{path}.{key}: un secret ne doit pas entrer dans la clé de cache")
            result[str(key)] = _without_secrets(item, f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_without_secrets(item, f"{path}[]") for item in value]
    return value


def canonical_cache_key(
    *,
    source_id: str,
    api_version: str,
    endpoint_id: str,
    parameters: Mapping[str, Any],
    output_format: str,
    connector_version: str,
    transformation_version: str,
) -> tuple[str, dict[str, Any]]:
    descriptor = {
        "source_id": source_id,
        "api_version": api_version,
        "endpoint_id": endpoint_id,
        "parameters": _without_secrets(parameters),
        "output_format": output_format.casefold(),
        "connector_version": connector_version,
        "transformation_version": transformation_version,
    }
    return hashlib.sha256(canonical_json(descriptor).encode("utf-8")).hexdigest(), descriptor


@dataclass(frozen=True)
class FreshnessPolicy:
    project_policy: str = "stale_if_error"
    max_stale_mode: str = "manual"
    fixed_duration_seconds: int | None = None
    frequency_multiple: float | None = None
    project_cap_seconds: int | None = None

    def validate(self) -> "FreshnessPolicy":
        if self.project_policy not in PROJECT_STALE_POLICIES:
            raise CatalogValidationError("politique de données périmées invalide")
        if self.max_stale_mode not in STALE_MODES:
            raise CatalogValidationError("mode d'ancienneté maximale invalide")
        if self.max_stale_mode == "fixed_duration" and not _positive_int(self.fixed_duration_seconds):
            raise CatalogValidationError("fixed_duration_seconds positif requis")
        if self.max_stale_mode in {"frequency_multiple", "frequency_with_project_cap"} and not _positive_number(self.frequency_multiple):
            raise CatalogValidationError("frequency_multiple positif requis")
        if self.max_stale_mode == "frequency_with_project_cap" and not _positive_int(self.project_cap_seconds):
            raise CatalogValidationError("project_cap_seconds positif requis")
        return self


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and value > 0


def maximum_stale_seconds(policy: FreshnessPolicy, source_frequency_seconds: int | None) -> int | None:
    policy.validate()
    if policy.max_stale_mode == "manual":
        return None
    if policy.max_stale_mode == "fixed_duration":
        return int(policy.fixed_duration_seconds or 0)
    if not _positive_int(source_frequency_seconds):
        raise CatalogValidationError("fréquence source positive requise pour ce mode")
    calculated = int(source_frequency_seconds * float(policy.frequency_multiple or 0))
    if policy.max_stale_mode == "frequency_with_project_cap":
        return min(calculated, int(policy.project_cap_seconds or 0))
    return calculated


def cache_decision(
    *,
    cached_at: datetime,
    next_validation_at: datetime,
    now: datetime | None,
    source_failed: bool,
    policy: FreshnessPolicy,
    source_frequency_seconds: int | None = None,
) -> dict[str, Any]:
    policy.validate()
    observed_at = now or datetime.now(UTC)
    observed_at = observed_at.replace(tzinfo=UTC) if observed_at.tzinfo is None else observed_at.astimezone(UTC)
    cached_at = cached_at.replace(tzinfo=UTC) if cached_at.tzinfo is None else cached_at.astimezone(UTC)
    next_validation_at = (
        next_validation_at.replace(tzinfo=UTC)
        if next_validation_at.tzinfo is None
        else next_validation_at.astimezone(UTC)
    )
    if observed_at <= next_validation_at:
        return {"decision": "use_fresh", "degraded": False, "age_seconds": int((observed_at - cached_at).total_seconds())}
    age_seconds = max(0, int((observed_at - cached_at).total_seconds()))
    maximum = maximum_stale_seconds(policy, source_frequency_seconds)
    admissible = maximum is None or age_seconds <= maximum
    if policy.max_stale_mode == "manual":
        return {
            "decision": "pending_approval",
            "degraded": True,
            "age_seconds": age_seconds,
            "max_stale_seconds": None,
            "reason": "manual_maximum_stale_age",
        }
    if policy.project_policy == "block":
        decision = "block"
    elif policy.project_policy == "manual":
        decision = "pending_approval"
    elif policy.project_policy == "allow_stale":
        decision = "use_stale" if admissible else "block"
    else:
        if not source_failed:
            decision = "refresh_required"
        else:
            decision = "use_stale" if admissible else "block"
    return {
        "decision": decision,
        "degraded": decision == "use_stale",
        "age_seconds": age_seconds,
        "max_stale_seconds": maximum,
        "source_failed": source_failed,
    }


def freshness_deadline(
    *,
    fetched_at: datetime,
    declared_frequency_seconds: int | None,
    source_ttl_seconds: int | None,
    forced: bool = False,
) -> datetime:
    fetched_at = fetched_at.replace(tzinfo=UTC) if fetched_at.tzinfo is None else fetched_at.astimezone(UTC)
    if forced:
        return fetched_at
    candidates = [value for value in (declared_frequency_seconds, source_ttl_seconds) if _positive_int(value)]
    if not candidates:
        raise CatalogValidationError("une fréquence déclarée ou une durée source est requise")
    return fetched_at + timedelta(seconds=min(candidates))


def preserve_unmapped_fields(raw: Mapping[str, Any], mapped_paths: set[str]) -> dict[str, Any]:
    unmapped: dict[str, Any] = {}

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
            return
        generalized = re.sub(r"\[\d+\]", "[]", path)
        if generalized not in mapped_paths:
            unmapped[path] = value

    walk(raw, "")
    return unmapped
