# Référence API - Humanitarian Data Platform 4.0.0

L’API principale FastAPI écoute uniquement sur l’adresse locale publiée par
Compose. Les UUID sont ceux du projet actif. Les erreurs de validation utilisent
les statuts HTTP 4xx ; un connecteur configuré sans secret requis retourne 503.

## Santé et catalogue

| Méthode | Chemin | Fonction |
|---|---|---|
| GET | `/api/health` | version, base, planificateur et runners |
| GET | `/api/sources` | catalogue enrichi et contrats de capacités |
| GET | `/api/source-settings` | configuration expurgée des connecteurs |
| GET/PUT | `/api/projects/{project_id}/sources/{source_id}` | paramètres par projet |
| POST | `/api/projects/{project_id}/sources/{source_id}/preview` | requête prévisualisée sans secret |

## Recherche et acquisitions

`POST /api/projects/{project_id}/federated-search` reçoit :

```json
{
  "sources": ["hdx", "who-gho", "gdacs"],
  "query": "cholera",
  "date_from": "2026-01-01",
  "date_to": "2026-08-15",
  "location": "Mozambique",
  "result_limit_per_source": 25,
  "auto_download": false,
  "source_parameters": {"gdacs": {"event_types": ["FL"]}}
}
```

La réponse contient un identifiant parent, un statut `completed`, `partial` ou
`failed`, un résultat par source, les acquisitions filles et une vue agrégée.
Chaque réponse brute est stockée séparément avec SHA-256.

Autres chemins : `POST /api/acquisitions`, `GET /api/acquisitions` et
`GET /api/projects/{project_id}/federated-searches`.

## Bibliothèque et import

| Méthode | Chemin | Fonction |
|---|---|---|
| POST | `/api/projects/{project_id}/uploads` | import multipart d’un fichier |
| GET | `/api/resources?project_id=...` | bibliothèque filtrable |
| GET | `/api/resources/{resource_id}/file` | téléchargement local |
| POST | `/api/resources/{resource_id}/verify` | recalcul SHA-256 |
| DELETE | `/api/resources/{resource_id}` | suppression du fichier, trace conservée |
| POST/PATCH/DELETE | `/api/resources/{resource_id}/refresh-schedule` | périodicité par fichier |

Champs multipart : `file`, `category`, `title`, `geographic_scope` et
`update_frequency`. La limite est `HDP_MAX_UPLOAD_BYTES`, bornée côté serveur
entre 1 Mio et 2 Gio.

## Traitements et lignée

`GET /api/processing/operations` publie la version du moteur, les opérations et
les limites. `POST /api/projects/{project_id}/processing-runs` reçoit une
ressource CSV/TSV, un nom, un fichier de sortie, le langage du script et une
recette JSON.

```json
{
  "resource_id": "00000000-0000-4000-8000-000000000002",
  "name": "Incidence",
  "output_title": "incidence.csv",
  "script_language": "python",
  "recipe": {"steps": [{"operation": "derive_rate", "numerator": "cases", "denominator": "population", "output": "incidence_per_100000", "multiplier": 100000}]}
}
```

Le résultat inclut les comptes de lignes, le profil d’entrée, le SHA-256 de
sortie et les identifiants de la ressource dérivée et du script. L’historique
est exposé par `GET /api/projects/{project_id}/processing-runs`.

## Carte

- `GET /api/projects/{project_id}/map/layers` ;
- `POST /api/resources/{resource_id}/map/import` ;
- `GET /api/map/layers/{layer_id}/geojson` ;
- `GET /api/map/layers/{layer_id}/export` ;
- `DELETE /api/map/layers/{layer_id}`.

L’import vérifie le SHA-256 avant de lire le GeoJSON. La suppression porte sur
la couche dérivée et ses entités PostGIS, jamais sur la ressource locale.

## SQL

`GET /api/projects/{project_id}/sql/schema` décrit les vues autorisées.
`POST /api/projects/{project_id}/sql/query` reçoit `query` et `max_rows` (1 à
1 000). Le texte est validé, la transaction est read-only et la requête est
journalisée par empreinte, statut, durée et nombre de lignes.

## Scripts, planifications et RSS

Les routes existantes `/api/projects/{project_id}/scripts`,
`/api/scripts/{script_id}/executions`, `/api/projects/{project_id}/schedules` et
`/api/projects/{project_id}/rss/*` restent disponibles. Python et R s’exécutent
dans des runners sans réseau, sans privilège et avec limites de temps/sortie.

