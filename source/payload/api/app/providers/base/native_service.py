from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from .contracts import ProviderDescriptor, resolve_provider_configuration


class NativeProviderService:
    """Reference execution contract for provider-native V7 connectors.

    Subclasses own request construction and normalization.  This base class owns
    bounded transport, retries, response-size enforcement, parameter validation,
    and effective configuration resolution so semantic/native paths share the
    same behavior.
    """

    descriptor: ProviderDescriptor

    def __init__(self, settings: dict[str, Any]):
        self.settings = dict(settings)

    def effective_configuration(
        self,
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
        execution_overrides: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        return resolve_provider_configuration(
            self.descriptor,
            global_settings=global_settings,
            project_settings=project_settings,
            execution_overrides=execution_overrides,
        )

    def operation_contract(self, operation: str) -> list[dict[str, Any]]:
        contracts = self.descriptor.metadata.get("parameter_contracts") or {}
        if operation not in contracts:
            raise ValueError(f"Unsupported {self.descriptor.provider_id} operation: {operation}")
        rows = contracts[operation]
        if not isinstance(rows, list):
            raise RuntimeError("Invalid provider parameter contract")
        return [dict(row) for row in rows]

    def validate_parameters(
        self,
        operation: str,
        parameters: dict[str, Any] | None,
        *,
        project_settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = self.operation_contract(operation)
        specs = {str(row["name"]): row for row in contract}
        supplied = dict(parameters or {})
        unknown = sorted(set(supplied) - set(specs))
        if unknown:
            raise ValueError(f"Unknown {self.descriptor.provider_id} parameters: {', '.join(unknown)}")

        merged: dict[str, Any] = {}
        project_settings = project_settings or {}
        for name, spec in specs.items():
            if name in supplied:
                value = supplied[name]
            elif name in project_settings and project_settings[name] not in (None, ""):
                value = project_settings[name]
            elif "default" in spec:
                value = spec.get("default")
            else:
                value = None
            if value is None and spec.get("required"):
                raise ValueError(f"Missing required parameter: {name}")
            if value is None:
                continue
            merged[name] = self._validate_value(name, value, spec)
        return merged

    @staticmethod
    def _validate_value(name: str, value: Any, spec: dict[str, Any]) -> Any:
        value_type = str(spec.get("type") or "string")
        if value_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            value = value.strip()
            minimum_length = spec.get("min_length")
            maximum_length = spec.get("max_length")
            if minimum_length is not None and len(value) < int(minimum_length):
                raise ValueError(f"{name} is shorter than allowed")
            if maximum_length is not None and len(value) > int(maximum_length):
                raise ValueError(f"{name} is longer than allowed")
        elif value_type == "integer":
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            if spec.get("minimum") is not None and value < int(spec["minimum"]):
                raise ValueError(f"{name} is below the minimum")
            if spec.get("maximum") is not None and value > int(spec["maximum"]):
                raise ValueError(f"{name} exceeds the maximum")
        elif value_type == "boolean":
            if type(value) is not bool:
                raise ValueError(f"{name} must be boolean")
        elif value_type in {"array[string]", "array[integer]"}:
            if not isinstance(value, list):
                raise ValueError(f"{name} must be an array")
            max_items = spec.get("max_items")
            if max_items is not None and len(value) > int(max_items):
                raise ValueError(f"{name} contains too many values")
            element_type = "string" if value_type == "array[string]" else "integer"
            checked = []
            for index, element in enumerate(value):
                checked.append(NativeProviderService._validate_value(f"{name}[{index}]", element, {"type": element_type}))
            value = list(dict.fromkeys(checked))
        else:
            raise ValueError(f"Unsupported contract type for {name}: {value_type}")

        enum = spec.get("enum")
        if enum is not None and value not in enum:
            raise ValueError(f"{name} is not one of the documented values")
        return value

    async def _get_json(self, url: str, query: dict[str, Any]) -> tuple[Any, str, int]:
        timeout = httpx.Timeout(
            float(self.settings.get("timeout_seconds", 40)),
            connect=float(self.settings.get("connect_timeout_seconds", 20)),
        )
        retries = int(self.settings.get("retry_count", 2))
        backoff = float(self.settings.get("backoff_seconds", 1))
        max_bytes = int(self.settings.get("max_response_bytes", 25_000_000))
        headers = {
            "User-Agent": str(self.settings.get("user_agent", "HDP/7.0.0")),
            "Accept-Language": str(self.settings.get("accept_language", "en")),
            "Accept": "application/json, application/geo+json;q=0.9",
        }
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    async with client.stream("GET", url, params=query, headers=headers) as response:
                        response.raise_for_status()
                        declared = response.headers.get("content-length")
                        if declared and declared.isdigit() and int(declared) > max_bytes:
                            raise RuntimeError(f"Provider response exceeds {max_bytes} bytes")
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > max_bytes:
                                raise RuntimeError(f"Provider response exceeds {max_bytes} bytes")
                        request_url = str(response.request.url)
                        status = response.status_code
                return json.loads(body), request_url, status
            except httpx.HTTPError as exc:
                last_error = exc
                status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                retryable = status is None or status == 429 or (status is not None and status >= 500)
                if attempt >= retries or not retryable:
                    raise
                await asyncio.sleep(backoff * (2**attempt))
        raise RuntimeError("Provider HTTP failure without response") from last_error

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any] | None = None,
        *,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        values = self.validate_parameters(operation, parameters, project_settings=project_settings)
        spec = self.build_request(operation, values)
        if str(spec.get("method", "GET")).upper() != "GET":
            raise RuntimeError("Current V7 native provider service only permits non-destructive GET operations")
        payload, request_url, http_status = await self._get_json(str(spec["url"]), dict(spec.get("query_parameters") or {}))
        items = self.normalize(operation, payload, request_url, values)
        native = {
            "method": "GET",
            "url": request_url,
            "base_url": str(spec["url"]),
            "query_parameters": dict(spec.get("query_parameters") or {}),
            "http_status": http_status,
            "operation": operation,
            "contract_version": self.descriptor.api_version,
        }
        return payload, items, native

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        raise NotImplementedError(f"Semantic execution not implemented for {self.descriptor.provider_id}")


def generic_rows(payload: Any) -> list[dict[str, Any]]:
    """Conservative row extraction used only where a provider operation has no richer normalizer."""
    if isinstance(payload, list):
        if len(payload) > 1 and isinstance(payload[1], list):
            return [row for row in payload[1] if isinstance(row, dict)]
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("Data", "data", "value", "results", "features", "items"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def normalize_generic_rows(
    payload: Any,
    *,
    request_url: str,
    source: str,
    organization: str,
    title_fields: tuple[str, ...] = ("name", "title", "label", "Indicator", "IndicatorName"),
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, row in enumerate(generic_rows(payload)):
        title = next((row.get(field) for field in title_fields if row.get(field) not in (None, "")), None)
        identifier = row.get("id") or row.get("Id") or row.get("code") or row.get("Code") or row.get("IndicatorId") or index
        items.append({
            "id": str(identifier),
            "title": str(title or identifier),
            "description": str(row.get("description") or row.get("Description") or ""),
            "date": row.get("date") or row.get("Date") or row.get("year") or row.get("Year"),
            "url": request_url,
            "source": source,
            "organization": organization,
            "geographic_scope": row.get("country") or row.get("CountryName") or row.get("geoAreaName") or "",
            "_native": row,
            "resources": [],
        })
    return items
