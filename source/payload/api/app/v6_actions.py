from __future__ import annotations

import re
import uuid
from typing import Any, Mapping


ACTION_POLICY: dict[str, dict[str, str]] = {
    "notification": {"risk": "safe", "control": "automatic_within_limits"},
    "classification": {"risk": "safe", "control": "automatic_within_limits"},
    "hdp_task": {"risk": "safe", "control": "automatic_within_limits"},
    "data_search": {"risk": "safe", "control": "automatic_within_limits"},
    "data_refresh": {"risk": "safe", "control": "automatic_within_limits"},
    "email_draft": {"risk": "preparatory", "control": "draft_only"},
    "spip_draft": {"risk": "preparatory", "control": "draft_only"},
    "python_script": {"risk": "external", "control": "manual_approval"},
    "r_script": {"risk": "external", "control": "manual_approval"},
    "webhook": {"risk": "external", "control": "manual_approval"},
}

ESTIMATE_KEYS = ("estimated_requests", "estimated_bytes", "estimated_duration_seconds")
SECRET_NAME = re.compile(r"(?:password|secret|token|api[_-]?key|authorization|cookie)", re.IGNORECASE)
SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


class ActionValidationError(ValueError):
    pass


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(SECRET_NAME.search(str(key)) or _contains_secret_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_secret_key(item) for item in value)
    return False


def _estimate(container: Mapping[str, Any], key: str, path: str) -> int:
    value = container.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise ActionValidationError(f"{path}.{key}: entier positif ou nul attendu")
    return value


def _require_uuid(parameters: Mapping[str, Any], key: str, path: str) -> None:
    try:
        uuid.UUID(str(parameters.get(key, "")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ActionValidationError(f"{path}.{key}: UUID de version requis") from exc


def _require_sha256(parameters: Mapping[str, Any], key: str, path: str) -> None:
    value = parameters.get(key)
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ActionValidationError(f"{path}.{key}: empreinte SHA-256 requise")


def validate_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(actions) > 50:
        raise ActionValidationError("Une règle ne peut pas contenir plus de 50 actions")
    normalized: list[dict[str, Any]] = []
    for index, action in enumerate(actions):
        path = f"actions[{index}]"
        if not isinstance(action, dict):
            raise ActionValidationError(f"{path}: objet attendu")
        unknown = set(action) - {"type", "parameters", "limits"}
        if unknown:
            raise ActionValidationError(f"{path}: champs inconnus: {sorted(unknown)}")
        action_type = action.get("type")
        if action_type not in ACTION_POLICY:
            raise ActionValidationError(f"{path}.type: type d'action invalide")
        parameters = action.get("parameters", {})
        limits = action.get("limits", {})
        if not isinstance(parameters, Mapping) or not isinstance(limits, Mapping):
            raise ActionValidationError(f"{path}: parameters et limits doivent être des objets")
        if _contains_secret_key(parameters) or _contains_secret_key(limits):
            raise ActionValidationError(f"{path}: une règle ne doit contenir aucun secret")
        for key in ESTIMATE_KEYS:
            _estimate(parameters, key, f"{path}.parameters")
            _estimate(limits, key, f"{path}.limits")
        if action_type in {"python_script", "r_script"}:
            _require_uuid(parameters, "script_version_id", f"{path}.parameters")
            _require_sha256(parameters, "script_sha256", f"{path}.parameters")
        if action_type == "webhook":
            _require_uuid(parameters, "webhook_version_id", f"{path}.parameters")
            _require_sha256(parameters, "configuration_sha256", f"{path}.parameters")
        normalized.append({"type": action_type, "parameters": dict(parameters), "limits": dict(limits)})
    return normalized


def action_status(
    action: Mapping[str, Any],
    request_limit: int,
    download_limit: int,
    duration_limit: int,
) -> tuple[str, str]:
    normalized = validate_actions([dict(action)])[0]
    policy = ACTION_POLICY[normalized["type"]]
    if policy["risk"] == "external":
        return "pending_approval", "external_action_requires_manual_approval"
    limits = normalized["limits"]
    parameters = normalized["parameters"]
    estimates = {
        key: max(_estimate(limits, key, "limits"), _estimate(parameters, key, "parameters"))
        for key in ESTIMATE_KEYS
    }
    if (
        estimates["estimated_requests"] > request_limit
        or estimates["estimated_bytes"] > download_limit
        or estimates["estimated_duration_seconds"] > duration_limit
    ):
        return "pending_approval", "automatic_limit_exceeded"
    return "queued", policy["control"]
