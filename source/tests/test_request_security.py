from __future__ import annotations

import sys
import types
import unittest
from http.cookies import SimpleCookie
from pathlib import Path


try:
    from starlette.requests import Request
except ModuleNotFoundError:
    class Request:  # type: ignore[no-redef]
        def __init__(self, scope: dict[str, object]) -> None:
            self.method = str(scope["method"])
            self.headers = {
                name.decode("ascii"): value.decode("latin-1")
                for name, value in scope["headers"]  # type: ignore[union-attr]
            }
            parsed = SimpleCookie()
            parsed.load(self.headers.get("cookie", ""))
            self.cookies = {name: morsel.value for name, morsel in parsed.items()}

    starlette = types.ModuleType("starlette")
    starlette_requests = types.ModuleType("starlette.requests")
    starlette_requests.Request = Request
    sys.modules["starlette"] = starlette
    sys.modules["starlette.requests"] = starlette_requests


APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.request_security import (  # noqa: E402
    CSRF_COOKIE,
    allowed_hosts,
    csrf_is_valid,
    csrf_token,
)


def make_request(method: str, headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/api/projects",
        "raw_path": b"/api/projects",
        "query_string": b"",
        "server": ("localhost", 18081),
        "client": ("127.0.0.1", 50000),
        "headers": [
            (name.casefold().encode("ascii"), value.encode("latin-1"))
            for name, value in headers.items()
        ],
    }
    return Request(scope)


class RequestSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.local_token = "l" * 64
        self.csrf = csrf_token(self.local_token)
        self.allowed = allowed_hosts()

    def test_double_submit_token_accepts_same_origin_mutation(self) -> None:
        request = make_request(
            "POST",
            {
                "host": "localhost:18081",
                "origin": "http://localhost:18081",
                "sec-fetch-site": "same-origin",
                "x-hdp-csrf": self.csrf,
                "cookie": f"{CSRF_COOKIE}={self.csrf}",
            },
        )
        self.assertTrue(csrf_is_valid(request, self.allowed, self.local_token))

    def test_legacy_header_remains_local_only(self) -> None:
        request = make_request(
            "POST",
            {
                "host": "127.0.0.1:18081",
                "origin": "http://127.0.0.1:18081",
                "sec-fetch-site": "same-origin",
                "x-hdp-csrf": "1",
            },
        )
        self.assertTrue(csrf_is_valid(request, self.allowed, self.local_token))

    def test_missing_mismatched_and_cross_site_tokens_are_rejected(self) -> None:
        cases = (
            {
                "host": "localhost:18081",
                "origin": "http://localhost:18081",
                "sec-fetch-site": "same-origin",
            },
            {
                "host": "localhost:18081",
                "origin": "http://localhost:18081",
                "sec-fetch-site": "same-origin",
                "x-hdp-csrf": self.csrf,
                "cookie": f"{CSRF_COOKIE}=incorrect",
            },
            {
                "host": "localhost:18081",
                "origin": "https://example.test",
                "sec-fetch-site": "cross-site",
                "x-hdp-csrf": self.csrf,
                "cookie": f"{CSRF_COOKIE}={self.csrf}",
            },
        )
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertFalse(
                    csrf_is_valid(
                        make_request("POST", headers), self.allowed, self.local_token
                    )
                )

    def test_safe_method_does_not_require_csrf(self) -> None:
        self.assertTrue(
            csrf_is_valid(
                make_request("GET", {"host": "localhost:18081"}),
                self.allowed,
                self.local_token,
            )
        )


if __name__ == "__main__":
    unittest.main()
