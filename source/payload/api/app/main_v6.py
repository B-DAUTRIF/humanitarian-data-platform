from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute

from .main import app
from .github_sync import router as github_sync_router
from .api_inventory import router as api_inventory_router
from .v6_notebook_execution import router as v6_notebook_router


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

app.version = "6.0.0"
app.description = (
    "Humanitarian Data Platform V6 : acquisition, recherche fédérée, gestion locale, "
    "traitements R/Python, synchronisation GitHub et exploitation de sources "
    "humanitaires et sanitaires par projets. Inventaire API vérifiable accessible "
    "depuis /api-inventory."
)
app.include_router(v6_notebook_router)
app.include_router(github_sync_router)
app.include_router(api_inventory_router)


INDEX_PATH = Path(__file__).resolve().parent.parent / "static" / "index.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def v6_index() -> str:
    """Serve the V6 UI and inject the inventory-driven native source controls.

    The injection is done server-side so the installed UI cannot silently diverge from
    the versioned API inventory. The dedicated /api-inventory page remains available
    for audit/export, while the same schema is now exposed directly in Source settings.
    """
    html = INDEX_PATH.read_text(encoding="utf-8")
    marker = '<script src="/api-inventory/native.js"></script>'
    if marker not in html:
        html = html.replace("</body>", f"{marker}</body>")
    return html
