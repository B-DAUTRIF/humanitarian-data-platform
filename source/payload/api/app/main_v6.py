from __future__ import annotations

"""Point d'entrée de compatibilité HDP V7.

Le nom historique ``main_v6`` est conservé afin de ne pas casser les outils de
qualification et les installations existantes. Il initialise désormais le runtime V7.
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
from .providers.dhs.api import router as dhs_provider_router
from .providers.gdacs.api import router as gdacs_provider_router
from .providers.reliefweb.api import router as reliefweb_provider_router
from .providers.un_sdg.api import router as un_sdg_provider_router
from .providers.unhcr.api import router as unhcr_provider_router
from .providers.unicef_sdmx.api import router as unicef_sdmx_provider_router
from .providers.who_gho.api import router as who_gho_provider_router
from .providers.world_bank_health.api import router as world_bank_health_provider_router
from .v6_notebook_execution import router as v6_notebook_router
from .v6_semantic_api import router as semantic_router
from .v7_semantic_ui import router as semantic_ui_router
from .v7_migrations import apply_v7_migrations
from .v7_semantic_jobs import recover_abandoned_semantic_jobs, router as semantic_jobs_router
from .v7_trace import router as trace_router, trace_event, trace_http_middleware

LEGACY_CONTRACT_VERSION = "6.0.0"
ACTIVE_APPLICATION_VERSION = "7.0.0"

LEGACY_NOTEBOOK_EXECUTION_PATH = "/api/notebooks/{notebook_id}/cells/{cell_index}/executions"
SEMANTIC_UI_PATH = "/api/semantic/ui"
app.router.routes[:] = [
    route
    for route in app.router.routes
    if not (
        isinstance(route, APIRoute)
        and ((route.path == LEGACY_NOTEBOOK_EXECUTION_PATH and "POST" in (route.methods or set())) or route.path == "/")
    )
]

app.version = ACTIVE_APPLICATION_VERSION
app.description = (
    "Humanitarian Data Platform V7 : acquisition, recherche fédérée, gestion locale, "
    "traitements R/Python, synchronisation GitHub et exploitation de sources humanitaires et sanitaires par projets. "
    "Inventaire API vérifiable accessible depuis /api-inventory. Routeur sémantique V7 accessible depuis /api/semantic. "
    "APIs fournisseur spécialisées disponibles sous /api/providers pour ReliefWeb, World Bank Health, DHS, GDACS, "
    "UN SDG, UNHCR, UNICEF SDMX et WHO GHO. Traçage diagnostic JSONL disponible sous /api/trace."
)
app.middleware("http")(trace_http_middleware)
app.include_router(v6_notebook_router)
app.include_router(github_sync_router)
app.include_router(api_inventory_router)
app.include_router(semantic_router)
app.include_router(trace_router)

app.router.routes[:] = [
    route
    for route in app.router.routes
    if not (isinstance(route, APIRoute) and route.path == SEMANTIC_UI_PATH and "GET" in (route.methods or set()))
]
app.include_router(semantic_ui_router)
app.include_router(semantic_jobs_router)
app.include_router(reliefweb_provider_router)
app.include_router(world_bank_health_provider_router)
app.include_router(dhs_provider_router)
app.include_router(gdacs_provider_router)
app.include_router(un_sdg_provider_router)
app.include_router(unhcr_provider_router)
app.include_router(unicef_sdmx_provider_router)
app.include_router(who_gho_provider_router)


@app.on_event("startup")
def apply_v7_schema() -> None:
    trace_event("runtime.startup.begin", application_version=ACTIVE_APPLICATION_VERSION)
    apply_v7_migrations()
    recover_abandoned_semantic_jobs()
    trace_event("runtime.startup.ready", application_version=ACTIVE_APPLICATION_VERSION)


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX_PATH = STATIC_DIR / "index.html"
LOGIN_PATH = STATIC_DIR / "login.html"


def v6_index_html() -> str:
    html = INDEX_PATH.read_text(encoding="utf-8")
    inventory_marker = '<script src="/api-inventory/native.js"></script>'
    if inventory_marker not in html:
        html = html.replace("</body>", f"{inventory_marker}</body>")
    semantic_marker = 'id="hdp-semantic-router-link"'
    if semantic_marker not in html:
        banner = (
            '<div id="hdp-semantic-router-link" style="position:fixed;right:18px;bottom:18px;z-index:9999;'
            'background:#172033;border-radius:8px;padding:10px 14px;box-shadow:0 4px 16px #0003">'
            '<a href="/api/semantic/ui" style="color:white;text-decoration:none;font-weight:600">Routeur sémantique V7</a> · '
            '<a href="/api/providers/reliefweb/ui" style="color:white;text-decoration:none">ReliefWeb</a> · '
            '<a href="/api/providers/world-bank-health/ui" style="color:white;text-decoration:none">World Bank</a> · '
            '<a href="/api/trace/export" style="color:white;text-decoration:none">Exporter log diagnostic</a> · '
            '<a href="#sources" style="color:white;text-decoration:none">Sources</a></div>'
        )
        html = html.replace("</body>", f"{banner}</body>")
    return html


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def v6_index(request: Request, token: str = Query(default="", max_length=256)) -> Response:
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
        response.set_cookie(SESSION_COOKIE, HDP_LOCAL_TOKEN, httponly=True, samesite="strict", secure=False, max_age=43_200)
        response.set_cookie(CSRF_COOKIE, csrf_token(HDP_LOCAL_TOKEN), httponly=False, samesite="strict", secure=False, max_age=43_200)
        response.headers["Cache-Control"] = "no-store"
        return response

    if not authenticated(request, HDP_LOCAL_TOKEN):
        raise HTTPException(status_code=401, detail="Ouvrez HDP depuis son raccourci sécurisé")

    response = HTMLResponse(v6_index_html())
    response.set_cookie(CSRF_COOKIE, csrf_token(HDP_LOCAL_TOKEN), httponly=False, samesite="strict", secure=False, max_age=43_200)
    response.headers["Cache-Control"] = "no-store"
    return response
