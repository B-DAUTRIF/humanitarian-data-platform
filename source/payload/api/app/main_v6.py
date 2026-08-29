from __future__ import annotations

"""Point d'entrée HDP V6.

Réutilise l'application historique sans la dupliquer, puis ajoute les modules V6
isolés afin de préserver la compatibilité avec la ligne qualifiée précédente.
"""

from .main import app
from .github_sync import router as github_sync_router

app.include_router(github_sync_router)
