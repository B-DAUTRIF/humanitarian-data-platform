from __future__ import annotations

import httpx
import pytest

from hdp_clients import HDPClient


def response(request: httpx.Request, payload, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload, request=request)


def test_inventory_filters(monkeypatch):
    captured = {}
    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return response(httpx.Request(method, url), {"total": 1, "rows": [{"Paramètre": "q"}]})
    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient("http://localhost:8080", token="secret")
    result = client.inventory(source="hdx", query="package", supported=True)
    assert result["total"] == 1
    assert captured["params"]["source"] == "hdx"
    assert captured["params"]["q"] == "package"
    assert captured["params"]["supported"] == "true"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["User-Agent"] == "HDPClientsPython/7.0.0"


def test_search_maps_parameters_and_csrf(monkeypatch):
    captured = {}
    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return response(httpx.Request(method, url), {"item_count": 0, "items": []})
    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient(token="secret")
    client.search(project_id="00000000-0000-4000-8000-000000000001", source="hdx", query="cholera", parameters={"fq": "groups:health"})
    assert captured["method"] == "POST"
    assert captured["json"]["parameters"]["fq"] == "groups:health"
    assert captured["headers"]["X-HDP-CSRF"] == "1"


def test_semantic_plan_uses_v7_contract(monkeypatch):
    captured = {}
    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return response(httpx.Request(method, url), {"contract_version": "7.0", "query_fingerprint": "abc", "intent": {"geography": {"name": "Rwanda", "iso3": "RWA", "m49": "646"}}, "routes": []})
    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient(token="secret")
    result = client.semantic_plan(sources=["reliefweb", "reliefweb", "world-bank-health"], query="malaria", location="RWA", date_from="2020-01-01", date_to="2025-12-31", project_id="00000000-0000-4000-8000-000000000001")
    assert result["query_fingerprint"] == "abc"
    assert captured["url"].endswith("/api/semantic/plan")
    assert captured["json"]["sources"] == ["reliefweb", "world-bank-health"]
    assert captured["json"]["location"] == "RWA"
    assert captured["json"]["project_id"].endswith("0001")
    assert captured["headers"]["X-HDP-CSRF"] == "1"


def test_semantic_search_preserves_source_statuses(monkeypatch):
    captured = {}
    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return response(httpx.Request(method, url), {"status": "partial", "sources": [{"source": "reliefweb", "status": "success", "item_count": 3}, {"source": "dhs", "status": "blocked_missing_mapping", "item_count": 0}], "item_count": 3})
    monkeypatch.setattr(httpx, "request", fake_request)
    result = HDPClient(token="secret").semantic_search(sources=["reliefweb", "dhs"], location="Rwanda")
    assert result["status"] == "partial"
    assert result["sources"][1]["status"] == "blocked_missing_mapping"
    assert captured["url"].endswith("/api/semantic/search")


def test_semantic_job_lifecycle_methods(monkeypatch):
    calls = []
    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        request = httpx.Request(method, url)
        if url.endswith("/api/semantic/jobs"):
            return response(request, {"job_id": "11111111-1111-4111-8111-111111111111", "status": "queued"})
        if url.endswith("/cancel"):
            return response(request, {"status": "cancelled", "cancel_requested": True})
        return response(request, {"status": "running", "progress": 40})
    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient(token="secret")
    created = client.create_semantic_job(sources=["world-bank-health"], query="malaria", location="RWA")
    job_id = created["job_id"]
    assert client.semantic_job(job_id)["progress"] == 40
    assert client.cancel_semantic_job(job_id)["cancel_requested"] is True
    assert calls[0][2]["headers"]["X-HDP-CSRF"] == "1"


def test_semantic_reproducibility_and_exports(monkeypatch):
    def fake_request(method, url, **kwargs):
        request = httpx.Request(method, url)
        if "/reproducibility/python" in url:
            return httpx.Response(200, text="print('ok')", headers={"content-type": "text/x-python"}, request=request)
        if url.endswith("/export/csv"):
            return httpx.Response(200, text="title\nA\n", headers={"content-type": "text/csv"}, request=request)
        return response(request, {"type": "FeatureCollection", "features": []})
    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient(token="secret")
    assert "print" in client.semantic_reproducibility("python", sources=["world-bank-health"], location="RWA")
    assert "title" in client.export_semantic_job("11111111-1111-4111-8111-111111111111", "csv")
    with pytest.raises(ValueError, match="python"):
        client.semantic_reproducibility("bash", sources=["world-bank-health"])
    with pytest.raises(ValueError, match="json"):
        client.export_semantic_job("job", "xlsx")


def test_semantic_request_rejects_empty_sources_and_invalid_limit():
    client = HDPClient()
    with pytest.raises(ValueError, match="at least one source"):
        client.semantic_plan(sources=[])
    with pytest.raises(ValueError, match="between 1 and 100"):
        client.semantic_search(sources=["reliefweb"], result_limit=101)


def test_federated_search_preserves_partial_errors(monkeypatch):
    client = HDPClient()
    def fake_search(self, **kwargs):
        if kwargs["source"] == "broken":
            from hdp_clients import HDPClientError
            raise HDPClientError("unavailable")
        return {"source": kwargs["source"]}
    monkeypatch.setattr(HDPClient, "search", fake_search)
    result = client.federated_search(project_id="p", sources=["hdx", "broken"], query="cholera")
    assert result[0]["ok"] is True
    assert result[1]["ok"] is False
