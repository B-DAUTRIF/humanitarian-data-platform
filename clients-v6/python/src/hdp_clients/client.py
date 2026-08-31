from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import httpx


class HDPClientError(RuntimeError):
    """Raised when the HDP server returns an unsuccessful response."""


@dataclass(slots=True)
class HDPClient:
    """Typed client for the local HDP V7 HTTP API."""
    base_url: str = "http://localhost:8080"
    token: str | None = None
    timeout: float = 60.0

    def _headers(self, *, mutation: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "HDPClientsPython/7.0.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            if mutation:
                headers["X-HDP-CSRF"] = "1"
        return headers

    def _request(self, method: str, path: str, *, params: Mapping[str, Any] | None = None, json: Any = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            response = httpx.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._headers(mutation=method.upper() not in {"GET", "HEAD", "OPTIONS"}),
                timeout=self.timeout,
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise HDPClientError(f"HDP inaccessible: {exc}") from exc
        if response.is_error:
            try:
                payload = response.json()
                detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
            except ValueError:
                detail = response.text
            raise HDPClientError(f"HDP HTTP {response.status_code}: {detail}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json() if "json" in response.headers.get("content-type", "") else response.text

    def health(self): return self._request("GET", "/api/health")
    def sources(self): return self._request("GET", "/api/sources")
    def inventory_sources(self): return self._request("GET", "/api-inventory/sources")
    def source_inventory(self, source_slug: str): return self._request("GET", f"/api-inventory/source/{source_slug}")
    def projects(self): return self._request("GET", "/api/projects")
    def create_project(self, name: str, description: str = ""): return self._request("POST", "/api/projects", json={"name": name, "description": description})
    def project_sources(self, project_id: str): return self._request("GET", f"/api/projects/{project_id}/sources")
    def source_settings(self, source_id: str): return self._request("GET", f"/api/source-settings/{source_id}")

    def inventory(self, *, source=None, query=None, supported=None, limit=10000, offset=0):
        params = {"limit": limit, "offset": offset}
        if source: params["source"] = source
        if query: params["q"] = query
        if supported is not None: params["supported"] = str(bool(supported)).lower()
        return self._request("GET", "/api-inventory/data", params=params)

    def reliefweb_descriptor(self): return self._request("GET", "/api/providers/reliefweb/descriptor")
    def reliefweb_effective_configuration(self, *, project_id=None): return self._request("GET", "/api/providers/reliefweb/configuration/effective", params={"project_id": project_id} if project_id else None)
    def reliefweb_search(self, *, content_type="reports", parameters=None, project_id=None):
        body = {"content_type": content_type, "parameters": dict(parameters or {})}
        if project_id: body["project_id"] = project_id
        return self._request("POST", "/api/providers/reliefweb/search", json=body)
    def reliefweb_item(self, content_type, item_id, *, fields_include=None, fields_exclude=None, profile=None, project_id=None):
        parameters = {}
        if fields_include: parameters["fields_include"] = list(fields_include)
        if fields_exclude: parameters["fields_exclude"] = list(fields_exclude)
        if profile: parameters["profile"] = profile
        body = {"parameters": parameters}
        if project_id: body["project_id"] = project_id
        return self._request("POST", f"/api/providers/reliefweb/item/{content_type}/{item_id}", json=body)

    def world_bank_descriptor(self):
        return self._request("GET", "/api/providers/world-bank-health/descriptor")

    def world_bank_effective_configuration(self, *, project_id=None):
        return self._request("GET", "/api/providers/world-bank-health/configuration/effective", params={"project_id": project_id} if project_id else None)

    def world_bank_observations(
        self,
        *,
        country: str,
        indicator: str,
        date: str = "",
        source: int = 2,
        page: int = 1,
        per_page: int = 50,
        mrv: int | None = None,
        mrnev: int | None = None,
        gapfill: bool = False,
        frequency: str = "",
        footnote: bool = False,
        language: str = "en",
        project_id: str | None = None,
    ):
        body = {
            "country": country,
            "indicator": indicator,
            "date": date,
            "source": source,
            "page": page,
            "per_page": per_page,
            "mrv": mrv,
            "mrnev": mrnev,
            "gapfill": gapfill,
            "frequency": frequency,
            "footnote": footnote,
            "language": language,
        }
        if project_id: body["project_id"] = project_id
        return self._request("POST", "/api/providers/world-bank-health/observations", json=body)

    def world_bank_metadata(self, *, query: str, source: int = 2, page: int = 1, per_page: int = 1000, language: str = "en", project_id: str | None = None):
        body = {"query": query, "source": source, "page": page, "per_page": per_page, "language": language}
        if project_id: body["project_id"] = project_id
        return self._request("POST", "/api/providers/world-bank-health/metadata", json=body)

    def world_bank_indicators(self, *, source: int = 2, page: int = 1, per_page: int = 1000, language: str = "en"):
        return self._request("GET", "/api/providers/world-bank-health/indicators", params={"source": source, "page": page, "per_page": per_page, "language": language})

    def world_bank_countries(self, *, identifier: str = "", page: int = 1, per_page: int = 1000, language: str = "en"):
        return self._request("GET", "/api/providers/world-bank-health/countries", params={"identifier": identifier, "page": page, "per_page": per_page, "language": language})

    def world_bank_topics(self, *, identifier: str = "", page: int = 1, per_page: int = 1000, language: str = "en"):
        return self._request("GET", "/api/providers/world-bank-health/topics", params={"identifier": identifier, "page": page, "per_page": per_page, "language": language})

    def world_bank_sources(self, *, identifier: str = "", page: int = 1, per_page: int = 1000, language: str = "en"):
        return self._request("GET", "/api/providers/world-bank-health/sources", params={"identifier": identifier, "page": page, "per_page": per_page, "language": language})

    def world_bank_indicator_metadata(self, indicator: str, *, source: int = 2, language: str = "en"):
        return self._request("GET", f"/api/providers/world-bank-health/indicator/{indicator}/metadata", params={"source": source, "language": language})

    def world_bank_geography_vocabulary(self, *, language: str = "en", refresh: bool = False):
        return self._request("GET", "/api/providers/world-bank-health/geography-vocabulary", params={"language": language, "refresh": str(bool(refresh)).lower()})

    def semantic_contracts(self): return self._request("GET", "/api/semantic/contracts")
    def semantic_capabilities(self): return self._request("GET", "/api/semantic/capabilities")

    @staticmethod
    def _semantic_body(*, sources: Iterable[str], query="", location="", date_from="", date_to="", result_limit=25, project_id=None):
        selected = list(dict.fromkeys(str(s).strip() for s in sources if str(s).strip()))
        if not selected: raise ValueError("sources must contain at least one source")
        if not 1 <= int(result_limit) <= 100: raise ValueError("result_limit must be between 1 and 100")
        body = {"sources": selected, "query": query, "location": location, "date_from": date_from, "date_to": date_to, "result_limit": int(result_limit)}
        if project_id: body["project_id"] = project_id
        return body

    def semantic_plan(self, **kwargs): return self._request("POST", "/api/semantic/plan", json=self._semantic_body(**kwargs))
    def semantic_search(self, **kwargs): return self._request("POST", "/api/semantic/search", json=self._semantic_body(**kwargs))
    def create_semantic_job(self, **kwargs): return self._request("POST", "/api/semantic/jobs", json=self._semantic_body(**kwargs))
    def semantic_job(self, job_id): return self._request("GET", f"/api/semantic/jobs/{job_id}")
    def cancel_semantic_job(self, job_id): return self._request("POST", f"/api/semantic/jobs/{job_id}/cancel")
    def semantic_reproducibility(self, language, **kwargs):
        if language.casefold() not in {"python", "r"}: raise ValueError("language must be 'python' or 'r'")
        return self._request("POST", f"/api/semantic/jobs/reproducibility/{language.casefold()}", json=self._semantic_body(**kwargs))
    def export_semantic_job(self, job_id, format_name="json"):
        if format_name.casefold() not in {"json", "csv", "geojson"}: raise ValueError("format_name must be json, csv or geojson")
        return self._request("GET", f"/api/semantic/jobs/{job_id}/export/{format_name.casefold()}")
    def search(self, *, project_id, source, query, result_limit=25, auto_download=False, parameters=None):
        return self._request("POST", "/api/search", json={"project_id": project_id, "source": source, "query": query, "result_limit": result_limit, "auto_download": auto_download, "parameters": dict(parameters or {})})
    def federated_search(self, *, project_id, sources, query, result_limit=25, auto_download=False, parameters_by_source=None):
        results = []
        for source in sources:
            try:
                results.append({"source": source, "ok": True, "result": self.search(project_id=project_id, source=source, query=query, result_limit=result_limit, auto_download=auto_download, parameters=(parameters_by_source or {}).get(source, {}))})
            except HDPClientError as exc:
                results.append({"source": source, "ok": False, "error": str(exc)})
        return results
