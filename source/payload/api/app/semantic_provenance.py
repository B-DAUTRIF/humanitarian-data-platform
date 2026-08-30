from __future__ import annotations

"""Deterministic, secret-free fingerprints for semantic queries and snapshots."""

import hashlib
import json
from typing import Any

SECRET_KEYS = {"appname", "app_identifier", "authorization", "token", "password", "secret"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): (
                "<redacted>"
                if str(key).casefold() in SECRET_KEYS
                else _redact(item)
            )
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        _redact(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def query_fingerprint(plan_without_fingerprint: dict[str, Any]) -> str:
    """Fingerprint every execution-significant semantic input, never credentials."""
    material = {
        "schema_version": plan_without_fingerprint.get("schema_version"),
        "contract_version": plan_without_fingerprint.get("contract_version"),
        "intent": plan_without_fingerprint.get("intent"),
        "project_context": plan_without_fingerprint.get("project_context"),
        "routes": [
            {
                "source": route.get("source"),
                "operation": route.get("operation"),
                "executable": route.get("executable"),
                "project_enabled": route.get("project_enabled"),
                "native_parameters": route.get("native_parameters", {}),
                "criteria": route.get("criteria", {}),
                "completeness": route.get("completeness"),
            }
            for route in plan_without_fingerprint.get("routes", [])
        ],
    }
    return sha256_json(material)


def result_snapshot_hash(
    executions: list[dict[str, Any]], items: list[dict[str, Any]]
) -> str:
    return sha256_json({"executions": executions, "items": items})
