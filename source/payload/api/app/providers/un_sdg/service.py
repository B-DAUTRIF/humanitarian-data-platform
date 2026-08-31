from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, generic_rows, normalize_generic_rows
from .descriptor import UN_SDG_DESCRIPTOR


def _tokens(value: str) -> list[str]:
    return [token for token in value.casefold().replace("_", " ").replace("-", " ").split() if token]


def _matches(value: str, query: str) -> bool:
    haystack = value.casefold()
    return all(token in haystack for token in _tokens(query)) if query else True


def _series_identity(row: dict[str, Any]) -> tuple[str, str]:
    code = row.get("seriesCode") or row.get("series_code") or row.get("code") or row.get("Code")
    label = row.get("seriesDescription") or row.get("description") or row.get("name") or row.get("title") or row.get("Description")
    return (str(code) if code is not None else "", str(label) if label is not None else "")


class UNSDGService(NativeProviderService):
    descriptor = UN_SDG_DESCRIPTOR

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        base = "https://unstats.un.org/SDGAPI/v1/sdg"
        if operation == "list_indicators":
            return {"method":"GET", "url":f"{base}/Indicator/List", "query_parameters":{}}
        if operation == "geoarea_series":
            return {"method":"GET", "url":f"{base}/GeoArea/{parameters['areaCode']}/List", "query_parameters":{}}
        if operation == "series_data":
            query = {name:value for name, value in parameters.items() if value not in (None, "")}
            return {"method":"GET", "url":f"{base}/Series/Data", "query_parameters":query}
        raise ValueError(f"Unsupported UN SDG operation: {operation}")

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if operation in {"list_indicators", "geoarea_series"}:
            return normalize_generic_rows(payload, request_url=request_url, source="UN Global SDG Indicators Database", organization="UNSD", title_fields=("seriesDescription","description","name","title","code","seriesCode"))
        items: list[dict[str, Any]] = []
        series_code = str(parameters.get("seriesCode") or "")
        area_code = parameters.get("areaCode")
        for index, row in enumerate(generic_rows(payload)):
            row_series = str(row.get("seriesCode") or row.get("series_code") or series_code)
            if series_code and row_series and row_series != series_code:
                continue
            period = row.get("timePeriod") or row.get("time_period") or row.get("year")
            value = row.get("value") if "value" in row else row.get("Value")
            geo = row.get("geoAreaName") or row.get("geo_area_name") or row.get("geoAreaCode") or area_code
            if period is None and value is None:
                continue
            period_text = str(period or "")
            items.append({
                "id":f"{row_series}:{row.get('geoAreaCode') or area_code}:{period_text}:{index}",
                "title":f"{row_series} — {geo} — {period_text}",
                "description":f"value={value}; units={row.get('units') or row.get('unit') or ''}; nature={row.get('nature') or row.get('natureCode') or ''}",
                "date":f"{int(float(period_text)):04d}-12-31" if period_text.replace(".0", "").isdigit() else None,
                "url":request_url,
                "source":"UN Global SDG Indicators Database",
                "organization":"UNSD",
                "geographic_scope":str(geo or ""),
                "series_code":row_series,
                "value":value,
                "unit":row.get("units") or row.get("unit"),
                "_native":row,
                "resources":[],
            })
        return items

    async def execute_semantic(self, route: dict[str, Any], *, global_settings: dict[str, Any] | None = None, project_settings: dict[str, Any] | None = None) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        native = dict(route.get("native_parameters") or {})
        parameters = dict(route.get("parameters") or {})
        area_code = native.get("areaCode")
        query = str(native.get("series_search") or parameters.get("query") or "")
        if area_code is not None:
            catalog_payload, catalog_items, catalog_request = await self.execute("geoarea_series", {"areaCode":int(area_code)})
        else:
            catalog_payload, catalog_items, catalog_request = await self.execute("list_indicators", {})
        candidates: list[tuple[str, str]] = []
        seen: set[str] = set()
        for row in generic_rows(catalog_payload):
            code, label = _series_identity(row)
            if code and code not in seen and _matches(f"{code} {label}", query):
                seen.add(code)
                candidates.append((code, label))
                if len(candidates) >= 5:
                    break
        result_limit = int(parameters.get("result_limit") or 25)
        if not query:
            return catalog_payload, catalog_items[:result_limit], {"catalogue":catalog_request, "series_candidates":[c[0] for c in candidates]}
        payloads: list[Any] = []
        items: list[dict[str, Any]] = []
        requests: list[dict[str, Any]] = []
        for code, _label in candidates:
            args: dict[str, Any] = {"seriesCode":code, "page":1, "pageSize":min(1000, result_limit * 4)}
            if area_code is not None:
                args["areaCode"] = int(area_code)
            if native.get("timePeriodStart") is not None:
                args["timePeriodStart"] = int(native["timePeriodStart"])
            if native.get("timePeriodEnd") is not None:
                args["timePeriodEnd"] = int(native["timePeriodEnd"])
            payload, rows, request = await self.execute("series_data", args)
            payloads.append(payload)
            requests.append(request)
            items.extend(rows)
            if len(items) >= result_limit:
                break
        return {"catalogue":catalog_payload, "series_data":payloads}, items[:result_limit], {"catalogue":catalog_request, "series_requests":requests, "series_candidates":[c[0] for c in candidates]}
