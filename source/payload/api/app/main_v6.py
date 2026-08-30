from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from .main import app
from .github_sync import router as github_sync_router
from .api_inventory import router as api_inventory_router

app.version = "6.0.0"
app.description = (
    "Humanitarian Data Platform V6 : acquisition, recherche fédérée, gestion locale, "
    "traitements R/Python, synchronisation GitHub et exploitation de sources "
    "humanitaires et sanitaires par projets. Inventaire API exhaustif accessible "
    "depuis /api-inventory."
)
app.include_router(github_sync_router)
app.include_router(api_inventory_router)
