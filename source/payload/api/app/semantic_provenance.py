from __future__ import annotations

"""Deterministic, secret-free fingerprints for semantic queries and snapshots."""

import hashlib
import json
from typing import Any

SECRET_KEYS = {"appname", "app_identifier", "authorization", "token", "password", "secret"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("<redacted>" if str(k).casefold() in SECRET_KEYS else _redact(v)) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(_redact(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def query_fingerprint(plan_without_fingerprint: dict[str, Any]) -> str:
    material = {
        "schema_version": plan_without_fingerprint.get("schema_version"),
        "contract_version": plan_without_fingerprint.get("contract_version"),
        "intent": plan_without_fingerprint.get("intent"),
        "routes": [
            {
                "source": route.get("source"),
                "operation": route.get("operation"),
                "executable": route.get("executable"),
                "native_parameters": route.get("native_parameters", {}),
                "criteria": route.get("criteria", {}),
            }
            for route in plan_without_fingerprint.get("routes", [])
        ],
    }
    return sha256_json(material)


def result_snapshot_hash(executions: list[dict[str, Any]], items: list[dict[str, Any]]) -> str:
    return sha256_json({"executions": executions, "items": items})
