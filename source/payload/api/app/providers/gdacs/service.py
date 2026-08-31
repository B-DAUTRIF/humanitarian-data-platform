from __future__ import annotations

from html import unescape
from re import sub
from typing import Any

from ..base.native_service import NativeProviderService
from .descriptor import GDACS_DESCRIPTOR


def _plain_text(value: Any) -> str:
    text = unescape(str(value or ""))
    return " ".join(sub(r"<[^>]+>", " ", text).split())


def _gdacs_features(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return [row for row in payload["features"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


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
        if operation != "search_events":
            raise ValueError(f"Unsupported GDACS operation: {operation}")
        items: list[dict[str, Any]] = []
        for index, feature in enumerate(_gdacs_features(payload)):
            properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else feature
            event_id = properties.get("eventid") or properties.get("eventId") or properties.get("id") or index
            event_type = properties.get("eventtype") or properties.get("eventType") or ""
            name = properties.get("name") or properties.get("eventname") or properties.get("eventName")
            description = _plain_text(properties.get("description") or properties.get("htmldescription") or "")
            title = str(name or description or f"{event_type} {event_id}").strip()
            country = properties.get("country") or properties.get("countryname") or properties.get("countryName") or ""
            event_url = properties.get("url") or properties.get("eventurl") or properties.get("eventUrl") or request_url
            items.append({
                "id": str(event_id),
                "title": title,
                "description": description,
                "date": properties.get("fromdate") or properties.get("fromDate") or properties.get("date"),
                "url": str(event_url),
                "source": "GDACS",
                "organization": "Global Disaster Alert and Coordination System",
                "geographic_scope": str(country),
                "event_type": event_type,
                "alert_level": properties.get("alertlevel") or properties.get("alertLevel"),
                "_native": feature,
                "resources": [],
            })
        return items

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
