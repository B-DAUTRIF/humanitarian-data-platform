from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService
from .descriptor import GDACS_DESCRIPTOR


class GDACSService(NativeProviderService):
    descriptor = GDACS_DESCRIPTOR

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if operation != "search_events":
            raise ValueError(f"Unsupported GDACS operation: {operation}")
        query: dict[str, Any] = {}
        if parameters.get("eventlist"):
            query["eventlist"] = ";".join(str(value).upper() for value in parameters["eventlist"])
        if parameters.get("fromdate"):
            query["fromdate"] = parameters["fromdate"]
        if parameters.get("todate"):
            query["todate"] = parameters["todate"]
        if parameters.get("alertlevel"):
            query["alertlevel"] = ";".join(str(value).lower() for value in parameters["alertlevel"])
        return {
            "method":"GET",
            "url":"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
            "query_parameters":query,
        }

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        from ...main import parse_gdacs_events
        return parse_gdacs_events(payload, "", 100, resource_url=request_url)

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        parameters = dict(route.get("parameters") or {})
        project_settings = project_settings or {}
        values: dict[str, Any] = {
            "eventlist": list(project_settings.get("event_types") or []),
            "alertlevel": [str(v).lower() for v in (project_settings.get("alert_levels") or ["Green", "Orange", "Red"])],
        }
        if parameters.get("date_from"):
            values["fromdate"] = parameters["date_from"]
        if parameters.get("date_to"):
            values["todate"] = parameters["date_to"]
        payload, items, native = await self.execute("search_events", values)
        query_text = str(parameters.get("query") or "").casefold().strip()
        if query_text:
            items = [item for item in items if query_text in " ".join(str(item.get(k) or "") for k in ("title", "description", "geographic_scope")).casefold()]
        limit = int(parameters.get("result_limit") or 25)
        return payload, items[:limit], native
