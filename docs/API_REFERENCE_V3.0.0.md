# Référence API - Humanitarian Data Platform 3.0.0

## API principale

Base locale : `http://127.0.0.1:<HDP_PORT>`, 8080 par défaut.
Swagger : `/docs`. OpenAPI : `/openapi.json`.

### Système et sources

- `GET /api/health`
- `GET /api/sources`
- `GET /api/source-settings`
- `GET/PUT /api/source-settings/{source_id}`
- `GET /api/projects/{project_id}/sources`
- `GET/PUT /api/projects/{project_id}/sources/{source_id}`
- `POST /api/projects/{project_id}/sources/{source_id}/preview`
- `GET /api/search`

### Projets et intégrations

- `GET/POST /api/projects`
- `PATCH/DELETE /api/projects/{project_id}`
- `GET/PUT /api/projects/{project_id}/preferences`
- `GET/PUT /api/projects/{project_id}/github`
- `POST /api/projects/{project_id}/github/repository`
- `GET/PUT /api/projects/{project_id}/geodata`
- `POST /api/projects/{project_id}/geodata/sync`
- `GET /api/cod/families`
- `GET /api/cod/availability`
- `GET /api/un-m49/entities`

### Acquisitions et ressources

- `GET /api/acquisitions?project_id=...`
- `GET /api/resources?project_id=...`
- `GET /api/resources/{resource_id}/file`
- `POST /api/resources/{resource_id}/verify`
- `DELETE /api/resources/{resource_id}`
- `GET /api/projects/{project_id}/storage`

### Scripts et exécutions

- `GET/POST /api/projects/{project_id}/scripts`
- `PATCH/DELETE /api/scripts/{script_id}`
- `GET /api/scripts/{script_id}/versions`
- `GET/POST /api/scripts/{script_id}/executions`
- `GET /api/executions/{execution_id}`
- `GET /api/executions/{execution_id}/report`
- `GET/PUT /api/projects/{project_id}/execution-settings`

### Planifications, RSS et chronologie

- `GET/POST /api/projects/{project_id}/schedules`
- `PATCH/DELETE /api/schedules/{schedule_id}`
- `POST /api/schedules/{schedule_id}/run`
- `GET /api/schedules/{schedule_id}/runs`
- `GET /api/rss/catalog`
- `GET/POST /api/projects/{project_id}/rss/subscriptions`
- `PATCH/DELETE /api/rss/subscriptions/{subscription_id}`
- `POST /api/rss/subscriptions/{subscription_id}/fetch`
- `GET /api/projects/{project_id}/rss/items`
- `GET /api/projects/{project_id}/timeline`

### Cartographie

- `GET /api/map/config`
- `POST /api/resources/{resource_id}/map/import`
- `GET /api/projects/{project_id}/map/layers`
- `GET /api/map/layers/{layer_id}/geojson`
- `GET /api/map/layers/{layer_id}/export`

`GET /api/search`, les synchronisations et les exécutions manuelles ont des
effets persistants. Les réponses d'erreur FastAPI utilisent `detail`.

## Passerelle GitHub

Base locale : `http://127.0.0.1:<HDP_GITHUB_API_PORT>`, 8091 par défaut.
Swagger : `/docs`. OpenAPI : `/openapi.json`.

- `GET /health`
- `GET /repository`
- `GET /branches`
- `GET /commits`
- `GET /issues`
- `POST /issues`, verrouillé par défaut
- `GET /pulls`
- `GET /releases`
- `GET /workflows`
- `POST /workflows/{workflow_id}/dispatch`, verrouillé par défaut
- `GET /contents/{content_path}`
- `GET /rate-limit`

Les routes acceptent `owner` et `repo` facultatifs. Les listes utilisent `page`
et `per_page` borné à 100. Voir [GITHUB_API.md](GITHUB_API.md) pour les
permissions et la configuration.
