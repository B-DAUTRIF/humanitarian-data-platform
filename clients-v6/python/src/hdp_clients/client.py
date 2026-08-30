from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import httpx


class HDPClientError(RuntimeError):
    """Raised when the HDP server returns an unsuccessful response."""


@dataclass(slots=True)
class HDPClient:
    """Typed client for the local HDP V7 HTTP API.

    The client talks to HDP rather than bypassing it so authentication,
    project preferences, semantic mappings, provenance and provider safety
    rules remain enforced by the server.
    """

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

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        mutation = method.upper() not in {"GET", "HEAD", "OPTIONS"}
        try:
            response = httpx.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._headers(mutation=mutation),
                timeout=self.timeout,
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise HDPClientError(f"HDP inaccessible: {exc}") from exc
        if response.is_error:
            detail: Any
            try:
                payload = response.json()
                detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
            except ValueError:
                detail = response.text
            raise HDPClientError(f"HDP HTTP {response.status_code}: {detail}")
        if response.status_code == 204 or not response.content:
            return None
        content_type = response.headers.get("content-type", "")
        return response.json() if "json" in content_type else response.text

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/health")

    def sources(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/sources")

    def inventory_sources(self) -> dict[str, Any]:
        return self._request("GET", "/api-inventory/sources")

    def inventory(
        self,
        *,
        source: str | None = None,
        query: str | None = None,
        supported: bool | None = None,
        limit: int = 10_000,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if source:
            params["source"] = source
        if query:
            params["q"] = query
        if supported is not None:
            params["supported"] = str(bool(supported)).lower()
        return self._request("GET", "/api-inventory/data", params=params)

    def source_inventory(self, source_slug: str) -> dict[str, Any]:
        return self._request("GET", f"/api-inventory/source/{source_slug}")

    def projects(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/projects")

    def create_project(self, name: str, description: str = "") -> dict[str, Any]:
        return self._request(
            "POST", "/api/projects", json={"name": name, "description": description}
        )

    def project_sources(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/projects/{project_id}/sources")

    def source_settings(self, source_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/source-settings/{source_id}")

    def semantic_contracts(self) -> dict[str, Any]:
        """Return the versioned semantic-router contract and invariants."""
        return self._request("GET", "/api/semantic/contracts")

    def semantic_capabilities(self) -> dict[str, Any]:
        """Return source-by-source semantic capabilities and executability."""
        return self._request("GET", "/api/semantic/capabilities")

    @staticmethod
    def _semantic_body(
        *,
        sources: Iterable[str],
        query: str = "",
        location: str = "",
        date_from: str = "",
        date_to: str = "",
        result_limit: int = 25,
    ) -> dict[str, Any]:
        selected = list(dict.fromkeys(str(source).strip() for source in sources if str(source).strip()))
        if not selected:
            raise ValueError("sources must contain at least one source")
        if not 1 <= int(result_limit) <= 100:
            raise ValueError("result_limit must be between 1 and 100")
        return {
            "sources": selected,
            "query": query,
            "location": location,
            "date_from": date_from,
            "date_to": date_to,
            "result_limit": int(result_limit),
        }

    def semantic_plan(
        self,
        *,
        sources: Iterable[str],
        query: str = "",
        location: str = "",
        date_from: str = "",
        date_to: str = "",
        result_limit: int = 25,
    ) -> dict[str, Any]:
        """Build an auditable semantic Query Plan without contacting providers."""
        body = self._semantic_body(
            sources=sources,
            query=query,
            location=location,
            date_from=date_from,
            date_to=date_to,
            result_limit=result_limit,
        )
        return self._request("POST", "/api/semantic/plan", json=body)

    def semantic_search(
        self,
        *,
        sources: Iterable[str],
        query: str = "",
        location: str = "",
        date_from: str = "",
        date_to: str = "",
        result_limit: int = 25,
    ) -> dict[str, Any]:
        """Execute the V7 semantic router and preserve per-source statuses/provenance."""
        body = self._semantic_body(
            sources=sources,
            query=query,
            location=location,
            date_from=date_from,
            date_to=date_to,
            result_limit=result_limit,
        )
        return self._request("POST", "/api/semantic/search", json=body)

    def search(
        self,
        *,
        project_id: str,
        source: str,
        query: str,
        result_limit: int = 25,
        auto_download: bool = False,
        parameters: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compatibility wrapper for the legacy per-source V6 search endpoint."""
        body = {
            "project_id": project_id,
            "source": source,
            "query": query,
            "result_limit": result_limit,
            "auto_download": auto_download,
            "parameters": dict(parameters or {}),
        }
        return self._request("POST", "/api/search", json=body)

    def federated_search(
        self,
        *,
        project_id: str,
        sources: Iterable[str],
        query: str,
        result_limit: int = 25,
        auto_download: bool = False,
        parameters_by_source: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Compatibility federated search through validated V6 per-source calls."""
        results: list[dict[str, Any]] = []
        for source in sources:
            try:
                value = self.search(
                    project_id=project_id,
                    source=source,
                    query=query,
                    result_limit=result_limit,
                    auto_download=auto_download,
                    parameters=(parameters_by_source or {}).get(source, {}),
                )
                results.append({"source": source, "ok": True, "result": value})
            except HDPClientError as exc:
                results.append({"source": source, "ok": False, "error": str(exc)})
        return results
