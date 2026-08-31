from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, normalize_generic_rows
from .descriptor import UNHCR_DESCRIPTOR


class UNHCRService(NativeProviderService):
    descriptor = UNHCR_DESCRIPTOR

    ENDPOINTS = {
        "population": "population",
        "demographics": "demographics",
        "asylum_applications": "asylum-applications",
        "asylum_decisions": "asylum-decisions",
        "solutions": "solutions",
        "countries": "countries",
        "regions": "regions",
        "years": "years",
    }

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        endpoint = self.ENDPOINTS.get(operation)
        if endpoint is None:
            raise ValueError(f"Unsupported UNHCR operation: {operation}")
        query: dict[str, Any] = {}
        for name, value in parameters.items():
            if value in (None, "", False):
                continue
            if type(value) is bool:
                query[name] = "true" if value else "false"
            else:
                query[name] = value
        return {
            "method":"GET",
            "url":f"https://api.unhcr.org/population/v1/{endpoint}/",
            "query_parameters":query,
        }

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if operation == "population":
            from ...main import parse_unhcr_population
            compat = {
                "query":"",
                "date_from":"",
                "date_to":"",
                "location":"",
                "result_limit":int(parameters.get("limit") or 25),
                "auto_download":False,
                "page":int(parameters.get("page") or 1),
                "year_from":int(parameters.get("yearFrom") or parameters.get("year") or 1951),
                "year_to":int(parameters.get("yearTo") or parameters.get("year") or 2100),
                "country_of_origin":str(parameters.get("coo") or ""),
                "country_of_asylum":str(parameters.get("coa") or ""),
            }
            return parse_unhcr_population(payload, compat, "", int(parameters.get("limit") or 25))
        return normalize_generic_rows(
            payload,
            request_url=request_url,
            source="UNHCR Refugee Statistics",
            organization="UNHCR",
            title_fields=("name","country","region","year","coo_name","coa_name","title"),
        )

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        parameters = dict(route.get("parameters") or {})
        native = dict(route.get("native_parameters") or {})
        limit = int(parameters.get("result_limit") or 25)
        project_settings = project_settings or {}
        base: dict[str, Any] = {
            "limit":limit,
            "page":int(project_settings.get("page") or 1),
            "cf_type":"ISO",
            "coo_all":False,
            "coa_all":False,
            "download":False,
        }
        if native.get("yearFrom") is not None:
            base["yearFrom"] = int(native["yearFrom"])
        elif parameters.get("date_from"):
            base["yearFrom"] = int(str(parameters["date_from"])[:4])
        else:
            base["yearFrom"] = int(project_settings.get("year_from") or 1951)
        if native.get("yearTo") is not None:
            base["yearTo"] = int(native["yearTo"])
        elif parameters.get("date_to"):
            base["yearTo"] = int(str(parameters["date_to"])[:4])
        else:
            base["yearTo"] = int(project_settings.get("year_to") or 2100)
        if base["yearFrom"] > base["yearTo"]:
            raise ValueError("UNHCR yearFrom must be <= yearTo")

        iso3 = str(native.get("iso3") or "").upper()
        requests: list[dict[str, Any]] = []
        payloads: dict[str, Any] = {}
        items: list[dict[str, Any]] = []
        roles = native.get("country_roles") or ([] if not iso3 else ["origin", "asylum"])
        if not roles:
            payload, rows, req = await self.execute("population", base)
            return payload, rows[:limit], req

        for role in roles:
            values = dict(base)
            if role == "origin":
                values["coo"] = iso3
            elif role == "asylum":
                values["coa"] = iso3
            else:
                raise ValueError(f"Unsupported UNHCR geography role: {role}")
            payload, rows, req = await self.execute("population", values)
            payloads[role] = payload
            requests.append({"role":role, **req})
            for row in rows:
                tagged = dict(row)
                tagged["_hdp_semantics"] = {"geography_role":role, "iso3":iso3, "cf_type":"ISO"}
                tagged["id"] = f"{role}:{tagged.get('id')}"
                items.append(tagged)
        return payloads, items[:limit], {"operation":"population", "requests":requests, "geography_roles":list(roles), "iso3":iso3}
