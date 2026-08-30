from __future__ import annotations

import httpx

from hdp_clients import HDPClient


def response(request: httpx.Request, payload, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload, request=request)


def test_inventory_filters(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        request = httpx.Request(method, url)
        return response(request, {"total": 1, "rows": [{"Paramètre": "q"}]})

    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient("http://localhost:8080", token="secret")
    result = client.inventory(source="hdx", query="package", supported=True)
    assert result["total"] == 1
    assert captured["params"]["source"] == "hdx"
    assert captured["params"]["q"] == "package"
    assert captured["params"]["supported"] == "true"
    assert captured["headers"]["Authorization"] == "Bearer secret"


def test_search_maps_parameters_and_csrf(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        request = httpx.Request(method, url)
        return response(request, {"item_count": 0, "items": []})

    monkeypatch.setattr(httpx, "request", fake_request)
    client = HDPClient(token="secret")
    client.search(
        project_id="00000000-0000-4000-8000-000000000001",
        source="hdx",
        query="cholera",
        parameters={"fq": "groups:health"},
    )
    assert captured["method"] == "POST"
    assert captured["json"]["parameters"]["fq"] == "groups:health"
    assert captured["headers"]["X-HDP-CSRF"] == "1"


def test_federated_search_preserves_partial_errors(monkeypatch):
    client = HDPClient()

    def fake_search(self, **kwargs):
        if kwargs["source"] == "broken":
            from hdp_clients import HDPClientError
            raise HDPClientError("unavailable")
        return {"source": kwargs["source"]}

    monkeypatch.setattr(HDPClient, "search", fake_search)
    result = client.federated_search(
        project_id="p", sources=["hdx", "broken"], query="cholera"
    )
    assert result[0]["ok"] is True
    assert result[1]["ok"] is False
