from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from .main import app
from .github_sync import router as github_sync_router

# La V6 étend le socle V5, mais doit exposer sa propre identité de release.
app.version = "6.0.0"
app.description = (
    "Humanitarian Data Platform V6 : acquisition, recherche fédérée, gestion locale, "
    "traitements R/Python, synchronisation GitHub et exploitation de sources "
    "humanitaires et sanitaires par projets."
)
app.include_router(github_sync_router)
