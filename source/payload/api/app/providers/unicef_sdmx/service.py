from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, normalize_generic_rows
from .descriptor import UNICEF_SDMX_DESCRIPTOR


def _dataflow_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return

        lowered = {str(key).casefold(): key for key in value}
        identifier_key = next((lowered[key] for key in ("id", "dataflowid", "dataflow_id") if key in lowered), None)
        agency_key = next((lowered[key] for key in ("agencyid", "agency_id", "agency") if key in lowered), None)
        name_key = next((lowered[key] for key in ("name", "names", "label", "title") if key in lowered), None)
        if identifier_key is not None and (agency_key is not None or name_key is not None):
            rows.append(value)

        for key, child in value.items():
            if str(key).casefold() in {"dataflows", "dataflow", "structure", "data", "items", "results"}:
                walk(child)

    walk(payload)
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        identifier = str(row.get("id") or row.get("ID") or row.get("dataflowId") or row.get("dataflowID") or "")
        agency = str(row.get("agencyID") or row.get("agencyId") or row.get("agency") or "")
        version = str(row.get("version") or row.get("Version") or "")
        key = (agency, identifier, version)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _label(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for preferred in ("en", "fr", "EN", "FR"):
            if value.get(preferred):
                return str(value[preferred])
        for item in value.values():
            if isinstance(item, str) and item.strip():
                return item
    if isinstance(value, list):
        for item in value:
            text = _label(item)
            if text:
                return text
    return ""


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
            items: list[dict[str, Any]] = []
            for index, row in enumerate(_dataflow_rows(payload)):
                identifier = row.get("id") or row.get("ID") or row.get("dataflowId") or row.get("dataflowID") or index
                name = _label(row.get("name") or row.get("Name") or row.get("names") or row.get("label"))
                agency = row.get("agencyID") or row.get("agencyId") or row.get("agency") or ""
                version = row.get("version") or row.get("Version") or ""
                items.append({
                    "id": str(identifier),
                    "title": name or str(identifier),
                    "description": _label(row.get("description") or row.get("Description")),
                    "date": None,
                    "url": request_url,
                    "source": "UNICEF Data SDMX",
                    "organization": "UNICEF",
                    "geographic_scope": "",
                    "agency": str(agency),
                    "version": str(version),
                    "_native": row,
                    "resources": [],
                })
            return items
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
