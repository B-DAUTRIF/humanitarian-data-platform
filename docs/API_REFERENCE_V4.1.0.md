# Référence API - Humanitarian Data Platform 4.1.0

L'API FastAPI est liée à l'adresse locale publiée par Compose. Sa documentation
interactive se trouve sur `/docs` et son contrat OpenAPI sur `/openapi.json`.

## Configuration, sources et technologies

| Méthode | Chemin | Fonction |
|---|---|---|
| GET | `/api/health` | version, base, planificateur et runners |
| GET | `/api/sources` | catalogue enrichi, capacités, schémas et liens officiels |
| GET | `/api/technologies` | 25 ressources et 87 liens regroupés en 13 catégories |
| GET | `/api/source-settings` | valeurs globales expurgées, séparées par source |
| GET/PUT | `/api/source-settings/{source_id}` | lire ou modifier le transport d'une source |
| GET/PUT | `/api/projects/{project_id}/sources/{source_id}` | paramètres métier du projet |
| POST | `/api/projects/{project_id}/sources/{source_id}/preview` | URL, cURL, Python et R sans secret |

Les réponses de catalogue exposent `registry_version`, `verified_at`,
`global_settings_schema`, `project_schema`, `technical_profile`,
`official_links` et les valeurs par défaut. L'API refuse les propriétés
inconnues et applique les bornes du schéma.

## Recherche fédérée

`POST /api/projects/{project_id}/federated-search` accepte les critères communs
et un objet `source_parameters` individualisé :

```json
{
  "sources": ["who-gho", "unicef-sdmx", "gdacs"],
  "query": "cholera",
  "date_from": "2026-01-01",
  "date_to": "2026-08-15",
  "location": "Mozambique",
  "result_limit_per_source": 25,
  "auto_download": false,
  "source_parameters": {
    "unicef-sdmx": {"agency": "UNICEF", "detail": "allstubs"},
    "gdacs": {"event_types": ["FL"], "alert_levels": ["Orange", "Red"]}
  }
}
```

La réponse brute de chaque source est conservée séparément avec SHA-256 et
paramètres effectifs. Une panne partielle n'efface pas les réponses déjà reçues.

## Autres familles de routes

- bibliothèque : `/api/projects/{project_id}/uploads`, `/api/resources` et
  `/api/resources/{resource_id}/*` ;
- traitement : `/api/processing/operations` et
  `/api/projects/{project_id}/processing-runs` ;
- carte : `/api/projects/{project_id}/map/layers` et `/api/map/layers/*` ;
- SQL : `/api/projects/{project_id}/sql/schema` et `/sql/query` ;
- scripts, planifications, RSS et chronologie : routes historiques compatibles.

Python et R s'exécutent dans des runners sans réseau et sans privilège, avec
limites de temps et de sortie. Le navigateur ne reçoit jamais la chaîne de
connexion PostgreSQL ni les secrets des connecteurs.
