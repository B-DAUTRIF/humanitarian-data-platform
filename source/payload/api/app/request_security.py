from __future__ import annotations

import hmac
from collections.abc import Iterable
from urllib.parse import urlparse

from starlette.requests import Request


SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
PUBLIC_PATHS = frozenset({"/api/health"})
SESSION_COOKIE = "hdp_session"
CSRF_COOKIE = "hdp_csrf"
CSRF_HEADER = "x-hdp-csrf"


def normalized_host(value: str) -> str:
    host = value.strip().casefold()
    if host.startswith("["):
        end = host.find("]")
        return host[1:end] if end >= 0 else host
    return host.split(":", 1)[0]


def allowed_hosts(extra_hosts: Iterable[str] = ()) -> frozenset[str]:
    values = {"127.0.0.1", "localhost", "::1", "api"}
    values.update(normalized_host(value) for value in extra_hosts if value.strip())
    return frozenset(values)


def valid_local_token(candidate: str, expected: str) -> bool:
    return bool(candidate and expected) and hmac.compare_digest(candidate, expected)


def bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, value = authorization.partition(" ")
    return value.strip() if scheme.casefold() == "bearer" else ""


def authenticated(request: Request, expected_token: str) -> bool:
    return valid_local_token(bearer_token(request), expected_token) or valid_local_token(
        request.cookies.get(SESSION_COOKIE, ""), expected_token
    )


def csrf_token(local_token: str) -> str:
    if not local_token:
        return ""
    return hmac.digest(
        local_token.encode("utf-8"), b"hdp-csrf-v1", "sha256"
    ).hex()


def origin_is_local(
    request: Request, allowed: frozenset[str], expected_origin: str = ""
) -> bool:
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        # Non-browser clients remain usable only with the bearer/session and
        # the non-safelisted CSRF header checked separately.
        return True
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or normalized_host(parsed.netloc) not in allowed:
        return False
    if expected_origin:
        expected = urlparse(expected_origin)
        return (
            parsed.scheme.casefold() == expected.scheme.casefold()
            and parsed.netloc.casefold() == expected.netloc.casefold()
        )
    return True


def csrf_is_valid(
    request: Request,
    allowed: frozenset[str],
    expected_secret: str,
    *,
    expected_origin: str = "",
    allow_legacy: bool = True,
) -> bool:
    if request.method.upper() in SAFE_METHODS:
        return True
    fetch_site = request.headers.get("sec-fetch-site", "").casefold()
    if fetch_site and fetch_site not in {"same-origin", "same-site", "none"}:
        return False
    if not origin_is_local(request, allowed, expected_origin):
        return False
    submitted = request.headers.get(CSRF_HEADER, "")
    expected = csrf_token(expected_secret)
    cookie = request.cookies.get(CSRF_COOKIE, "")
    if valid_local_token(submitted, expected) and valid_local_token(cookie, expected):
        return True
    # Compatibilité avec l'interface 5.0.1 déjà ouverte. Ce chemin reste borné
    # par SameSite=Strict, le contrôle Fetch Metadata et l'origine locale.
    return allow_legacy and submitted == "1"
