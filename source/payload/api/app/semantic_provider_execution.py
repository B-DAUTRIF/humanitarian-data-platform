from __future__ import annotations

"""Provider-native execution helpers for the V7 semantic router.

The semantic router delegates specialized providers to the same reference
service used by their native API. This prevents a second, drifting provider
implementation and keeps native request/provenance behavior inspectable.
"""

from typing import Any


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
    if source == "reliefweb":
        return await execute_reliefweb_native(route, settings)
    if source == "hdx-hapi":
        return await execute_hapi_native(route, settings)
    if source == "world-bank-health":
        return await execute_world_bank_native(route, settings)
    specialized = await execute_six_provider_native(route, settings)
    if specialized is not None:
        return specialized
    return None
