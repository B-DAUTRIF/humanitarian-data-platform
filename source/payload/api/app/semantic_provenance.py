from __future__ import annotations

"""Deterministic, secret-free fingerprints for semantic queries and snapshots."""

import hashlib
import json
import re
from typing import Any

_EXACT_SECRET_KEYS = {
    "appname",
    "app_identifier",
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "client_secret",
    "cookie",
    "set_cookie",
    "x_api_key",
}
_COMPACT_SECRET_KEYS = {
    "appidentifier",
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "accesstoken",
    "refreshtoken",
    "clientsecret",
    "cookie",
    "setcookie",
    "xapikey",
}
_SECRET_SUFFIXES = ("_password", "_passwd", "_secret", "_token", "_api_key")
_COMPACT_SECRET_SUFFIXES = ("password", "passwd", "secret", "token", "apikey")


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")


def _is_secret_key(value: Any) -> bool:
    key = _normalized_key(value)
    compact = key.replace("_", "")
    if key in _EXACT_SECRET_KEYS or compact in _COMPACT_SECRET_KEYS:
        return True
    if any(key.endswith(suffix) for suffix in _SECRET_SUFFIXES):
        return True
    return any(compact.endswith(suffix) for suffix in _COMPACT_SECRET_SUFFIXES) and compact not in {"tokencount"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): ("<redacted>" if _is_secret_key(key) else _redact(child))
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
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


def result_snapshot_hash(executions: list[dict[str, Any]], items: list[dict[str, Any]]) -> str:
    return sha256_json({"executions": executions, "items": items})
