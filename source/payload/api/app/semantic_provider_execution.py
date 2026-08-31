from __future__ import annotations

"""Provider-native execution helpers for the V7 semantic router.

The semantic router delegates specialized providers to the same reference
service used by their native API. This prevents a second, drifting provider
implementation and keeps native request/provenance behavior inspectable.
"""

import time
from typing import Any

from .v7_trace import trace_event


async def execute_reliefweb_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    from .providers.reliefweb.service import ReliefWebService

    parameters = route["parameters"]
    native = route.get("native_parameters", {})
    filters: list[dict[str, Any]] = []
    if native.get("filter[field]"):
        filters.append({"field": native["filter[field]"], "value": native["filter[value]"]})
    if native.get("filter_date_field"):
        value: dict[str, str] = {}
        if native.get("filter_date_from"):
            value["from"] = f"{native['filter_date_from']}T00:00:00+00:00"
        if native.get("filter_date_to"):
            value["to"] = f"{native['filter_date_to']}T23:59:59+00:00"
        filters.append({"field": native["filter_date_field"], "value": value})
    rw_parameters: dict[str, Any] = {
        "query": parameters.get("query") or "",
        "limit": int(parameters.get("result_limit") or 25),
        "offset": 0,
        "profile": "full",
        "preset": "latest",
        "sort": ["date.created:desc"],
    }
    if len(filters) == 1:
        rw_parameters["filter"] = filters[0]
    elif filters:
        rw_parameters["filter"] = {"operator": "AND", "conditions": filters}
    service = ReliefWebService(settings)
    project_config = route.get("provider_configuration") if isinstance(route.get("provider_configuration"), dict) else {}
    return await service.execute("reports", rw_parameters, global_settings=settings, project_settings=project_config)


async def execute_hapi_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    from .main import search_remote_source
    from .source_registry import request_preview

    parameters = dict(route["parameters"])
    parameters.update({key: value for key, value in route.get("native_parameters", {}).items() if key == "location_code"})
    payload, items = await search_remote_source("hdx-hapi", parameters, settings)
    preview = request_preview("hdx-hapi", parameters)
    return payload, items, {"method": preview["method"], "url": preview["url"], "query_parameters": preview["query_parameters"]}


async def execute_world_bank_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    from .providers.world_bank_health.service import WorldBankHealthService

    service = WorldBankHealthService(settings)
    project_config = route.get("provider_configuration") if isinstance(route.get("provider_configuration"), dict) else {}
    return await service.execute_semantic(route, global_settings=settings, project_settings=project_config)


async def execute_six_provider_native(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]] | None:
    source = str(route["source"])
    project_config = route.get("provider_configuration") if isinstance(route.get("provider_configuration"), dict) else {}
    if source == "dhs":
        from .providers.dhs.service import DHSService
        service = DHSService(settings)
    elif source == "gdacs":
        from .providers.gdacs.service import GDACSService
        service = GDACSService(settings)
    elif source == "un-sdg":
        from .providers.un_sdg.service import UNSDGService
        service = UNSDGService(settings)
    elif source == "unhcr":
        from .providers.unhcr.service import UNHCRService
        service = UNHCRService(settings)
    elif source == "unicef-sdmx":
        from .providers.unicef_sdmx.service import UNICEFSDMXService
        service = UNICEFSDMXService(settings)
    elif source == "who-gho":
        from .providers.who_gho.service import WHOGHOService
        service = WHOGHOService(settings)
    else:
        return None
    return await service.execute_semantic(route, global_settings=settings, project_settings=project_config)


async def execute_native_route(route: dict[str, Any], settings: dict[str, Any]) -> tuple[Any, list[dict[str, Any]], dict[str, Any]] | None:
    source = str(route["source"])
    started = time.perf_counter()
    trace_event(
        "semantic.provider.start",
        source=source,
        operation=route.get("operation"),
        executable=route.get("executable"),
        completeness=route.get("completeness"),
        criteria=route.get("criteria"),
        parameters=route.get("parameters"),
        native_parameters=route.get("native_parameters"),
        canonical_geography=route.get("canonical_geography"),
        project_enabled=route.get("project_enabled"),
        project_configuration=route.get("provider_configuration"),
    )
    try:
        if source == "reliefweb":
            result = await execute_reliefweb_native(route, settings)
        elif source == "hdx-hapi":
            result = await execute_hapi_native(route, settings)
        elif source == "world-bank-health":
            result = await execute_world_bank_native(route, settings)
        else:
            result = await execute_six_provider_native(route, settings)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        if result is None:
            trace_event("semantic.provider.unsupported", source=source, elapsed_ms=elapsed_ms)
            return None
        payload, items, native = result
        trace_event(
            "semantic.provider.finish",
            source=source,
            operation=route.get("operation"),
            elapsed_ms=elapsed_ms,
            result_count=len(items),
            native_request=native,
            payload_type=type(payload).__name__,
        )
        return result
    except Exception as exc:
        trace_event(
            "semantic.provider.exception",
            source=source,
            operation=route.get("operation"),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            parameters=route.get("parameters"),
            native_parameters=route.get("native_parameters"),
            canonical_geography=route.get("canonical_geography"),
        )
        raise
