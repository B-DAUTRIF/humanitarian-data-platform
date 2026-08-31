from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, normalize_generic_rows
from .descriptor import UNICEF_SDMX_DESCRIPTOR


class UNICEFSDMXService(NativeProviderService):
    descriptor = UNICEF_SDMX_DESCRIPTOR

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        base = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest"
        agency = parameters["agency"]
        dataflow = parameters["dataflow"]
        version = parameters["version"]
        if operation == "list_dataflows":
            url = f"{base}/dataflow/{agency}/{dataflow}/{version}/"
            query = {"format":parameters.get("format","sdmx-json"), "detail":parameters.get("detail","full"), "references":parameters.get("references","none")}
        elif operation == "get_data":
            key = parameters.get("data_query") or "all"
            url = f"{base}/data/{agency},{dataflow},{version}/{key}"
            query = {"format":parameters.get("format","sdmx-json")}
        else:
            raise ValueError(f"Unsupported UNICEF SDMX operation: {operation}")
        return {"method":"GET", "url":url, "query_parameters":query}

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if operation == "list_dataflows":
            from ...main import parse_unicef_dataflows
            return parse_unicef_dataflows(payload, "", 5000)
        return normalize_generic_rows(
            payload,
            request_url=request_url,
            source="UNICEF Data SDMX",
            organization="UNICEF",
            title_fields=("name","Name","label","Label","id","ID","title"),
        )

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        parameters = dict(route.get("parameters") or {})
        project_settings = project_settings or {}
        payload, items, native = await self.execute(
            "list_dataflows",
            {
                "agency":str(project_settings.get("agency") or "all"),
                "dataflow":str(project_settings.get("dataflow") or "all"),
                "version":str(project_settings.get("version") or "latest"),
                "format":"sdmx-json",
                "detail":str(project_settings.get("detail") or "full"),
                "references":str(project_settings.get("references") or "none"),
            },
        )
        query = str(parameters.get("query") or "").casefold().strip()
        if query:
            items = [item for item in items if query in " ".join(str(item.get(k) or "") for k in ("id","title","description")).casefold()]
        return payload, items[: int(parameters.get("result_limit") or 25)], native
