from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from fastapi.routing import APIRoute

from .main import app
from .github_sync import router as github_sync_router
from .api_inventory import router as api_inventory_router
from .v6_notebook_execution import router as v6_notebook_router


# The V5 notebook execution endpoint is retained in source for historical traceability,
# but it contains an obsolete call contract for validate_execution_request(). Remove only
# that concrete route from the assembled V6 application before installing its corrected,
# API-compatible V6 replacement.
LEGACY_NOTEBOOK_EXECUTION_PATH = "/api/notebooks/{notebook_id}/cells/{cell_index}/executions"
app.router.routes[:] = [
    route
    for route in app.router.routes
    if not (
        isinstance(route, APIRoute)
        and route.path == LEGACY_NOTEBOOK_EXECUTION_PATH
        and "POST" in (route.methods or set())
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
