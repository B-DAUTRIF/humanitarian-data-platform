# API GitHub HDP — v2.4.1

HDP embarque une passerelle locale vers l'API REST GitHub dans le service Docker `github-api`.

## Principes de sécurité

- `GITHUB_TOKEN` reste côté serveur et n'est jamais renvoyé au navigateur.
- Lecture activée par défaut.
- Écritures désactivées par défaut (`GITHUB_API_WRITE_ENABLED=false`).
- Le service est publié uniquement sur `127.0.0.1` par défaut.
- Les noms owner/repository sont validés avant construction des requêtes.
- La version REST est envoyée avec `X-GitHub-Api-Version`.

## Configuration

Variables optionnelles dans `.env` :

```dotenv
GITHUB_TOKEN=
GITHUB_API_VERSION=2026-03-10
GITHUB_DEFAULT_OWNER=B-DAUTRIF
GITHUB_DEFAULT_REPOSITORY=humanitarian-data-platform
GITHUB_API_WRITE_ENABLED=false
HDP_GITHUB_API_PORT=8091
```

Ne jamais versionner un jeton réel.

## Endpoints locaux

- `GET /health`
- `GET /repository`
- `GET /branches`
- `GET /commits`
- `GET /issues`
- `GET /pulls`
- `GET /releases`
- `GET /workflows`
- `GET /contents/{path}`
- `GET /rate-limit`
- `POST /issues` — seulement si les écritures sont explicitement activées
- `POST /workflows/{workflow_id}/dispatch` — seulement si les écritures sont explicitement activées

Les endpoints de listes acceptent la pagination GitHub classique (`page`, `per_page`). Les en-têtes de pagination et de rate-limit utiles sont retournés dans `meta`, sans recopier les en-têtes sensibles.

## Exemples

```bash
curl http://127.0.0.1:8091/health
curl http://127.0.0.1:8091/repository
curl 'http://127.0.0.1:8091/branches?per_page=20&page=1'
curl 'http://127.0.0.1:8091/commits?sha=main'
curl 'http://127.0.0.1:8091/issues?state=open'
curl http://127.0.0.1:8091/workflows
```

## Écritures

Les écritures nécessitent simultanément :

1. un `GITHUB_TOKEN` possédant les permissions adaptées ;
2. `GITHUB_API_WRITE_ENABLED=true` ;
3. les droits GitHub du compte ou de l'application associée au jeton.

Cette double barrière évite qu'un jeton configuré pour les fonctionnalités historiques de HDP rende automatiquement les nouveaux endpoints mutables.

## Documentation GitHub de référence

- REST API : https://docs.github.com/en/rest
- Versioning : https://docs.github.com/en/rest/about-the-rest-api/api-versions
- Authentication : https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api

Les permissions exactes dépendent du type de jeton utilisé et de l'opération appelée ; elles doivent être revérifiées avant activation des écritures.
