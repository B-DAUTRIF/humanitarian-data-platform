# Référence API V5

Toutes les routes, sauf santé/statique/amorçage local, exigent la session HDP. Toute mutation exige `X-HDP-CSRF: 1` et une origine locale cohérente.

| Méthode | Route | Fonction |
|---|---|---|
| GET | `/api/hdx/datagrid/taxonomy` | Dimensions et politique de classification |
| POST | `/api/projects/{project_id}/hdx/datagrid/search` | Recherche HDX et indexation des métadonnées |
| GET | `/api/projects/{project_id}/hdx/metadata` | Métadonnées jeu/fichier du projet |
| POST | `/api/projects/{project_id}/hdx/aggregation-plan` | Contrat de compatibilité avant agrégation |
| GET/POST | `/api/projects/{project_id}/signals/rules` | Lire/créer les règles |
| GET/POST | `/api/projects/{project_id}/signals` | Lire/ingérer des événements |
| GET | `/api/signals/prompts` | Patrons contraints et référence HDX |
| POST | `/api/projects/{project_id}/signals/syndromic-snapshot` | Vue syndromique bornée |
| GET/POST | `/api/projects/{project_id}/notebooks` | Lister/créer des notebooks |
| GET | `/api/notebooks/{notebook_id}` | Lire la révision courante |
| POST | `/api/notebooks/{notebook_id}/revisions` | Créer une révision immuable |
| POST | `/api/notebooks/{notebook_id}/cells/{cell_index}/executions` | Exécuter une cellule confirmée |

La route historique `GET /api/search` répond désormais 405 ; l’acquisition avec effets de bord utilise exclusivement `POST /api/acquisitions`.
