from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, normalize_generic_rows
from .descriptor import WHO_GHO_DESCRIPTOR


class WHOGHOService(NativeProviderService):
    descriptor = WHO_GHO_DESCRIPTOR

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        base = "https://ghoapi.azureedge.net/api"
        query: dict[str, Any] = {}
        if operation == "list_dimensions":
            url = f"{base}/Dimension"
        elif operation == "dimension_values":
            url = f"{base}/DIMENSION/{parameters['dimension']}/DimensionValues"
        elif operation == "list_indicators":
            url = f"{base}/Indicator"
            if parameters.get("filter"):
                query["$filter"] = parameters["filter"]
        elif operation == "indicator_data":
            url = f"{base}/{parameters['indicator']}"
            if parameters.get("filter"):
                query["$filter"] = parameters["filter"]
        else:
            raise ValueError(f"Unsupported WHO GHO operation: {operation}")
        if "top" in parameters:
            query["$top"] = parameters["top"]
        if "skip" in parameters:
            query["$skip"] = parameters["skip"]
        query["$format"] = parameters.get("format", "json")
        return {"method":"GET", "url":url, "query_parameters":query}

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if operation == "list_indicators":
            from ...main import parse_who_indicators
            return parse_who_indicators(payload, "", int(parameters.get("top") or 100))
        return normalize_generic_rows(
            payload,
            request_url=request_url,
            source="WHO Global Health Observatory",
            organization="World Health Organization",
            title_fields=("IndicatorName", "Title", "Dimension", "Code", "SpatialDim", "TimeDim", "name", "title"),
        )

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        parameters = dict(route.get("parameters") or {})
        query_text = str(parameters.get("query") or "").strip()
        result_limit = int(parameters.get("result_limit") or 25)
        escaped = query_text.replace("'", "''")
        filter_value = ""
        if query_text:
            filter_value = f"contains(IndicatorName,'{escaped}') or contains(IndicatorCode,'{escaped}')"
        payload, items, native = await self.execute(
            "list_indicators",
            {"filter":filter_value, "top":max(result_limit, 100), "skip":int((project_settings or {}).get("skip") or 0), "format":"json"},
        )
        return payload, items[:result_limit], native
