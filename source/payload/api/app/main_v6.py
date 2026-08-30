from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from pathlib import Path

from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.routing import APIRoute

from .main import (
    CSRF_COOKIE,
    HDP_AUTH_MODE,
    HDP_LOCAL_TOKEN,
    SESSION_COOKIE,
    active_passkey_session,
    app,
    authenticated,
    csrf_token,
    set_operator_session_cookies,
    valid_local_token,
)
from .github_sync import router as github_sync_router
from .api_inventory import router as api_inventory_router
from .v6_notebook_execution import router as v6_notebook_router
from .v6_semantic_api import router as semantic_router


LEGACY_NOTEBOOK_EXECUTION_PATH = "/api/notebooks/{notebook_id}/cells/{cell_index}/executions"
app.router.routes[:] = [
    route
    for route in app.router.routes
    if not (
        isinstance(route, APIRoute)
        and (
            (route.path == LEGACY_NOTEBOOK_EXECUTION_PATH and "POST" in (route.methods or set()))
            or route.path == "/"
        )
    )
]

app.version = "6.0.0-semantic-router-test"
app.description = (
    "Humanitarian Data Platform V6 : acquisition, recherche fédérée, gestion locale, "
    "traitements R/Python, synchronisation GitHub et exploitation de sources "
    "humanitaires et sanitaires par projets. Inventaire API vérifiable accessible "
    "depuis /api-inventory. Routeur sémantique de test accessible depuis /api/semantic."
)
app.include_router(v6_notebook_router)
app.include_router(github_sync_router)
app.include_router(api_inventory_router)
app.include_router(semantic_router)


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX_PATH = STATIC_DIR / "index.html"
LOGIN_PATH = STATIC_DIR / "login.html"


def v6_index_html() -> str:
    """Return the authenticated V6 UI with V6 test controls injected once."""
    html = INDEX_PATH.read_text(encoding="utf-8")
    inventory_marker = '<script src="/api-inventory/native.js"></script>'
    if inventory_marker not in html:
        html = html.replace("</body>", f"{inventory_marker}</body>")
    semantic_marker = 'id="hdp-semantic-router-test-link"'
    if semantic_marker not in html:
        banner = (
            '<div id="hdp-semantic-router-test-link" style="position:fixed;right:18px;bottom:18px;z-index:9999;'
            'background:#172033;border-radius:8px;padding:10px 14px;box-shadow:0 4px 16px #0003">'
            '<a href="/api/semantic/ui" style="color:white;text-decoration:none;font-weight:600">'
            'Routeur sémantique — TEST</a></div>'
        )
        html = html.replace("</body>", f"{banner}</body>")
    return html


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def v6_index(request: Request, token: str = Query(default="", max_length=256)) -> Response:
    """Serve a stable authentication bootstrap before exposing the V6 application.

    In passkey mode an unauthenticated browser receives ``login.html`` and therefore
    never starts the protected V6 API bootstrap.  This preserves the security contract
    from ``main.home`` while still injecting the inventory-driven controls after a
    session has been established.
    """
    if HDP_AUTH_MODE == "passkey":
        session_secret = active_passkey_session(request)
        if not session_secret:
            response = FileResponse(LOGIN_PATH)
            response.delete_cookie(SESSION_COOKIE, path="/")
            response.delete_cookie(CSRF_COOKIE, path="/")
            response.headers["Cache-Control"] = "no-store"
            return response
        response = HTMLResponse(v6_index_html())
        set_operator_session_cookies(response, session_secret)
        return response

    if token:
        if not valid_local_token(token, HDP_LOCAL_TOKEN):
            raise HTTPException(status_code=401, detail="Jeton local HDP invalide")
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            HDP_LOCAL_TOKEN,
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=43_200,
        )
        response.set_cookie(
            CSRF_COOKIE,
            csrf_token(HDP_LOCAL_TOKEN),
            httponly=False,
            samesite="strict",
            secure=False,
            max_age=43_200,
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    if not authenticated(request, HDP_LOCAL_TOKEN):
        raise HTTPException(status_code=401, detail="Ouvrez HDP depuis son raccourci sécurisé")

    response = HTMLResponse(v6_index_html())
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token(HDP_LOCAL_TOKEN),
        httponly=False,
        samesite="strict",
        secure=False,
        max_age=43_200,
    )
    response.headers["Cache-Control"] = "no-store"
    return response
