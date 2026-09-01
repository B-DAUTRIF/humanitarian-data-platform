from __future__ import annotations

from typing import Any

from ..base.native_service import NativeProviderService, normalize_generic_rows
from .descriptor import DHS_DESCRIPTOR


class DHSService(NativeProviderService):
    descriptor = DHS_DESCRIPTOR

    def build_request(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        endpoints = {
            "list_indicators": "https://api.dhsprogram.com/rest/dhs/indicators",
            "indicator_data": "https://api.dhsprogram.com/rest/dhs/data",
            "list_countries": "https://api.dhsprogram.com/rest/dhs/countries",
            "list_surveys": "https://api.dhsprogram.com/rest/dhs/surveys",
        }
        if operation not in endpoints:
            raise ValueError(f"Unsupported DHS operation: {operation}")
        query: dict[str, Any] = {}
        for name, value in parameters.items():
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                query[name] = ",".join(str(item) for item in value)
            else:
                query[name] = value
        return {"method":"GET", "url":endpoints[operation], "query_parameters":query}

    def normalize(self, operation: str, payload: Any, request_url: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        if operation == "list_indicators":
            from ...main import parse_dhs_indicators
            return parse_dhs_indicators(payload, "", int(parameters.get("perpage") or 5000))
        return normalize_generic_rows(
            payload,
            request_url=request_url,
            source="The DHS Program",
            organization="The DHS Program",
            title_fields=("Indicator", "IndicatorName", "CountryName", "SurveyType", "SurveyId", "name", "title"),
        )

    @staticmethod
    def _verified_country_mapping(rows: list[dict[str, Any]], iso3: str) -> tuple[str, dict[str, Any]]:
        """Resolve ISO3 to one DHS country code without treating duplicate catalogue rows as ambiguity.

        The DHS countries endpoint may return repeated catalogue rows. Verification is therefore
        based on the set of distinct non-empty DHS_countryCode values attached to exact
        ISO3_countryCode matches. More than one distinct DHS code still fails closed.
        """
        wanted = iso3.strip().upper()
        matches = [
            row for row in rows
            if isinstance(row, dict)
            and str(row.get("ISO3_countryCode") or "").strip().upper() == wanted
        ]
        codes = sorted({str(row.get("DHS_countryCode") or "").strip() for row in matches if str(row.get("DHS_countryCode") or "").strip()})
        if len(codes) != 1:
            raise ValueError(
                f"DHS ISO3 mapping is not uniquely verified for {wanted}: "
                f"{len(matches)} exact catalogue row(s), {len(codes)} distinct DHS code(s)"
            )
        code = codes[0]
        representative = next(row for row in matches if str(row.get("DHS_countryCode") or "").strip() == code)
        evidence = {
            "iso3": wanted,
            "dhs_country_code": code,
            "exact_match_count": len(matches),
            "distinct_dhs_codes": codes,
            "catalogue_row": representative,
        }
        return code, evidence

    async def _resolve_iso3(self, iso3: str) -> tuple[str, dict[str, Any]]:
        # 100 is sufficient for the current DHS country catalogue and avoids provider-side
        # behaviour observed with oversized perpage values. We still verify the exact ISO3
        # mapping and never substitute ISO3 directly into countryIds.
        payload, _items, native = await self.execute("list_countries", {"f":"json", "page":1, "perpage":100})
        rows = payload.get("Data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ValueError("DHS countries catalogue response does not expose a verifiable row list")
        code, evidence = self._verified_country_mapping(rows, iso3)
        evidence["catalogue_request"] = native
        return code, evidence

    async def execute_semantic(
        self,
        route: dict[str, Any],
        *,
        global_settings: dict[str, Any] | None = None,
        project_settings: dict[str, Any] | None = None,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
        parameters = dict(route.get("parameters") or {})
        native = dict(route.get("native_parameters") or {})
        project_settings = project_settings or {}
        query_text = str(parameters.get("query") or "")
        result_limit = int(parameters.get("result_limit") or 25)
        catalog_size = int(project_settings.get("catalog_page_size") or 5000)

        catalog_payload, _catalog_items, catalog_request = await self.execute(
            "list_indicators", {"f":"json", "page":1, "perpage":catalog_size}
        )
        from ...main import parse_dhs_indicators
        matches = parse_dhs_indicators(catalog_payload, query_text, min(100, max(result_limit, 25)))
        indicator_ids = [str(item.get("id") or "").strip() for item in matches if str(item.get("id") or "").strip()]

        data_params: dict[str, Any] = {"f":"json", "page":1, "perpage":max(result_limit, 25)}
        if indicator_ids:
            data_params["indicatorIds"] = indicator_ids[:100]

        mapping_evidence: dict[str, Any] | None = None
        geo = route.get("canonical_geography") or {}
        if geo and geo.get("iso3"):
            dhs_code, mapping_evidence = await self._resolve_iso3(str(geo["iso3"]))
            data_params["countryIds"] = [dhs_code]

        start = str(parameters.get("date_from") or "")
        end = str(parameters.get("date_to") or "")
        if start or end:
            start_year = int((start or end)[:4])
            end_year = int((end or start)[:4])
            if end_year < start_year or end_year - start_year > 99:
                raise ValueError("DHS semantic survey-year interval is invalid or exceeds 100 years")
            data_params["surveyYears"] = list(range(start_year, end_year + 1))

        if project_settings.get("breakdown"):
            data_params["breakdown"] = project_settings["breakdown"]

        payload, items, data_request = await self.execute("indicator_data", data_params)
        native_record = {
            "operation":"indicator_data",
            "indicator_catalogue_request":catalog_request,
            "indicator_candidates":indicator_ids,
            "geography_mapping":mapping_evidence,
            "data_request":data_request,
            "semantic_native_parameters":native,
        }
        return {"catalogue":catalog_payload, "data":payload}, items[:result_limit], native_record
