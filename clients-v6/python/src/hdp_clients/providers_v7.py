from __future__ import annotations

from typing import Any

from .client import HDPClient

SIX_PROVIDERS = ("dhs", "gdacs", "un-sdg", "unhcr", "unicef-sdmx", "who-gho")


def provider_descriptor(client: HDPClient, provider: str) -> Any:
    if provider not in SIX_PROVIDERS:
        raise ValueError(f"unsupported specialized provider: {provider}")
    return client._request("GET", f"/api/providers/{provider}/descriptor")


def provider_effective_configuration(client: HDPClient, provider: str, *, project_id: str | None = None) -> Any:
    if provider not in SIX_PROVIDERS:
        raise ValueError(f"unsupported specialized provider: {provider}")
    params = {"project_id": project_id} if project_id else None
    return client._request("GET", f"/api/providers/{provider}/configuration/effective", params=params)


def provider_query(client: HDPClient, provider: str, operation: str, parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    if provider not in SIX_PROVIDERS:
        raise ValueError(f"unsupported specialized provider: {provider}")
    body: dict[str, Any] = {"operation": operation, "parameters": dict(parameters or {})}
    if project_id:
        body["project_id"] = project_id
    return client._request("POST", f"/api/providers/{provider}/query", json=body)


def dhs_query(client: HDPClient, operation: str = "list_indicators", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "dhs", operation, parameters, project_id=project_id)


def gdacs_query(client: HDPClient, operation: str = "search_events", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "gdacs", operation, parameters, project_id=project_id)


def un_sdg_query(client: HDPClient, operation: str = "list_indicators", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "un-sdg", operation, parameters, project_id=project_id)


def unhcr_query(client: HDPClient, operation: str = "population", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "unhcr", operation, parameters, project_id=project_id)


def unicef_sdmx_query(client: HDPClient, operation: str = "list_dataflows", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "unicef-sdmx", operation, parameters, project_id=project_id)


def who_gho_query(client: HDPClient, operation: str = "list_indicators", parameters: dict[str, Any] | None = None, *, project_id: str | None = None) -> Any:
    return provider_query(client, "who-gho", operation, parameters, project_id=project_id)
